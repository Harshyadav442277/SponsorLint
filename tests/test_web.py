"""End-to-end API coverage for the zero-key browser demo."""

import asyncio
import importlib

import httpx
import pytest
from fastapi import HTTPException

from sponsorlint.web.app import REPORTS, SPECS, app

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


def test_sample_campaign_keeps_unresolved_visual_item_in_review():
    asyncio.run(_sample_campaign_scenario())


async def _unconfirmed_manual_scenario():
    SPECS.clear()
    REPORTS.clear()
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
