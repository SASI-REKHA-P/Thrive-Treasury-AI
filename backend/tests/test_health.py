import json
from decimal import Decimal
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.models.transaction import PaymentRecord, SettlementRecord, SyntheticBatch

client = TestClient(app)


def test_health_endpoint():
    """Verify that GET /api/health responds with HTTP 200 and standard payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "thrive-treasury-ai"
    assert "version" in data


def test_dataset_paths_resolution():
    """Verify that backend configuration locates both root dataset files via pathlib."""
    path_checks = settings.verify_paths()
    assert path_checks["root_exists"], "Repository root could not be located"
    assert path_checks["data_dir_exists"], "Root data directory could not be located"
    assert path_checks["synthetic_batch_exists"], f"Missing synthetic batch at {settings.synthetic_dataset_path}"
    assert path_checks["ground_truth_exists"], f"Missing ground truth at {settings.ground_truth_dataset_path}"

    # Verify both JSON files are valid and loadable
    with open(settings.synthetic_dataset_path, "r", encoding="utf-8") as f:
        synthetic_data = json.load(f)
        assert synthetic_data["batch_id"] == "BATCH-2026-SYNTH-120"
        assert len(synthetic_data["payments"]) == 120
        assert len(synthetic_data["settlements"]) == 117

    with open(settings.ground_truth_dataset_path, "r", encoding="utf-8") as f:
        ground_truth_data = json.load(f)
        assert ground_truth_data["batch_id"] == "BATCH-2026-SYNTH-120"
        assert len(ground_truth_data["records"]) == 120


def test_models_decimal_precision():
    """Verify that models preserve Decimal precision and serialize safely."""
    payment = PaymentRecord(
        order_id="ORD-TEST-01",
        auth_ref="AUTH-TEST-01",
        gross_amount=Decimal("15000.00"),
        currency="INR",
        payment_method="NETBANKING",
        booking_timestamp=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    settlement = SettlementRecord(
        settlement_id="SET-TEST-01",
        order_ref="ORD-TEST-01",
        auth_ref="AUTH-TEST-01",
        net_deposit=Decimal("14646.00"),
        settlement_currency="INR",
        clearing_timestamp=datetime(2026, 9, 1, 14, 0, 0, tzinfo=timezone.utc),
        bank_account_ref="HDFC-CLR-01",
    )

    # Validate Python types
    assert isinstance(payment.gross_amount, Decimal)
    assert isinstance(settlement.net_deposit, Decimal)

    # Compute difference with 100% precision
    diff = payment.gross_amount - settlement.net_deposit
    assert diff == Decimal("354.00")

    # Validate JSON serialization (mode='json') preserves exact two-decimal string format
    dumped_payment = payment.model_dump(mode="json")
    dumped_settlement = settlement.model_dump(mode="json")

    assert dumped_payment["gross_amount"] == "15000.00"
    assert dumped_settlement["net_deposit"] == "14646.00"
    assert not isinstance(dumped_payment["gross_amount"], float)
