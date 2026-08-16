"""End-to-end API coverage for the zero-key browser demo."""

from fastapi.testclient import TestClient

from sponsorlint.web.app import REPORTS, SPECS, app


def test_sample_campaign_reaches_both_canonical_verdicts():
    SPECS.clear()
    REPORTS.clear()
    client = TestClient(app)

    page = client.get("/")
    assert page.status_code == 200
    assert "Load sample campaign" in page.text

    sample = client.get("/api/sample")
    assert sample.status_code == 200
    campaign = sample.json()
    assert [take["id"] for take in campaign["takes"]] == ["v1", "v3"]

    approval = client.post("/api/spec/approve", json={"spec": campaign["spec"]})
    assert approval.status_code == 200
    spec_id = approval.json()["spec_id"]

    original = client.post("/api/verify", data={"spec_id": spec_id, "take": "v1"})
    assert original.status_code == 200
    assert original.json()["report"]["status"] == "DO_NOT_SEND"
    assert original.json()["report"]["score"] == "4/7"

    corrected = client.post("/api/verify", data={"spec_id": spec_id, "take": "v3"})
    assert corrected.status_code == 200
    corrected_body = corrected.json()
    assert corrected_body["report"]["status"] == "SPONSOR_READY"
    assert corrected_body["report"]["score"] == "7/7"

    stored = client.get(f"/api/report/{corrected_body['report_id']}")
    assert stored.status_code == 200
    assert stored.json() == corrected_body["report"]
