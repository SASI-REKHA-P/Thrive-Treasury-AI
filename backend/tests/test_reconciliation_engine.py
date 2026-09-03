from decimal import Decimal
import pytest
from app.services.data_loader import DataLoader
from app.services.normalizer import Normalizer
from app.services.engine import DeterministicReconciliationEngine
from app.models.reconciliation import ReconciliationRule, ReconciliationStatus


@pytest.fixture
def reconciled_batch():
    """Run full batch through DataLoader -> Normalizer -> DeterministicReconciliationEngine."""
    loader = DataLoader()
    raw_batch = loader.load_synthetic_batch()
    normalized_batch = Normalizer.normalize_batch(raw_batch)
    engine = DeterministicReconciliationEngine()
    results = engine.reconcile_batch(normalized_batch)
    gt_dataset = loader.load_ground_truth()
    return results, gt_dataset, normalized_batch


def test_full_batch_returns_120_results(reconciled_batch):
    """Test 1: Exactly 120 results produced."""
    results, _, _ = reconciled_batch
    assert len(results) == 120


def test_category_and_rule_counts(reconciled_batch):
    """Tests 2-9: Verify all 8 categories match target rule distributions."""
    results, gt_dataset, _ = reconciled_batch

    rule_counts = {}
    status_counts = {}
    for r in results:
        rule_counts[r.rule_id] = rule_counts.get(r.rule_id, 0) + 1
        status_counts[r.status] = status_counts.get(r.status, 0) + 1

    # Exact expected counts for each of the 8 frozen rules
    assert rule_counts[ReconciliationRule.RULE_01_EXACT_MATCH] == 60
    assert rule_counts[ReconciliationRule.RULE_02_EXPECTED_FEE] == 15
    assert rule_counts[ReconciliationRule.RULE_03_DATE_TOLERANCE] == 10
    assert rule_counts[ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK] == 5
    assert rule_counts[ReconciliationRule.RULE_05_MISSING_SETTLEMENT] == 10
    assert rule_counts[ReconciliationRule.RULE_06_DUPLICATE_CHECK] == 7
    assert rule_counts[ReconciliationRule.RULE_07_CURRENCY_MISMATCH] == 5
    assert rule_counts[ReconciliationRule.RULE_08_AMOUNT_MISMATCH] == 8

    # Status distribution
    assert status_counts[ReconciliationStatus.MATCHED] == 85
    assert status_counts[ReconciliationStatus.EXCEPTION] == 30
    assert status_counts[ReconciliationStatus.PENDING_REVIEW] == 5


def test_anchor_ord_8492(reconciled_batch):
    """Test 10: ORD-8492 -> RULE_01_EXACT_MATCH and MATCHED."""
    results, _, _ = reconciled_batch
    r = next(res for res in results if res.order_id == "ORD-8492")

    assert r.status == ReconciliationStatus.MATCHED
    assert r.rule_id == ReconciliationRule.RULE_01_EXACT_MATCH
    assert r.payment_amount == Decimal("4200.00")
    assert r.settlement_amount == Decimal("4200.00")
    assert r.difference == Decimal("0.00")
    assert "exactly matches" in r.reason.lower()


def test_anchor_ord_8493(reconciled_batch):
    """Test 11: ORD-8493 -> RULE_02_EXPECTED_FEE and MATCHED."""
    results, _, _ = reconciled_batch
    r = next(res for res in results if res.order_id == "ORD-8493")

    assert r.status == ReconciliationStatus.MATCHED
    assert r.rule_id == ReconciliationRule.RULE_02_EXPECTED_FEE
    assert r.payment_amount == Decimal("15000.00")
    assert r.settlement_amount == Decimal("14646.00")
    assert r.difference == Decimal("354.00")
    assert "2% mdr" in r.reason.lower()


def test_anchor_ord_8494(reconciled_batch):
    """Test 12: ORD-8494 -> RULE_04_CROSS_CURRENCY_CHECK and PENDING_REVIEW."""
    results, _, _ = reconciled_batch
    r = next(res for res in results if res.order_id == "ORD-8494")

    assert r.status == ReconciliationStatus.PENDING_REVIEW
    assert r.rule_id == ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK
    assert r.payment_amount == Decimal("500.00")
    assert r.payment_currency == "USD"
    assert r.settlement_amount == Decimal("41200.00")
    assert r.settlement_currency == "INR"
    assert r.requires_human_review is True
    assert "fx conversion is unavailable" in r.reason.lower()


