import csv
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.orchestrator import pipeline_state
from app.services.audit_service import audit_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_clean_pipeline():
    """Ensure clean state for every export test."""
    pipeline_state.clear()
    audit_service.clear()
    yield
    pipeline_state.clear()
    audit_service.clear()


# ==============================================================================
# A. LEDGER EXPORT TESTS
# ==============================================================================

def test_ledger_export_returns_404_before_run():
    """Verify ledger export returns HTTP 404 when no reconciliation run exists."""
    response = client.get("/api/reconciliation/export/ledger")
    assert response.status_code == 404
    assert "no reconciliation run available" in response.json()["detail"].lower()


def test_ledger_export_success_after_run():
    """Verify ledger export produces valid CSV with exactly 120 operational rows."""
    # Execute batch run
    client.post("/api/reconciliation/run")

    response = client.get("/api/reconciliation/export/ledger")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "reconciliation_ledger.csv" in response.headers["content-disposition"]

    # Parse CSV content
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 120

    # Verify headers
    expected_headers = {
        "order_id", "auth_ref", "settlement_ids", "payment_amount",
        "payment_currency", "settlement_amount", "settlement_currency",
        "variance", "status", "rule_id", "deterministic_reason",
        "human_review_status", "review_required", "ai_investigated",
        "ai_classification", "ai_confidence", "ai_confidence_tier",
        "ai_recommended_action",
    }
    assert expected_headers.issubset(set(reader.fieldnames))

    # Verify Decimal precision preservation (no binary float formatting)
    for row in rows:
        if row["payment_amount"]:
            assert "." in row["payment_amount"]
            parts = row["payment_amount"].split(".")
            assert len(parts[1]) == 2  # Exactly 2 decimal digits

    # Spot check anchor ORD-8492
    r8492 = next((r for r in rows if r["order_id"] == "ORD-8492"), None)
    assert r8492 is not None
    assert r8492["status"] == "MATCHED"
    assert r8492["rule_id"] == "RULE_01_EXACT_MATCH"
    assert r8492["payment_amount"] == "4200.00"
    assert r8492["settlement_amount"] == "4200.00"


# ==============================================================================
# B. DISPUTE PACKET EXPORT TESTS
# ==============================================================================

def test_disputes_export_empty_when_no_cases_escalated():
    """Verify disputes export returns valid CSV with header-only when zero cases escalated."""
    client.post("/api/reconciliation/run")

    response = client.get("/api/reconciliation/export/disputes")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 0  # Zero escalated cases initially


def test_disputes_export_includes_only_escalated_cases():
    """
    Verify disputes export contains ONLY explicitly escalated cases,
    and does NOT automatically include un-escalated EXCEPTION or PENDING_REVIEW cases.
    """
    client.post("/api/reconciliation/run")

    # Escalate ORD-8494 via review workflow
    escalation_payload = {
        "action": "ESCALATE_DISPUTE",
        "actor": "Lead Controller Jane",
        "notes": "Escalated for Nostro foreign exchange currency variance dispute.",
    }
    rev_res = client.post("/api/reconciliation/review/ORD-8494", json=escalation_payload)
    assert rev_res.status_code == 200
    assert rev_res.json()["resulting_human_review_status"] == "ESCALATED"

    # Export disputes
    response = client.get("/api/reconciliation/export/disputes")
    assert response.status_code == 200

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 1

    dispute_row = rows[0]
    assert dispute_row["order_id"] == "ORD-8494"
    assert dispute_row["human_review_status"] == "ESCALATED"
    assert dispute_row["controller_actor"] == "Lead Controller Jane"
    assert dispute_row["controller_decision"] == "ESCALATE_DISPUTE"
    assert dispute_row["controller_notes"] == "Escalated for Nostro foreign exchange currency variance dispute."
    assert dispute_row["ai_classification"] == "CROSS_BORDER_FX_EXPOSURE"
    assert dispute_row["ai_confidence"] == "0.90"

    # Verify that other non-escalated exceptions (e.g. ORD-6001) do NOT appear
    order_ids = [r["order_id"] for r in rows]
    assert "ORD-6001" not in order_ids
    assert "ORD-8492" not in order_ids


# ==============================================================================
# C. SINGLE CASE DISPUTE PACKET (JSON) TESTS
# ==============================================================================

def test_single_case_export_unknown_order_returns_404():
    """Verify requesting an unknown order returns HTTP 404."""
    client.post("/api/reconciliation/run")
    response = client.get("/api/reconciliation/export/disputes/ORD-UNKNOWN")
    assert response.status_code == 404


def test_single_case_export_ineligible_order_returns_409():
    """Verify requesting a non-escalated order returns HTTP 409 Conflict."""
    client.post("/api/reconciliation/run")
    # ORD-8492 is MATCHED and not escalated
    response = client.get("/api/reconciliation/export/disputes/ORD-8492")
    assert response.status_code == 409
    assert "not an eligible dispute" in response.json()["detail"].lower()


