"""FastAPI routes. Architecture.md §6.

IMPORT DISCIPLINE applies here exactly as in `cli.py`: the `/`, `/api/sample`
and `/api/verify` routes must not pull `pypdf`, `faster_whisper` or the LLM
client at module scope, or the whole UI dies on a demo-only install.

Persistence is an in-memory dict keyed by uuid. That is the entire persistence
layer — no database (Rules.md §1.9).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from ..lint.engine import run
from ..models import EmptySpecError, Spec, Transcript
from ..report.render import report_context

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
SAMPLES = REPO_ROOT / "samples"
UPLOADS = REPO_ROOT / "uploads"

app = FastAPI(title="SponsorLint", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
templates = Jinja2Templates(directory=str(HERE / "templates"))

#: uuid -> Spec / Report. In-memory only; restarting clears it.
SPECS: dict[str, Spec] = {}
REPORTS: dict[str, dict] = {}


# --------------------------------------------------------------------------
# views
# --------------------------------------------------------------------------


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


# --------------------------------------------------------------------------
# the sample campaign — always available, no key, no upload
# --------------------------------------------------------------------------


@app.get("/api/sample")
def sample():
    """The committed demo campaign. A judge who uploads nothing still reaches
    the report screen."""
    try:
        spec_data = json.loads((SAMPLES / "spec.approved.json").read_text(encoding="utf-8"))
        brief_text = (SAMPLES / "brief.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(500, f"Could not read the sample campaign: {exc}") from exc

    return {
        "brief_text": brief_text,
        "spec": spec_data,
        "takes": _available_takes(),
    }


def _available_takes() -> list[dict]:
    takes = []
    for name, label in (("v1", "Take 1 — original"), ("v3", "Take 3 — corrected")):
        path = SAMPLES / f"transcript.{name}.json"
        if path.exists():
            takes.append({"id": name, "label": label})
    return takes


# --------------------------------------------------------------------------
# compile — the only LLM call
# --------------------------------------------------------------------------


@app.post("/api/compile")
async def compile_route(brief: UploadFile | None = None, text: str = Form("")):
    """Brief -> proposed spec. Needs an API key; the sample path does not."""
    from ..brief.compile import CompileError, compile_brief  # LLM client here
    from ..brief.extract import ExtractError, extract_text  # pypdf here

    brief_text = text.strip()

    if brief is not None and brief.filename:
        UPLOADS.mkdir(exist_ok=True)
        target = UPLOADS / f"{uuid.uuid4().hex}-{Path(brief.filename).name}"
        target.write_bytes(await brief.read())
        try:
            brief_text = extract_text(target)
        except ExtractError as exc:
            raise HTTPException(400, str(exc)) from exc
        finally:
            target.unlink(missing_ok=True)

    if not brief_text:
        raise HTTPException(400, "No brief supplied. Upload a PDF or paste the brief text.")

    try:
        spec = compile_brief(brief_text)
    except CompileError as exc:
        raise HTTPException(502, str(exc)) from exc

    return {"brief_text": brief_text, "spec": spec.model_dump(exclude_none=True)}


# --------------------------------------------------------------------------
# approve — the trust boundary
# --------------------------------------------------------------------------


@app.post("/api/spec/approve")
async def approve(payload: dict):
    """The edited spec enters the verifier. Not the raw extraction."""
    try:
        spec = Spec.model_validate(payload.get("spec") or {})
    except ValidationError as exc:
        return JSONResponse({"detail": _readable(exc)}, status_code=400)

    if not spec.rules:
        return JSONResponse(
            {"detail": "No requirements to check. Add at least one rule."},
            status_code=400,
        )

    blockers = spec.approval_blockers()
    if blockers:
        return JSONResponse({"detail": "\n".join(blockers), "blockers": blockers}, status_code=400)

    spec_id = uuid.uuid4().hex
    SPECS[spec_id] = spec
    return {"spec_id": spec_id, "rules": len(spec.rules)}


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------


@app.post("/api/verify")
async def verify(
    spec_id: str = Form(...),
    take: str = Form(""),
    video: UploadFile | None = None,
):
    """Approved spec + transcript -> report.

    `take` uses a committed transcript (no ffmpeg, no model download). A video
    upload transcribes for real — that path needs the full requirements file.
    """
    spec = SPECS.get(spec_id)
    if spec is None:
        raise HTTPException(404, "That specification is no longer in memory. Approve it again.")

    if video is not None and video.filename:
        transcript = await _transcribe_upload(video)
    elif take:
        transcript = _load_take(take)
    else:
        raise HTTPException(400, "Choose a recorded take or upload a video file.")

    try:
        report = run(spec, transcript)
    except EmptySpecError as exc:
        raise HTTPException(400, str(exc)) from exc

    report_id = uuid.uuid4().hex
    context = report_context(report)
    REPORTS[report_id] = context
    return {"report_id": report_id, "report": context}


def _load_take(take: str) -> Transcript:
    path = SAMPLES / f"transcript.{Path(take).name}.json"
    if not path.exists():
        raise HTTPException(404, f"No committed transcript named {take}.")
    return Transcript.model_validate(json.loads(path.read_text(encoding="utf-8")))


async def _transcribe_upload(video: UploadFile) -> Transcript:
    from ..transcript.transcribe import TranscribeError, transcribe  # whisper here

    UPLOADS.mkdir(exist_ok=True)
    target = UPLOADS / f"{uuid.uuid4().hex}-{Path(video.filename).name}"
    target.write_bytes(await video.read())
    try:
        return transcribe(target)
    except TranscribeError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        target.unlink(missing_ok=True)


@app.get("/api/report/{report_id}")
def get_report(report_id: str):
    report = REPORTS.get(report_id)
    if report is None:
        raise HTTPException(404, "No such report.")
    return report


# --------------------------------------------------------------------------


def _readable(exc: ValidationError) -> str:
    lines = []
    for error in exc.errors():
        where = " -> ".join(str(p) for p in error["loc"]) or "spec"
        lines.append(f"{where}: {error['msg']}")
    return "\n".join(lines)