def test_missing_settlement_cases(reconciled_batch):
    """Test 13: ORD-5001...ORD-5010 -> RULE_05_MISSING_SETTLEMENT."""
    results, _, _ = reconciled_batch
    missing_ids = [f"ORD-50{i:02d}" for i in range(1, 11)]

    for oid in missing_ids:
        r = next(res for res in results if res.order_id == oid)
        assert r.status == ReconciliationStatus.EXCEPTION
        assert r.rule_id == ReconciliationRule.RULE_05_MISSING_SETTLEMENT
        assert r.settlement_amount is None
        assert len(r.settlement_ids) == 0
        assert r.requires_human_review is True


def test_duplicate_settlement_cases(reconciled_batch):
    """Test 14: ORD-4001...ORD-4007 -> RULE_06_DUPLICATE_CHECK."""
    results, _, _ = reconciled_batch
    dup_ids = [f"ORD-40{i:02d}" for i in range(1, 8)]

    for oid in dup_ids:
        r = next(res for res in results if res.order_id == oid)
        assert r.status == ReconciliationStatus.EXCEPTION
        assert r.rule_id == ReconciliationRule.RULE_06_DUPLICATE_CHECK
        assert len(r.settlement_ids) == 2  # Preserves both duplicates
        assert r.checks.duplicate_check is True
        assert r.requires_human_review is True


def test_no_floats_and_decimal_precision(reconciled_batch):
    """Test 15: No floats used in monetary fields."""
    results, _, _ = reconciled_batch

    for r in results:
        assert isinstance(r.payment_amount, Decimal)
        assert not isinstance(r.payment_amount, float)
        if r.settlement_amount is not None:
            assert isinstance(r.settlement_amount, Decimal)
            assert not isinstance(r.settlement_amount, float)
        if r.difference is not None:
            assert isinstance(r.difference, Decimal)
            assert not isinstance(r.difference, float)


def test_every_result_has_rule_and_explanation(reconciled_batch):
    """Tests 16 & 17: Every result has a rule_id and clear explanation."""
    results, _, _ = reconciled_batch

    for r in results:
        assert isinstance(r.rule_id, ReconciliationRule)
        assert len(r.rule_id.value) > 0
        assert isinstance(r.reason, str)
        assert len(r.reason.strip()) > 10


def test_decimal_variance_preserved(reconciled_batch):
    """Test 18: Decimal variance accurately preserved for fee and mismatch cases."""
    results, _, _ = reconciled_batch

    for r in results:
        if r.settlement_amount is not None and r.payment_currency == r.settlement_currency:
            expected_diff = r.payment_amount - r.settlement_amount
            assert r.difference == expected_diff


def test_duplicate_settlements_not_silently_ignored(reconciled_batch):
    """Test 19: Both settlements referenced for duplicates."""
    results, _, _ = reconciled_batch
    dup_results = [r for r in results if r.rule_id == ReconciliationRule.RULE_06_DUPLICATE_CHECK]

    assert len(dup_results) == 7
    for dr in dup_results:
        assert len(dr.settlement_ids) == 2


def test_deterministic_repeated_execution(reconciled_batch):
    """Test 20: Engine is 100% deterministic across multiple repeated runs."""
    results1, _, normalized_batch = reconciled_batch
    engine = DeterministicReconciliationEngine()
    results2 = engine.reconcile_batch(normalized_batch)
    results3 = engine.reconcile_batch(normalized_batch)

    assert len(results1) == len(results2) == len(results3) == 120

    for r1, r2, r3 in zip(results1, results2, results3):
        assert r1.order_id == r2.order_id == r3.order_id
        assert r1.status == r2.status == r3.status
        assert r1.rule_id == r2.rule_id == r3.rule_id
        assert r1.difference == r2.difference == r3.difference
        assert r1.reason == r2.reason == r3.reason
        assert r1.settlement_ids == r2.settlement_ids == r3.settlement_ids


def test_strict_record_by_record_benchmark_match(reconciled_batch):
    """
    Test 21: Strict record-by-record benchmark assertion covering all 120 records.
    Asserts:
      - actual rule_id == ground_truth expected_rule (120/120)
      - actual status == ground_truth expected_status (120/120)
    """
    results, gt_dataset, _ = reconciled_batch
    gt_map = {entry.order_id: entry for entry in gt_dataset.records}

    assert len(results) == 120
    assert len(gt_map) == 120

    for result in results:
        gt_entry = gt_map.get(result.order_id)
        assert gt_entry is not None, f"Missing ground truth entry for {result.order_id}"

        # Strict rule match
        assert (
            result.rule_id.value == gt_entry.expected_rule
        ), f"Rule mismatch for {result.order_id}: actual={result.rule_id.value} vs expected={gt_entry.expected_rule}"

        # Strict status match
        assert (
            result.status.value == gt_entry.expected_status
        ), f"Status mismatch for {result.order_id}: actual={result.status.value} vs expected={gt_entry.expected_status}"

