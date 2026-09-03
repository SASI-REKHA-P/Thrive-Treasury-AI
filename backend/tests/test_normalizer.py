from decimal import Decimal
from datetime import datetime, timezone
import pytest
from app.services.data_loader import DataLoader
from app.services.normalizer import Normalizer, NormalizationError
from app.models.transaction import PaymentRecord, SettlementRecord
from app.models.normalized import NormalizedBatch, NormalizedPayment, NormalizedSettlement


@pytest.fixture
def loaded_batch():
    """Fixture providing raw loaded batch."""
    loader = DataLoader()
    return loader.load_synthetic_batch()


def test_normalizer_batch_counts_and_preservation(loaded_batch):
    """Verify that normalizer produces a NormalizedBatch with all 120 payments and 117 settlements."""
    normalized_batch = Normalizer.normalize_batch(loaded_batch)

    assert isinstance(normalized_batch, NormalizedBatch)
    assert normalized_batch.batch_id == "BATCH-2026-SYNTH-120"
    assert len(normalized_batch.payments) == 120
    assert len(normalized_batch.settlements) == 117


def test_normalizer_anchor_ord_8492(loaded_batch):
    """Verify anchor record ORD-8492 is preserved accurately."""
    normalized_batch = Normalizer.normalize_batch(loaded_batch)

    p_8492 = next(p for p in normalized_batch.payments if p.order_id == "ORD-8492")
    s_8492 = next(s for s in normalized_batch.settlements if s.order_ref == "ORD-8492")

    assert p_8492.order_id == "ORD-8492"
    assert p_8492.auth_ref == "AUTH-8492-PG"
    assert p_8492.gross_amount == Decimal("4200.00")
    assert p_8492.currency == "INR"
    assert s_8492.net_deposit == Decimal("4200.00")
    assert s_8492.settlement_currency == "INR"
    assert p_8492.gross_amount - s_8492.net_deposit == Decimal("0.00")


def test_normalizer_anchor_ord_8493(loaded_batch):
    """Verify anchor record ORD-8493 preserves 15000.00 vs 14646.00 with Decimal precision."""
    normalized_batch = Normalizer.normalize_batch(loaded_batch)

    p_8493 = next(p for p in normalized_batch.payments if p.order_id == "ORD-8493")
    s_8493 = next(s for s in normalized_batch.settlements if s.order_ref == "ORD-8493")

    assert p_8493.gross_amount == Decimal("15000.00")
    assert s_8493.net_deposit == Decimal("14646.00")
    assert p_8493.currency == "INR"
    assert s_8493.settlement_currency == "INR"
    assert p_8493.gross_amount - s_8493.net_deposit == Decimal("354.00")


def test_normalizer_anchor_ord_8494(loaded_batch):
    """Verify anchor record ORD-8494 preserves USD payment, INR settlement, and tz-aware timestamps."""
    normalized_batch = Normalizer.normalize_batch(loaded_batch)

    p_8494 = next(p for p in normalized_batch.payments if p.order_id == "ORD-8494")
    s_8494 = next(s for s in normalized_batch.settlements if s.order_ref == "ORD-8494")

    assert p_8494.gross_amount == Decimal("500.00")
    assert p_8494.currency == "USD"
    assert s_8494.net_deposit == Decimal("41200.00")
    assert s_8494.settlement_currency == "INR"
    assert p_8494.booking_timestamp.tzinfo is not None
    assert s_8494.clearing_timestamp.tzinfo is not None


def test_all_normalized_amounts_are_decimal(loaded_batch):
    """Verify 100% of payments and settlements use Decimal (no floats)."""
    normalized_batch = Normalizer.normalize_batch(loaded_batch)

    for p in normalized_batch.payments:
        assert isinstance(p.gross_amount, Decimal), f"Payment {p.order_id} is not Decimal"
        assert not isinstance(p.gross_amount, float)

    for s in normalized_batch.settlements:
        assert isinstance(s.net_deposit, Decimal), f"Settlement {s.settlement_id} is not Decimal"
        assert not isinstance(s.net_deposit, float)


def test_all_normalized_timestamps_are_timezone_aware(loaded_batch):
    """Verify 100% of normalized timestamps are timezone-aware."""
    normalized_batch = Normalizer.normalize_batch(loaded_batch)

    assert normalized_batch.generated_at.tzinfo is not None

    for p in normalized_batch.payments:
        assert p.booking_timestamp.tzinfo is not None, f"Payment {p.order_id} has naive timestamp"

    for s in normalized_batch.settlements:
        assert s.clearing_timestamp.tzinfo is not None, f"Settlement {s.settlement_id} has naive timestamp"


def test_all_currencies_are_uppercase(loaded_batch):
    """Verify all currency codes are normalized to uppercase ISO strings."""
    normalized_batch = Normalizer.normalize_batch(loaded_batch)

    for p in normalized_batch.payments:
        assert p.currency == p.currency.upper()
        assert len(p.currency) == 3

    for s in normalized_batch.settlements:
        assert s.settlement_currency == s.settlement_currency.upper()
        assert len(s.settlement_currency) == 3


def test_no_ground_truth_leakage_in_normalized_models(loaded_batch):
    """Verify no ground truth fields exist in normalized operational records."""
    normalized_batch = Normalizer.normalize_batch(loaded_batch)

    forbidden_fields = {"ground_truth_category", "expected_status", "expected_rule"}

    for p in normalized_batch.payments:
        field_names = set(p.model_dump().keys())
        assert not (field_names & forbidden_fields), f"Leakage found in payment {p.order_id}"

    for s in normalized_batch.settlements:
        field_names = set(s.model_dump().keys())
        assert not (field_names & forbidden_fields), f"Leakage found in settlement {s.settlement_id}"


def test_normalizer_rejects_naive_timestamp():
    """Verify normalizer rejects naive datetimes without timezone info."""
    naive_payment = PaymentRecord(
        order_id="ORD-NAIVE",
        auth_ref="AUTH-NAIVE",
        gross_amount=Decimal("100.00"),
        currency="INR",
        payment_method="UPI",
        booking_timestamp=datetime(2026, 9, 1, 10, 0, 0),  # Naive (tzinfo=None)
    )

    with pytest.raises(NormalizationError) as exc_info:
        Normalizer.normalize_payment(naive_payment)
    assert "naive" in str(exc_info.value).lower()


def test_normalizer_trims_whitespace_and_uppercases():
    """Verify whitespace is trimmed and currency is uppercased."""
    raw_payment = PaymentRecord(
        order_id="  ORD-TRIM-01  ",
        auth_ref="  AUTH-TRIM-01  ",
        gross_amount=Decimal("250.00"),
        currency="inr",  # lowercase
        payment_method="  card  ",
        booking_timestamp=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    normalized = Normalizer.normalize_payment(raw_payment)

    assert normalized.order_id == "ORD-TRIM-01"
    assert normalized.auth_ref == "AUTH-TRIM-01"
    assert normalized.currency == "INR"
    assert normalized.payment_method == "card"
    assert normalized.gross_amount == Decimal("250.00")
