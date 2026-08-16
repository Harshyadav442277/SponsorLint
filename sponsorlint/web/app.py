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
from urllib.parse import urlsplit

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from ..lint.engine import run
from ..models import Spec, SpecError, Transcript
from ..report.render import report_context

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
SAMPLES = REPO_ROOT / "samples"
UPLOADS = REPO_ROOT / "uploads"
MAX_BRIEF_BYTES = 10 * 1024 * 1024
MAX_MEDIA_BYTES = 500 * 1024 * 1024
MAX_STORED_ITEMS = 100
BRIEF_SUFFIXES = frozenset({".pdf", ".md", ".markdown", ".txt"})
MEDIA_SUFFIXES = frozenset({
    ".aac", ".flac", ".m4a", ".m4v", ".mkv", ".mov", ".mp3", ".mp4",
    ".ogg", ".wav", ".webm",
})

app = FastAPI(title="SponsorLint", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
templates = Jinja2Templates(directory=str(HERE / "templates"))

#: uuid -> Spec / Report. In-memory only; restarting clears it.
SPECS: dict[str, Spec] = {}
REPORTS: dict[str, dict] = {}


@app.middleware("http")
async def reject_cross_origin_writes(request: Request, call_next):
    """A foreign page must not trigger local API calls or paid compilation."""
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin:
            parsed = urlsplit(origin)
            if (parsed.scheme, parsed.netloc) != (request.url.scheme, request.url.netloc):
                return JSONResponse(
                    {"detail": "Cross-origin requests are not allowed."},
                    status_code=403,
                )
    return await call_next(request)


# --------------------------------------------------------------------------
# views
# --------------------------------------------------------------------------


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


# --------------------------------------------------------------------------
# the sample campaign — always available, no key, no upload
# --------------------------------------------------------------------------


@app.get("/api/sample")
async def sample():
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

    if len(brief_text.encode("utf-8")) > MAX_BRIEF_BYTES:
        raise HTTPException(413, "The pasted brief exceeds the 10 MiB limit.")

    if brief is not None and brief.filename:
        target = await _save_upload(
            brief,
            allowed_suffixes=BRIEF_SUFFIXES,
            max_bytes=MAX_BRIEF_BYTES,
            label="brief",
        )
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
    _remember(SPECS, spec_id, spec)
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
    except SpecError as exc:
        raise HTTPException(400, str(exc)) from exc

    report_id = uuid.uuid4().hex
    context = report_context(report)
    _remember(REPORTS, report_id, context)
    return {"report_id": report_id, "report": context}


def _load_take(take: str) -> Transcript:
    path = SAMPLES / f"transcript.{Path(take).name}.json"
    if not path.exists():
        raise HTTPException(404, f"No committed transcript named {take}.")
    return Transcript.model_validate(json.loads(path.read_text(encoding="utf-8")))


async def _transcribe_upload(video: UploadFile) -> Transcript:
    from ..transcript.transcribe import TranscribeError, transcribe  # whisper here

    target = await _save_upload(
        video,
        allowed_suffixes=MEDIA_SUFFIXES,
        max_bytes=MAX_MEDIA_BYTES,
        label="media",
    )
    try:
        return transcribe(target)
    except TranscribeError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        target.unlink(missing_ok=True)


async def _save_upload(
    upload: UploadFile,
    *,
    allowed_suffixes: frozenset[str],
    max_bytes: int,
    label: str,
) -> Path:
    """Stream one allowlisted upload to a UUID path with a hard size cap."""
    filename = Path((upload.filename or "upload").replace("\\", "/")).name
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise HTTPException(400, f"Unsupported {label} file type. Use one of: {allowed}.")

    try:
        UPLOADS.mkdir(parents=True, exist_ok=True)
        target = UPLOADS / f"{uuid.uuid4().hex}-{filename}"
        total = 0
        with target.open("xb") as handle:
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(
                        413,
                        f"The {label} upload exceeds the {max_bytes // (1024 * 1024)} MiB limit.",
                    )
                handle.write(chunk)
    except HTTPException:
        if "target" in locals():
            target.unlink(missing_ok=True)
        raise
    except OSError as exc:
        if "target" in locals():
            target.unlink(missing_ok=True)
        raise HTTPException(500, f"Could not store the {label} upload.") from exc
    return target


def _remember(mapping: dict, key: str, value) -> None:
    """Bound process-local demo state; oldest entries are disposable."""
    mapping[key] = value
    while len(mapping) > MAX_STORED_ITEMS:
        mapping.pop(next(iter(mapping)))


@app.get("/api/report/{report_id}")
async def get_report(report_id: str):
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
