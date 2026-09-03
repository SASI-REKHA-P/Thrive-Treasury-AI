import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.orchestrator import pipeline_state
from app.services.audit_service import audit_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_clean_pipeline():
    """Ensure clean state before and after each test."""
    pipeline_state.clear()
    audit_service.clear()
    yield
    pipeline_state.clear()
    audit_service.clear()


def test_clear_populated_audit_trail_and_response_format():
    """1. Clear populated audit trail and 7. Verify correct response shape."""
    # Execute batch run and record a review decision to populate audit trail
    client.post("/api/reconciliation/run")
    client.post(
        "/api/reconciliation/review/ORD-8494",
        json={
            "action": "APPROVE_ADVISORY",
            "actor": "Lead Controller Jane",
            "notes": "Approved variance.",
        },
    )

    # Verify audit trail has events
    events_before = client.get("/api/reconciliation/audit-trail").json()
    assert len(events_before) >= 2  # BATCH_LOADED + DECISION_RECORDED

    # Call DELETE /api/reconciliation/audit-trail
    response = client.delete("/api/reconciliation/audit-trail")
    assert response.status_code == 200
    data = response.json()
    assert data["cleared"] is True
    assert data["count"] == len(events_before)

    # Verify audit trail is now empty
    events_after = client.get("/api/reconciliation/audit-trail").json()
    assert events_after == []


def test_clear_already_empty_audit_trail():
    """2. Clear already-empty audit trail returns cleared=True, count=0."""
    response = client.delete("/api/reconciliation/audit-trail")
    assert response.status_code == 200
    data = response.json()
    assert data["cleared"] is True
    assert data["count"] == 0


def test_clear_audit_trail_preserves_reconciliation_and_review_state():
    """3. Verify reconciliation results and 4. Human review state remain completely unchanged."""
    client.post("/api/reconciliation/run")
    client.post(
        "/api/reconciliation/review/ORD-8494",
        json={
            "action": "ESCALATE_DISPUTE",
            "actor": "Lead Controller Jane",
            "notes": "Escalated for Nostro settlement dispute.",
        },
    )

    # Capture state before clearing
    txns_before = client.get("/api/reconciliation/transactions").json()
    txn_8494_before = client.get("/api/reconciliation/transactions/ORD-8494").json()
    assert txn_8494_before["human_review_status"] == "ESCALATED"

    # Clear audit trail
    clear_res = client.delete("/api/reconciliation/audit-trail")
    assert clear_res.status_code == 200

    # Capture state after clearing
    txns_after = client.get("/api/reconciliation/transactions").json()
    txn_8494_after = client.get("/api/reconciliation/transactions/ORD-8494").json()

    # Verify transactions, statuses, and review states remain identical
    assert txns_before == txns_after
    assert txn_8494_after["status"] == "PENDING_REVIEW"
    assert txn_8494_after["rule_id"] == "RULE_04_CROSS_CURRENCY_CHECK"
    assert txn_8494_after["human_review_status"] == "ESCALATED"


def test_clear_audit_trail_preserves_evaluation_behavior():
    """5. Verify evaluation metrics and benchmark accuracy remain unchanged."""
    client.post("/api/reconciliation/run")
    eval_before = client.get("/api/evaluation/metrics").json()

    # Clear audit trail
    clear_res = client.delete("/api/reconciliation/audit-trail")
    assert clear_res.status_code == 200

    eval_after = client.get("/api/evaluation/metrics").json()
    assert eval_before == eval_after
    assert eval_after["rule_accuracy"] == "1.0000"
    assert eval_after["status_accuracy"] == "1.0000"
    assert eval_after["deterministic_resolution_rate"] == "0.7083"


def test_subsequent_reconciliation_and_reviews_populate_audit_trail():
    """6. Verify a subsequent reconciliation run and reviews create audit events normally."""
    client.post("/api/reconciliation/run")
    client.delete("/api/reconciliation/audit-trail")
    assert client.get("/api/reconciliation/audit-trail").json() == []

    # Run pipeline again
    client.post("/api/reconciliation/run")
    events_new_run = client.get("/api/reconciliation/audit-trail").json()
    assert len(events_new_run) >= 1
    assert any(e["event_type"] == "BATCH_LOADED" for e in events_new_run)

    # Perform a new review
    client.post(
        "/api/reconciliation/review/ORD-8001",
        json={
            "action": "MANUAL_OVERRIDE",
            "actor": "Controller Alex",
            "notes": "Cleared after phone confirmation.",
        },
    )
    events_after_review = client.get("/api/reconciliation/audit-trail").json()
    assert any(
        e["event_type"] == "DECISION_RECORDED" and e["order_id"] == "ORD-8001"
        for e in events_after_review
    )
