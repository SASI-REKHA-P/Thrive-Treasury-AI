from decimal import Decimal
import copy
import pytest

from app.services.data_loader import DataLoader
from app.services.normalizer import Normalizer
from app.services.engine import DeterministicReconciliationEngine
from app.services.evaluator import BatchEvaluator, EvaluationError
from app.models.evaluation import BatchEvaluation


@pytest.fixture
def evaluation_inputs():
    """Load, normalize, and reconcile full operational batch, and load ground truth."""
    loader = DataLoader()
    raw_batch = loader.load_synthetic_batch()
    norm_batch = Normalizer.normalize_batch(raw_batch)
    engine = DeterministicReconciliationEngine()
    results = engine.reconcile_batch(norm_batch)
    gt_dataset = loader.load_ground_truth()
    fixed_latency_ms = Decimal("45.50")
    return results, gt_dataset, fixed_latency_ms


def test_complete_benchmark_evaluation(evaluation_inputs):
    """Test 1: Complete evaluation of the 120-record batch against ground truth."""
    results, gt_dataset, latency_ms = evaluation_inputs
    evaluation = BatchEvaluator.evaluate(results, gt_dataset, latency_ms)

    assert isinstance(evaluation, BatchEvaluation)
    assert evaluation.batch_id == "BATCH-2026-SYNTH-120"
    assert evaluation.total_records == 120

    # Accuracy Metrics
    assert evaluation.rule_accuracy == Decimal("1.0000")
    assert evaluation.status_accuracy == Decimal("1.0000")

    # Record Counts
    assert evaluation.matched_records == 85
    assert evaluation.exception_records == 30
    assert evaluation.pending_review_records == 5

    assert evaluation.resolved_records == 85
    assert evaluation.unresolved_records == 35

    # Operational Treasury Rates
    assert evaluation.deterministic_resolution_rate == Decimal("0.7083")
    assert evaluation.exception_rate == Decimal("0.2500")
    assert evaluation.pending_review_rate == Decimal("0.0417")

    # Latency & Throughput
    assert evaluation.processing_time_ms == latency_ms
    expected_throughput = (Decimal("120") / (latency_ms / Decimal("1000"))).quantize(Decimal("0.01"))
    assert evaluation.throughput_per_sec == expected_throughput


def test_category_breakdown_metrics(evaluation_inputs):
    """Test 2: Category breakdown across all 8 ground-truth categories."""
    results, gt_dataset, latency_ms = evaluation_inputs
    evaluation = BatchEvaluator.evaluate(results, gt_dataset, latency_ms)

    expected_categories = {
        "EXACT_MATCH": 60,
        "FEE_ADJUSTED_MATCH": 15,
        "DATE_TOLERANCE_MATCH": 10,
        "DUPLICATE_SETTLEMENT": 7,
        "MISSING_SETTLEMENT": 10,
        "AMOUNT_MISMATCH": 8,
        "CURRENCY_MISMATCH": 5,
        "CROSS_CURRENCY_AMBIGUITY": 5,
    }

    assert len(evaluation.category_metrics) == 8

    total_category_records = 0
    for cat_name, expected_count in expected_categories.items():
        assert cat_name in evaluation.category_metrics
        cat = evaluation.category_metrics[cat_name]
        assert cat.total_records == expected_count
        assert cat.rule_matches == expected_count
        assert cat.status_matches == expected_count
        assert cat.rule_accuracy == Decimal("1.0000")
        assert cat.status_accuracy == Decimal("1.0000")
        total_category_records += cat.total_records

    assert total_category_records == 120


def test_confusion_matrix_values(evaluation_inputs):
    """Test 3: Binary resolution confusion matrix values."""
    results, gt_dataset, latency_ms = evaluation_inputs
    evaluation = BatchEvaluator.evaluate(results, gt_dataset, latency_ms)

    cm = evaluation.confusion_matrix
    assert cm.true_positives == 85
    assert cm.true_negatives == 35
    assert cm.false_positives == 0
    assert cm.false_negatives == 0


