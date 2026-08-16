"""End-to-end API coverage for the zero-key browser demo."""

import asyncio
import importlib
import json
import threading
import time

import httpx
import pytest
from fastapi import HTTPException

from sponsorlint.web.app import REPORTS, REPORT_TRANSCRIPTS, SPECS, app

web_app = importlib.import_module("sponsorlint.web.app")


class MemoryUpload:
    """Minimal async upload double; avoids testing Starlette's threadpool."""

    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content
        self._offset = 0

    async def read(self, size: int) -> bytes:
        chunk = self._content[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


async def _sample_campaign_scenario():
    SPECS.clear()
    REPORTS.clear()
    REPORT_TRANSCRIPTS.clear()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        page = await client.get("/")
        assert page.status_code == 200
        assert "Run sample campaign" in page.text

        sample = await client.get("/api/sample")
        assert sample.status_code == 200
        campaign = sample.json()
        assert [take["id"] for take in campaign["takes"]] == ["v1", "v3"]

        approval = await client.post("/api/spec/approve", json={"spec": campaign["spec"]})
        assert approval.status_code == 200
        spec_id = approval.json()["spec_id"]

        original = await client.post("/api/verify", data={"spec_id": spec_id, "take": "v1"})
        assert original.status_code == 200
        assert original.json()["report"]["status"] == "DO_NOT_SEND"
        assert original.json()["report"]["score"] == "4/7"

        corrected = await client.post("/api/verify", data={"spec_id": spec_id, "take": "v3"})
        assert corrected.status_code == 200
        corrected_body = corrected.json()
        assert corrected_body["report"]["status"] == "REVIEW"
        assert corrected_body["report"]["score"] == "7/7"

        stored = await client.get(f"/api/report/{corrected_body['report_id']}")
        assert stored.status_code == 200
        assert stored.json() == corrected_body["report"]

        confirmed = await client.post(
            f"/api/report/{corrected_body['report_id']}/confirm-manual",
            json={"spec": campaign["spec"], "index": 0},
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["report"]["status"] == "SPONSOR_READY"
        assert confirmed.json()["report"]["score"] == "7/7"


def test_sample_campaign_keeps_unresolved_visual_item_in_review():
    asyncio.run(_sample_campaign_scenario())


async def _unconfirmed_manual_scenario():
    SPECS.clear()
    REPORTS.clear()
    REPORT_TRANSCRIPTS.clear()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        sample = (await client.get("/api/sample")).json()
        sample["spec"]["manual_review"][0]["confirmed"] = False

        approval = await client.post("/api/spec/approve", json={"spec": sample["spec"]})
        assert approval.status_code == 200
        response = await client.post(
            "/api/verify",
            data={"spec_id": approval.json()["spec_id"], "take": "v3"},
        )
        report = response.json()["report"]

        assert report["status"] == "REVIEW"
        assert report["summary"]["manual_review"] == 1
        assert report["summary"]["manual_confirmed"] == 0


def test_unconfirmed_manual_item_keeps_report_in_review():
    asyncio.run(_unconfirmed_manual_scenario())


async def _cross_origin_scenario():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/spec/approve",
            headers={"Origin": "https://attacker.example"},
            json={"spec": {}},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Cross-origin requests are not allowed."


def test_cross_origin_write_is_rejected():
    asyncio.run(_cross_origin_scenario())


async def _deployment_and_manual_confirmation_errors_scenario():
    SPECS.clear()
    REPORTS.clear()
    REPORT_TRANSCRIPTS.clear()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/healthz")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        missing = await client.post(
            "/api/report/missing/confirm-manual",
            json={"spec": {}, "index": 0},
        )
        assert missing.status_code == 404

        sample = (await client.get("/api/sample")).json()
        approval = await client.post("/api/spec/approve", json={"spec": sample["spec"]})
        verified = await client.post(
            "/api/verify",
            data={"spec_id": approval.json()["spec_id"], "take": "v3"},
        )
        report_id = verified.json()["report_id"]

        invalid_index = await client.post(
            f"/api/report/{report_id}/confirm-manual",
            json={"spec": sample["spec"], "index": 99},
        )
        assert invalid_index.status_code == 400
        assert invalid_index.json()["detail"] == "That manual-review item does not exist."


def test_deployment_probe_and_manual_confirmation_errors_are_explicit():
    asyncio.run(_deployment_and_manual_confirmation_errors_scenario())


def test_upload_is_streamed_with_a_hard_limit_and_cleaned_up(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "UPLOADS", tmp_path)
    upload = MemoryUpload("large.txt", b"12345")

    with pytest.raises(HTTPException) as raised:
        asyncio.run(web_app._save_upload(
            upload,
            allowed_suffixes=frozenset({".txt"}),
            max_bytes=4,
            label="brief",
        ))

    assert raised.value.status_code == 413
    assert list(tmp_path.iterdir()) == []


def test_upload_extension_is_allowlisted_before_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "UPLOADS", tmp_path)
    upload = MemoryUpload("payload.html", b"<script>")

    with pytest.raises(HTTPException) as raised:
        asyncio.run(web_app._save_upload(
            upload,
            allowed_suffixes=frozenset({".txt"}),
            max_bytes=100,
            label="brief",
    ))

    assert raised.value.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_process_local_state_is_bounded(monkeypatch):
    monkeypatch.setattr(web_app, "MAX_STORED_ITEMS", 2)
    values = {}
    web_app._remember(values, "oldest", 1)
    web_app._remember(values, "middle", 2)
    web_app._remember(values, "newest", 3)
    assert values == {"middle": 2, "newest": 3}


