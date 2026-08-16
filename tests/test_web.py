"""End-to-end API coverage for the zero-key browser demo."""

import asyncio

import httpx

from sponsorlint.web.app import REPORTS, SPECS, app


async def _sample_campaign_scenario():
    SPECS.clear()
    REPORTS.clear()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        page = await client.get("/")
        assert page.status_code == 200
        assert "Load sample campaign" in page.text

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
        assert corrected_body["report"]["status"] == "SPONSOR_READY"
        assert corrected_body["report"]["score"] == "7/7"

        stored = await client.get(f"/api/report/{corrected_body['report_id']}")
        assert stored.status_code == 200
        assert stored.json() == corrected_body["report"]


def test_sample_campaign_reaches_both_canonical_verdicts():
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
