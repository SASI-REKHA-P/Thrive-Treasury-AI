from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.orchestrator import pipeline_state

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_clean_state():
    """Ensure in-memory state is managed cleanly across tests."""
    pipeline_state.clear()
    yield
    pipeline_state.clear()


# 1. Health endpoint
def test_health_endpoint_still_works():
    """Verify GET /api/health continues to return liveness status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "thrive-treasury-ai"


# 10. No-run behavior (Testing 404 before pipeline has run)
def test_endpoints_return_404_when_no_pipeline_run_exists():
    """Verify all data query endpoints return HTTP 404 if pipeline has not been executed."""
    r_tx = client.get("/api/reconciliation/transactions")
    assert r_tx.status_code == 404
    assert "No reconciliation run available" in r_tx.json()["detail"]

    r_tx_id = client.get("/api/reconciliation/transactions/ORD-8492")
    assert r_tx_id.status_code == 404
    assert "No reconciliation run available" in r_tx_id.json()["detail"]

    r_inv = client.get("/api/investigations/ORD-8494")
    assert r_inv.status_code == 404
    assert "No reconciliation run available" in r_inv.json()["detail"]

    r_eval = client.get("/api/evaluation/metrics")
    assert r_eval.status_code == 404
    assert "No reconciliation run available" in r_eval.json()["detail"]


# 2. Pipeline Execution POST /api/reconciliation/run
def test_pipeline_execution_success():
    """Verify POST /api/reconciliation/run executes the complete pipeline and returns exact counts."""
    response = client.post("/api/reconciliation/run")
    assert response.status_code == 200

    data = response.json()
    assert "run_id" in data
    assert data["run_id"].startswith("RUN-")
    assert "timestamp" in data

    # Authentic operational counts
    assert data["total"] == 120
    assert data["matched"] == 85
    assert data["exceptions"] == 30
    assert data["pending_review"] == 5
    assert data["ai_investigated"] == 13
    assert float(data["processing_time_ms"]) > 0.0


# 3. GET /api/reconciliation/transactions
def test_get_all_transactions_after_run():
    """Verify GET /api/reconciliation/transactions returns all 120 records after a pipeline run."""
    client.post("/api/reconciliation/run")

    response = client.get("/api/reconciliation/transactions")
    assert response.status_code == 200
    transactions = response.json()
    assert len(transactions) == 120


# 4. Status filtering
def test_status_filtering():
    """Verify status query param filters transactions with exact counts (85 MATCHED, 30 EXCEPTION, 5 PENDING_REVIEW)."""
    client.post("/api/reconciliation/run")

    # MATCHED
    r_matched = client.get("/api/reconciliation/transactions?status=MATCHED")
    assert r_matched.status_code == 200
    data_matched = r_matched.json()
    assert len(data_matched) == 85
    assert all(r["status"] == "MATCHED" for r in data_matched)

    # EXCEPTION
    r_exc = client.get("/api/reconciliation/transactions?status=EXCEPTION")
    assert r_exc.status_code == 200
    data_exc = r_exc.json()
    assert len(data_exc) == 30
    assert all(r["status"] == "EXCEPTION" for r in data_exc)

    # PENDING_REVIEW
    r_pr = client.get("/api/reconciliation/transactions?status=PENDING_REVIEW")
    assert r_pr.status_code == 200
    data_pr = r_pr.json()
    assert len(data_pr) == 5
    assert all(r["status"] == "PENDING_REVIEW" for r in data_pr)


# 5. Rule filtering
def test_rule_filtering():
    """Verify rule_id query param filters transactions correctly."""
    client.post("/api/reconciliation/run")

    # RULE_08_AMOUNT_MISMATCH -> 8 records
    r_r08 = client.get("/api/reconciliation/transactions?rule_id=RULE_08_AMOUNT_MISMATCH")
    assert r_r08.status_code == 200
    data_r08 = r_r08.json()
    assert len(data_r08) == 8
    assert all(r["rule_id"] == "RULE_08_AMOUNT_MISMATCH" for r in data_r08)

    # RULE_01_EXACT_MATCH -> 60 records
    r_r01 = client.get("/api/reconciliation/transactions?rule_id=RULE_01_EXACT_MATCH")
    assert r_r01.status_code == 200
    assert len(r_r01.json()) == 60


# 6. AI filtering
def test_ai_requirement_filtering():
    """Verify requires_ai query param filters transactions."""
    client.post("/api/reconciliation/run")

    r_ai = client.get("/api/reconciliation/transactions?requires_ai=true")
    assert r_ai.status_code == 200
    data_ai = r_ai.json()
    assert len(data_ai) == 13  # 8 RULE_08 + 5 RULE_04
    assert all(r["requires_ai"] is True or r["ai_status"] == "INVESTIGATED" for r in data_ai)

    r_no_ai = client.get("/api/reconciliation/transactions?requires_ai=false")
    assert r_no_ai.status_code == 200
    data_no_ai = r_no_ai.json()
    assert len(data_no_ai) == 107
    assert all(r["requires_ai"] is False and r["ai_status"] == "NOT_REQUIRED" for r in data_no_ai)



# 7. Individual transaction lookup
def test_individual_transaction_lookup():
    """Verify GET /api/reconciliation/transactions/{order_id} returns single record or 404."""
    client.post("/api/reconciliation/run")

    # Known transaction ORD-8492
    r_found = client.get("/api/reconciliation/transactions/ORD-8492")
    assert r_found.status_code == 200
    data = r_found.json()
    assert data["order_id"] == "ORD-8492"
    assert data["status"] == "MATCHED"
    assert data["rule_id"] == "RULE_01_EXACT_MATCH"

    # Unknown transaction
    r_unknown = client.get("/api/reconciliation/transactions/ORD-NONEXISTENT")
    assert r_unknown.status_code == 404
    assert "not found" in r_unknown.json()["detail"]


# 8. AI investigation lookup
def test_ai_investigation_lookup():
    """Verify GET /api/investigations/{order_id} behavior."""
    client.post("/api/reconciliation/run")

    # Known AI-investigated transaction ORD-8494
    r_found = client.get("/api/investigations/ORD-8494")
    assert r_found.status_code == 200
    data = r_found.json()
    assert data["order_id"] == "ORD-8494"
    assert data["classification"] == "CROSS_BORDER_FX_EXPOSURE"
    assert data["recommended_action"] == "ESCALATE_TO_TREASURY_FX_DESK"
    assert data["human_review_required"] is True

    # Known non-AI transaction (ORD-8492) -> 404
    r_not_investigated = client.get("/api/investigations/ORD-8492")
    assert r_not_investigated.status_code == 404
    assert "was not investigated by AI" in r_not_investigated.json()["detail"]

    # Unknown order ID -> 404
    r_unknown = client.get("/api/investigations/ORD-UNKNOWN")
    assert r_unknown.status_code == 404


# 9. Evaluation endpoint
def test_evaluation_metrics_endpoint():
    """Verify GET /api/evaluation/metrics returns authentic BatchEvaluation structure."""
    client.post("/api/reconciliation/run")

    response = client.get("/api/evaluation/metrics")
    assert response.status_code == 200
    eval_data = response.json()

    assert eval_data["total_records"] == 120
    assert eval_data["matched_records"] == 85
    assert eval_data["exception_records"] == 30
    assert eval_data["pending_review_records"] == 5
    assert eval_data["resolved_records"] == 85
    assert eval_data["unresolved_records"] == 35

    assert eval_data["rule_accuracy"] == "1.0000"
    assert eval_data["status_accuracy"] == "1.0000"
    assert eval_data["deterministic_resolution_rate"] == "0.7083"
    assert eval_data["exception_rate"] == "0.2500"
    assert eval_data["pending_review_rate"] == "0.0417"

    # Confusion matrix
    cm = eval_data["confusion_matrix"]
    assert cm["true_positives"] == 85
    assert cm["true_negatives"] == 35
    assert cm["false_positives"] == 0
    assert cm["false_negatives"] == 0

    # Category metrics
    assert len(eval_data["category_metrics"]) == 8


# 11. Invalid query parameters validation
def test_invalid_query_parameter_validation():
    """Verify invalid enum query parameters return HTTP 422."""
    client.post("/api/reconciliation/run")

    # Invalid status
    r_invalid_status = client.get("/api/reconciliation/transactions?status=INVALID_STATUS")
    assert r_invalid_status.status_code == 422

    # Invalid rule_id
    r_invalid_rule = client.get("/api/reconciliation/transactions?rule_id=INVALID_RULE")
    assert r_invalid_rule.status_code == 422


# 12. Multiple filters (AND semantics)
def test_multiple_filters_and_semantics():
    """Verify combining multiple filters applies AND semantics."""
    client.post("/api/reconciliation/run")

    # Matching condition: EXCEPTION and RULE_08 -> 8 records
    r1 = client.get("/api/reconciliation/transactions?status=EXCEPTION&rule_id=RULE_08_AMOUNT_MISMATCH")
    assert r1.status_code == 200
    assert len(r1.json()) == 8

    # Non-matching condition: MATCHED and RULE_08 -> 0 records
    r2 = client.get("/api/reconciliation/transactions?status=MATCHED&rule_id=RULE_08_AMOUNT_MISMATCH")
    assert r2.status_code == 200
    assert len(r2.json()) == 0

    # PENDING_REVIEW and requires_ai=true -> 5 records (RULE_04)
    r3 = client.get("/api/reconciliation/transactions?status=PENDING_REVIEW&requires_ai=true")
    assert r3.status_code == 200
    assert len(r3.json()) == 5