async def _responsive_during_transcription_scenario(tmp_path, monkeypatch):
    SPECS.clear()
    REPORTS.clear()
    REPORT_TRANSCRIPTS.clear()
    monkeypatch.setattr(web_app, "UPLOADS", tmp_path)

    transcribe_module = importlib.import_module("sponsorlint.transcript.transcribe")
    started = threading.Event()
    release = threading.Event()

    def slow_transcribe(_path):
        started.set()
        assert release.wait(timeout=3)
        return web_app._load_take("v1")

    monkeypatch.setattr(transcribe_module, "transcribe", slow_transcribe)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        sample = (await client.get("/api/sample")).json()
        approval = await client.post("/api/spec/approve", json={"spec": sample["spec"]})
        spec_id = approval.json()["spec_id"]

        first = asyncio.create_task(client.post(
            "/api/verify",
            data={"spec_id": spec_id},
            files={"video": ("first.mp4", b"media", "video/mp4")},
        ))
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(0.01)
        assert started.is_set()

        began = time.perf_counter()
        health = await client.get("/healthz")
        health_latency = time.perf_counter() - began
        assert health.status_code == 200
        assert health_latency < 0.5

        began = time.perf_counter()
        sample_during_transcription = await client.get("/api/sample")
        sample_latency = time.perf_counter() - began
        assert sample_during_transcription.status_code == 200
        assert sample_latency < 0.5

        second = await client.post(
            "/api/verify",
            data={"spec_id": spec_id},
            files={"video": ("second.mp4", b"media", "video/mp4")},
        )
        assert second.status_code == 503
        assert second.headers["retry-after"] == "60"
        assert "already running" in second.json()["detail"]

        release.set()
        assert (await first).status_code == 200


def test_health_and_sample_remain_responsive_during_one_transcription(tmp_path, monkeypatch):
    asyncio.run(_responsive_during_transcription_scenario(tmp_path, monkeypatch))


async def _responsive_during_compile_scenario(monkeypatch):
    compile_module = importlib.import_module("sponsorlint.brief.compile")
    started = threading.Event()
    release = threading.Event()

    def slow_compile(_brief_text):
        started.set()
        assert release.wait(timeout=3)
        spec_data = json.loads(
            (web_app.SAMPLES / "spec.approved.json").read_text(encoding="utf-8")
        )
        return web_app.Spec.model_validate(spec_data)

    monkeypatch.setattr(compile_module, "compile_brief", slow_compile)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        compiling = asyncio.create_task(client.post(
            "/api/compile",
            data={"text": "Mention the approved sponsor requirements."},
        ))
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(0.01)
        assert started.is_set()

        began = time.perf_counter()
        health = await client.get("/healthz")
        assert health.status_code == 200
        assert time.perf_counter() - began < 0.5

        release.set()
        assert (await compiling).status_code == 200


def test_health_remains_responsive_during_blocking_compile(monkeypatch):
    asyncio.run(_responsive_during_compile_scenario(monkeypatch))