def test_single_case_export_successful_for_escalated_order():
    """Verify single case dispute export produces structured JSON with deterministic and advisory context."""
    client.post("/api/reconciliation/run")

    # Escalate ORD-8494
    client.post(
        "/api/reconciliation/review/ORD-8494",
        json={
            "action": "ESCALATE_DISPUTE",
            "actor": "Auditor Sarah",
            "notes": "Dispute packet compiled for banking counterparty.",
        },
    )

    response = client.get("/api/reconciliation/export/disputes/ORD-8494")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "dispute_packet_ORD-8494.json" in response.headers["content-disposition"]

    data = response.json()
    assert data["packet_type"] == "ACQUIRER_DISPUTE_PACKET"
    assert data["case"]["order_id"] == "ORD-8494"
    assert data["case"]["reconciliation_status"] == "PENDING_REVIEW"
    assert data["case"]["rule_id"] == "RULE_04_CROSS_CURRENCY_CHECK"
    assert data["case"]["human_review_status"] == "ESCALATED"

    assert data["deterministic_findings"]["rule_id"] == "RULE_04_CROSS_CURRENCY_CHECK"
    assert "checks" in data["deterministic_findings"]

    assert data["ai_advisory"] is not None
    assert data["ai_advisory"]["classification"] == "CROSS_BORDER_FX_EXPOSURE"
    assert "advisory_disclaimer" in data["ai_advisory"]

    assert data["controller_review"]["actor"] == "Auditor Sarah"
    assert data["controller_review"]["decision"] == "ESCALATE_DISPUTE"
    assert data["controller_review"]["notes"] == "Dispute packet compiled for banking counterparty."


# ==============================================================================
# D. AUDIT TRAIL EXPORT TESTS
# ==============================================================================

def test_audit_export_returns_404_before_run():
    """Verify audit export returns HTTP 404 when no pipeline run exists."""
    response = client.get("/api/reconciliation/export/audit-trail")
    assert response.status_code == 404


def test_audit_export_success_with_actor_and_timestamps():
    """Verify audit export CSV accurately reflects recorded decision events."""
    client.post("/api/reconciliation/run")

    # Record decision
    client.post(
        "/api/reconciliation/review/ORD-8494",
        json={
            "action": "APPROVE_ADVISORY",
            "actor": "Lead Controller Jane",
            "notes": "Rate approved via Reuters terminal feed.",
        },
    )

    response = client.get("/api/reconciliation/export/audit-trail")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "audit_trail.csv" in response.headers["content-disposition"]

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) >= 1  # DECISION_RECORDED

    decision_row = next((r for r in rows if r["event_type"] == "DECISION_RECORDED"), None)
    assert decision_row is not None
    assert decision_row["actor"] == "Lead Controller Jane"
    assert decision_row["order_id"] == "ORD-8494"
    assert decision_row["action"] == "APPROVE_ADVISORY"
    assert decision_row["notes"] == "Rate approved via Reuters terminal feed."


# ==============================================================================
# E. IMMUTABILITY VERIFICATION
# ==============================================================================

def test_exports_are_strictly_read_only_and_do_not_mutate_state():
    """Verify calling export endpoints does NOT alter any operational or benchmark state."""
    client.post("/api/reconciliation/run")
    client.post(
        "/api/reconciliation/review/ORD-8494",
        json={"action": "ESCALATE_DISPUTE", "actor": "Controller"},
    )

    # Capture state before exports
    txns_before = client.get("/api/reconciliation/transactions").json()
    metrics_before = client.get("/api/evaluation/metrics").json()
    audits_before = client.get("/api/reconciliation/audit-trail").json()

    # Call all export endpoints
    client.get("/api/reconciliation/export/ledger")
    client.get("/api/reconciliation/export/disputes")
    client.get("/api/reconciliation/export/disputes/ORD-8494")
    client.get("/api/reconciliation/export/audit-trail")

    # Capture state after exports
    txns_after = client.get("/api/reconciliation/transactions").json()
    metrics_after = client.get("/api/evaluation/metrics").json()
    audits_after = client.get("/api/reconciliation/audit-trail").json()

    assert txns_before == txns_after
    assert metrics_before == metrics_after
    assert audits_before == audits_after


# ==============================================================================
# F. GROUND TRUTH ISOLATION TEST
# ==============================================================================

def test_ground_truth_isolation_in_exports():
    """Verify export module does not reference or leak ground truth / benchmark fields."""
    from app.services.export_service import ExportService
    import inspect

    # Verify no import of ground truth or evaluator
    source = inspect.getsource(ExportService)
    assert "GroundTruthDataset" not in source
    assert "ground_truth_120.json" not in source
    assert "expected_status" not in source
    assert "expected_rule" not in source
    assert "BatchEvaluator" not in source


    # Run pipeline and verify exported CSV has no ground truth keys
    client.post("/api/reconciliation/run")
    ledger_csv = client.get("/api/reconciliation/export/ledger").text
    assert "benchmark" not in ledger_csv.lower()
    assert "ground_truth" not in ledger_csv.lower()
    assert "expected_status" not in ledger_csv
    assert "true_positive" not in ledger_csv
