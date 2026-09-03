import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.orchestrator import pipeline_state
from app.services.audit_service import audit_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_pipeline_run():
    """Ensure a fresh pipeline run exists for review workflow tests."""
    pipeline_state.clear()
    audit_service.clear()
    client.post("/api/reconciliation/run")
    yield
    pipeline_state.clear()
    audit_service.clear()


# 1. Successful APPROVE_ADVISORY
def test_successful_approve_advisory():
    """Verify APPROVE_ADVISORY updates human_review_status to RESOLVED and preserves deterministic status."""
    payload = {
        "action": "APPROVE_ADVISORY",
        "actor": "Lead Controller Jane",
        "notes": "Accepted AI fee variance diagnosis.",
    }
    response = client.post("/api/reconciliation/review/ORD-8494", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["order_id"] == "ORD-8494"
    assert data["action"] == "APPROVE_ADVISORY"
    assert data["actor"] == "Lead Controller Jane"
    assert data["notes"] == "Accepted AI fee variance diagnosis."
    assert data["resulting_human_review_status"] == "RESOLVED"
    assert "audit_event_id" in data

    # Verify transaction record in memory preserves deterministic truth
    txn_res = client.get("/api/reconciliation/transactions/ORD-8494")
    assert txn_res.status_code == 200
    txn_data = txn_res.json()
    assert txn_data["status"] == "PENDING_REVIEW"
    assert txn_data["rule_id"] == "RULE_04_CROSS_CURRENCY_CHECK"
    assert txn_data["human_review_status"] == "RESOLVED"


# 2. Successful MANUAL_OVERRIDE
def test_successful_manual_override():
    """Verify MANUAL_OVERRIDE updates workflow to RESOLVED with custom controller notes."""
    payload = {
        "action": "MANUAL_OVERRIDE",
        "actor": "Senior Auditor Smith",
        "notes": "Special clearing arrangement confirmed with banking desk.",
    }
    response = client.post("/api/reconciliation/review/ORD-8001", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["resulting_human_review_status"] == "RESOLVED"
    assert data["action"] == "MANUAL_OVERRIDE"

    txn = client.get("/api/reconciliation/transactions/ORD-8001").json()
    assert txn["status"] == "PENDING_REVIEW"
    assert txn["human_review_status"] == "RESOLVED"


# 3. Successful ESCALATE_DISPUTE
def test_successful_escalate_dispute():
    """Verify ESCALATE_DISPUTE updates workflow to ESCALATED without claiming resolved discrepancy."""
    payload = {
        "action": "ESCALATE_DISPUTE",
        "actor": "Dispute Specialist Alex",
        "notes": "Routed to merchant banking desk for manual clearing claim.",
    }
    response = client.post("/api/reconciliation/review/ORD-8002", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["resulting_human_review_status"] == "ESCALATED"

    txn = client.get("/api/reconciliation/transactions/ORD-8002").json()
    assert txn["status"] == "PENDING_REVIEW"
    assert txn["human_review_status"] == "ESCALATED"


# 4. Unknown order -> 404
def test_review_unknown_order_returns_404():
    """Verify reviewing a non-existent transaction returns HTTP 404."""
    payload = {
        "action": "APPROVE_ADVISORY",
        "actor": "Controller",
    }
    response = client.post("/api/reconciliation/review/ORD-NONEXISTENT", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# 5. Invalid action -> 422
def test_review_invalid_action_returns_422():
    """Verify invalid action enum returns HTTP 422."""
    payload = {
        "action": "INVALID_ACTION",
        "actor": "Controller",
    }
    response = client.post("/api/reconciliation/review/ORD-8494", json=payload)
    assert response.status_code == 422


# 6. Malformed request (empty actor) -> 422
def test_review_empty_actor_returns_422():
    """Verify empty or whitespace-only actor returns validation error."""
    payload = {
        "action": "APPROVE_ADVISORY",
        "actor": "   ",
    }
    response = client.post("/api/reconciliation/review/ORD-8494", json=payload)
    assert response.status_code == 422


# 7. Non-reviewable case rejected -> 400
def test_review_non_reviewable_case_rejected():
    """Verify attempting to review an auto-cleared transaction (ORD-8492) returns HTTP 400."""
    payload = {
        "action": "APPROVE_ADVISORY",
        "actor": "Controller",
    }
    response = client.post("/api/reconciliation/review/ORD-8492", json=payload)
    assert response.status_code == 400
    assert "does not require human controller review" in response.json()["detail"]


# 8. Already resolved case rejected -> 409
def test_review_already_resolved_case_rejected():
    """Verify attempting to review a transaction that has already been resolved returns HTTP 409."""
    payload = {
        "action": "APPROVE_ADVISORY",
        "actor": "Controller 1",
    }
    # First review: succeeds
    res1 = client.post("/api/reconciliation/review/ORD-8494", json=payload)
    assert res1.status_code == 200

    # Second review: rejected with 409 Conflict
    res2 = client.post("/api/reconciliation/review/ORD-8494", json=payload)
    assert res2.status_code == 409
    assert "already been resolved" in res2.json()["detail"]


# 9, 10. Deterministic status and rule_id unchanged across all review operations
def test_deterministic_integrity_preserved_after_multiple_reviews():
    """Verify multiple review decisions leave engine outputs completely intact."""
    client.post(
        "/api/reconciliation/review/ORD-8494",
        json={"action": "APPROVE_ADVISORY", "actor": "Controller"},
    )
    client.post(
        "/api/reconciliation/review/ORD-8001",
        json={"action": "MANUAL_OVERRIDE", "actor": "Controller"},
    )

    t1 = client.get("/api/reconciliation/transactions/ORD-8494").json()
    assert t1["status"] == "PENDING_REVIEW"
    assert t1["rule_id"] == "RULE_04_CROSS_CURRENCY_CHECK"

    t2 = client.get("/api/reconciliation/transactions/ORD-8001").json()
    assert t2["status"] == "PENDING_REVIEW"
    assert t2["rule_id"] == "RULE_04_CROSS_CURRENCY_CHECK"


# 11, 12, 13, 14. Audit event created with actor, timestamp, and action
def test_audit_event_recorded_on_decision():
    """Verify DECISION_RECORDED audit event is logged with full metadata."""
    client.post(
        "/api/reconciliation/review/ORD-8494",
        json={
            "action": "APPROVE_ADVISORY",
            "actor": "Lead Controller Sarah",
            "notes": "Nostro exchange rate validated via Reuters feed.",
        },
    )

    audit_res = client.get("/api/reconciliation/audit-trail?order_id=ORD-8494")
    assert audit_res.status_code == 200
    events = audit_res.json()
    assert len(events) >= 1

    decision_evt = next((e for e in events if e["event_type"] == "DECISION_RECORDED"), None)
    assert decision_evt is not None
    assert decision_evt["actor"] == "Lead Controller Sarah"
    assert decision_evt["order_id"] == "ORD-8494"
    assert "timestamp" in decision_evt
    assert decision_evt["details"]["action"] == "APPROVE_ADVISORY"
    assert decision_evt["details"]["notes"] == "Nostro exchange rate validated via Reuters feed."
    assert decision_evt["details"]["resulting_human_review_status"] == "RESOLVED"


# 15, 16. Audit trail ordering and optional order_id filtering
def test_audit_trail_chronological_ordering_and_filtering():
    """Verify audit trail retrieves events in deterministic newest-first order with optional filtering."""
    # Decision 1
    client.post(
        "/api/reconciliation/review/ORD-8494",
        json={"action": "APPROVE_ADVISORY", "actor": "Controller A"},
    )
    # Decision 2
    client.post(
        "/api/reconciliation/review/ORD-8001",
        json={"action": "MANUAL_OVERRIDE", "actor": "Controller B"},
    )

    # Fetch all audit events
    all_events = client.get("/api/reconciliation/audit-trail").json()
    decision_events = [e for e in all_events if e["event_type"] == "DECISION_RECORDED"]
    assert len(decision_events) == 2

    # Newest decision (ORD-8001) should appear before older decision (ORD-8494)
    assert decision_events[0]["order_id"] == "ORD-8001"
    assert decision_events[1]["order_id"] == "ORD-8494"

    # Filtered by order_id
    filtered = client.get("/api/reconciliation/audit-trail?order_id=ORD-8494").json()
    assert all(e["order_id"] == "ORD-8494" for e in filtered)
