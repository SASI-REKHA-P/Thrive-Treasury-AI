from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Set
from app.models.reconciliation import ReconciliationResult
from app.models.transaction import GroundTruthDataset, GroundTruthEntry
from app.models.evaluation import BatchEvaluation, CategoryMetrics, ConfusionMatrix


class EvaluationError(Exception):
    """Raised when evaluation integrity validation fails."""
    pass


class BatchEvaluator:
    """
    Deterministic Batch Evaluation Service.
    
    Compares observed reconciliation engine outputs against isolated ground-truth benchmarks.
    Computes authentic, reproducible classification accuracy, operational resolution rates,
    confusion matrices, and category breakdowns without fabricating any values.
    """

    RATE_QUANTIZER = Decimal("0.0001")

    @classmethod
    def evaluate(
        cls,
        results: List[ReconciliationResult],
        ground_truth: GroundTruthDataset,
        processing_time_ms: Decimal,
        batch_id: Optional[str] = None,
    ) -> BatchEvaluation:
        """
        Evaluate a complete batch of reconciliation results against benchmark ground truth.
        
        Args:
            results: Complete list of ReconciliationResult objects produced by the engine.
            ground_truth: Isolated GroundTruthDataset loaded by the evaluation service.
            processing_time_ms: Actual measured execution latency in milliseconds.
            batch_id: Optional batch identifier override. Defaults to ground_truth.batch_id.
            
        Returns:
            BatchEvaluation report containing all calculated metrics.
            
        Raises:
            EvaluationError: On missing results, unexpected results, duplicate order IDs, or non-positive latency.
        """
        # 1. Validate processing latency
        if processing_time_ms <= Decimal("0"):
            raise EvaluationError(
                f"processing_time_ms must be strictly positive, got {processing_time_ms}. "
                "Throughput cannot be calculated from zero or negative latency."
            )

        # 2. Validate count matching
        if len(results) != len(ground_truth.records):
            raise EvaluationError(
                f"Result count ({len(results)}) does not match ground-truth count ({len(ground_truth.records)})."
            )

        # 3. Validate duplicate order IDs in results
        seen_order_ids: Set[str] = set()
        for r in results:
            if r.order_id in seen_order_ids:
                raise EvaluationError(f"Duplicate result order_id detected: '{r.order_id}'.")
            seen_order_ids.add(r.order_id)

        # 4. Build ground-truth lookup index
        gt_map: Dict[str, GroundTruthEntry] = {
            entry.order_id: entry for entry in ground_truth.records
        }

        # 5. Check for unknown engine results
        for r in results:
            if r.order_id not in gt_map:
                raise EvaluationError(
                    f"Engine result order_id '{r.order_id}' does not exist in ground truth."
                )

        # 6. Check for missing ground-truth records
        missing_ids = set(gt_map.keys()) - seen_order_ids
        if missing_ids:
            raise EvaluationError(
                f"Ground-truth order_id(s) missing from engine results: {sorted(missing_ids)}."
            )

        # 7. Accumulate statistics
        total_records = len(results)
        matched_records = 0
        exception_records = 0
        pending_review_records = 0

        rule_matches = 0
        status_matches = 0

        tp = 0
        tn = 0
        fp = 0
        fn = 0

        rule_distribution: Dict[str, int] = {}
        category_data: Dict[str, Dict] = {}

        for r in results:
            gt_entry = gt_map[r.order_id]
            actual_rule = r.rule_id.value
            actual_status = r.status.value
            expected_rule = gt_entry.expected_rule
            expected_status = gt_entry.expected_status
            cat = gt_entry.ground_truth_category

            # Track rule distribution
            rule_distribution[actual_rule] = rule_distribution.get(actual_rule, 0) + 1

            # Track status counts
            if actual_status == "MATCHED":
                matched_records += 1
            elif actual_status == "EXCEPTION":
                exception_records += 1
            elif actual_status == "PENDING_REVIEW":
                pending_review_records += 1

            # Check benchmark accuracy
            is_rule_match = (actual_rule == expected_rule)
            is_status_match = (actual_status == expected_status)

            if is_rule_match:
                rule_matches += 1
            if is_status_match:
                status_matches += 1

            # Binary Resolution Confusion Matrix:
            # Positive = MATCHED, Negative = UNRESOLVED (EXCEPTION or PENDING_REVIEW)
            is_actual_resolved = (actual_status == "MATCHED")
            is_expected_resolved = (expected_status == "MATCHED")

            if is_expected_resolved and is_actual_resolved:
                tp += 1
            elif (not is_expected_resolved) and (not is_actual_resolved):
                tn += 1
            elif (not is_expected_resolved) and is_actual_resolved:
                fp += 1
            elif is_expected_resolved and (not is_actual_resolved):
                fn += 1

            # Category accumulator
            if cat not in category_data:
                category_data[cat] = {
                    "total": 0,
                    "rule_matches": 0,
                    "status_matches": 0,
                    "primary_status": expected_status,
                    "primary_rule": expected_rule,
                }
            category_data[cat]["total"] += 1
            if is_rule_match:
                category_data[cat]["rule_matches"] += 1
            if is_status_match:
                category_data[cat]["status_matches"] += 1

        # 8. Compute Rates using Decimal precision
        dec_total = Decimal(str(total_records))
        resolved_records = matched_records
        unresolved_records = exception_records + pending_review_records

        rule_accuracy = (Decimal(str(rule_matches)) / dec_total).quantize(cls.RATE_QUANTIZER)
        status_accuracy = (Decimal(str(status_matches)) / dec_total).quantize(cls.RATE_QUANTIZER)

        deterministic_resolution_rate = (Decimal(str(resolved_records)) / dec_total).quantize(
            cls.RATE_QUANTIZER
        )
        exception_rate = (Decimal(str(exception_records)) / dec_total).quantize(cls.RATE_QUANTIZER)
        pending_review_rate = (Decimal(str(pending_review_records)) / dec_total).quantize(
            cls.RATE_QUANTIZER
        )

        # 9. Compute Throughput
        latency_seconds = processing_time_ms / Decimal("1000")
        throughput_per_sec = (dec_total / latency_seconds).quantize(Decimal("0.01"))

        # 10. Build Category Metrics
        category_metrics: Dict[str, CategoryMetrics] = {}
        for cat_name, c_data in category_data.items():
            cat_total = Decimal(str(c_data["total"]))
            cat_rule_acc = (Decimal(str(c_data["rule_matches"])) / cat_total).quantize(
                cls.RATE_QUANTIZER
            )
            cat_status_acc = (Decimal(str(c_data["status_matches"])) / cat_total).quantize(
                cls.RATE_QUANTIZER
            )
            category_metrics[cat_name] = CategoryMetrics(
                category=cat_name,
                total_records=c_data["total"],
                rule_matches=c_data["rule_matches"],
                status_matches=c_data["status_matches"],
                rule_accuracy=cat_rule_acc,
                status_accuracy=cat_status_acc,
                primary_status=c_data["primary_status"],
                primary_rule=c_data["primary_rule"],
            )

        resolved_batch_id = batch_id or ground_truth.batch_id

        return BatchEvaluation(
            batch_id=resolved_batch_id,
            evaluated_at=datetime.now(timezone.utc),
            total_records=total_records,
            matched_records=matched_records,
            exception_records=exception_records,
            pending_review_records=pending_review_records,
            resolved_records=resolved_records,
            unresolved_records=unresolved_records,
            rule_accuracy=rule_accuracy,
            status_accuracy=status_accuracy,
            deterministic_resolution_rate=deterministic_resolution_rate,
            exception_rate=exception_rate,
            pending_review_rate=pending_review_rate,
            confusion_matrix=ConfusionMatrix(
                true_positives=tp,
                true_negatives=tn,
                false_positives=fp,
                false_negatives=fn,
            ),
            category_metrics=category_metrics,
            rule_distribution=rule_distribution,
            processing_time_ms=processing_time_ms,
            throughput_per_sec=throughput_per_sec,
        )