def test_rule_distribution_counts(evaluation_inputs):
    """Test 4: Exact rule distribution matches engine assignments."""
    results, gt_dataset, latency_ms = evaluation_inputs
    evaluation = BatchEvaluator.evaluate(results, gt_dataset, latency_ms)

    expected_rules = {
        "RULE_01_EXACT_MATCH": 60,
        "RULE_02_EXPECTED_FEE": 15,
        "RULE_03_DATE_TOLERANCE": 10,
        "RULE_04_CROSS_CURRENCY_CHECK": 5,
        "RULE_05_MISSING_SETTLEMENT": 10,
        "RULE_06_DUPLICATE_CHECK": 7,
        "RULE_07_CURRENCY_MISMATCH": 5,
        "RULE_08_AMOUNT_MISMATCH": 8,
    }

    assert evaluation.rule_distribution == expected_rules


def test_missing_result_error(evaluation_inputs):
    """Test 5: Truncated results list raises EvaluationError."""
    results, gt_dataset, latency_ms = evaluation_inputs
    truncated_results = results[:-1]  # 119 records

    with pytest.raises(EvaluationError) as exc_info:
        BatchEvaluator.evaluate(truncated_results, gt_dataset, latency_ms)
    assert "does not match ground-truth count" in str(exc_info.value)


def test_unexpected_result_error(evaluation_inputs):
    """Test 6: Unknown order_id raises EvaluationError."""
    results, gt_dataset, latency_ms = evaluation_inputs
    modified_results = copy.deepcopy(results)
    # Replace first result's order_id with an unknown identifier
    modified_results[0].order_id = "ORD-UNKNOWN-9999"

    with pytest.raises(EvaluationError) as exc_info:
        BatchEvaluator.evaluate(modified_results, gt_dataset, latency_ms)
    assert "does not exist in ground truth" in str(exc_info.value)


def test_duplicate_result_error(evaluation_inputs):
    """Test 7: Duplicate result order_id raises EvaluationError."""
    results, gt_dataset, latency_ms = evaluation_inputs
    duplicate_results = copy.deepcopy(results)
    # Overwrite second result's order_id with first result's order_id
    duplicate_results[1].order_id = duplicate_results[0].order_id

    with pytest.raises(EvaluationError) as exc_info:
        BatchEvaluator.evaluate(duplicate_results, gt_dataset, latency_ms)
    assert "duplicate result order_id detected" in str(exc_info.value).lower()


def test_invalid_processing_time_error(evaluation_inputs):
    """Test 8: Non-positive processing_time_ms raises EvaluationError."""
    results, gt_dataset, _ = evaluation_inputs

    with pytest.raises(EvaluationError) as exc_info:
        BatchEvaluator.evaluate(results, gt_dataset, Decimal("0.00"))
    assert "strictly positive" in str(exc_info.value)

    with pytest.raises(EvaluationError) as exc_info:
        BatchEvaluator.evaluate(results, gt_dataset, Decimal("-10.00"))
    assert "strictly positive" in str(exc_info.value)


def test_evaluation_repeatability(evaluation_inputs):
    """Test 9: Multiple evaluation runs with identical inputs produce identical deterministic metrics."""
    results, gt_dataset, latency_ms = evaluation_inputs

    eval1 = BatchEvaluator.evaluate(results, gt_dataset, latency_ms)
    eval2 = BatchEvaluator.evaluate(results, gt_dataset, latency_ms)

    assert eval1.total_records == eval2.total_records
    assert eval1.matched_records == eval2.matched_records
    assert eval1.exception_records == eval2.exception_records
    assert eval1.pending_review_records == eval2.pending_review_records
    assert eval1.resolved_records == eval2.resolved_records
    assert eval1.unresolved_records == eval2.unresolved_records
    assert eval1.rule_accuracy == eval2.rule_accuracy
    assert eval1.status_accuracy == eval2.status_accuracy
    assert eval1.deterministic_resolution_rate == eval2.deterministic_resolution_rate
    assert eval1.exception_rate == eval2.exception_rate
    assert eval1.pending_review_rate == eval2.pending_review_rate
    assert eval1.throughput_per_sec == eval2.throughput_per_sec
    assert eval1.confusion_matrix == eval2.confusion_matrix
    assert eval1.rule_distribution == eval2.rule_distribution
    assert eval1.category_metrics == eval2.category_metrics
