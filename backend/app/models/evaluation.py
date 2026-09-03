from datetime import datetime
from decimal import Decimal
from typing import Dict
from pydantic import Field
from .base import FinancialBaseModel


class CategoryMetrics(FinancialBaseModel):
    """Granular performance metrics for a specific ground-truth category."""
    category: str = Field(..., description="Ground-truth category identifier")
    total_records: int = Field(..., description="Count of transactions in this category")
    rule_matches: int = Field(..., description="Count of records matching expected rule")
    status_matches: int = Field(..., description="Count of records matching expected status")
    rule_accuracy: Decimal = Field(..., description="Rule accuracy rate (rule_matches / total)")
    status_accuracy: Decimal = Field(..., description="Status accuracy rate (status_matches / total)")
    primary_status: str = Field(..., description="Target status for category (MATCHED / EXCEPTION / PENDING_REVIEW)")
    primary_rule: str = Field(..., description="Target rule identifier for category")


class ConfusionMatrix(FinancialBaseModel):
    """
    Binary resolution classification matrix.
    Positive = RESOLVED (MATCHED)
    Negative = UNRESOLVED (EXCEPTION or PENDING_REVIEW)
    """
    true_positives: int = Field(default=0, description="Expected MATCHED and actual MATCHED")
    true_negatives: int = Field(default=0, description="Expected unresolved and actual unresolved")
    false_positives: int = Field(default=0, description="Expected unresolved but actual MATCHED")
    false_negatives: int = Field(default=0, description="Expected MATCHED but actual unresolved")


class BatchEvaluation(FinancialBaseModel):
    """Authentic performance evaluation report calculated against ground-truth benchmarks."""
    batch_id: str = Field(..., description="Target operational batch identifier")
    evaluated_at: datetime = Field(..., description="UTC-aware timestamp when evaluation executed")
    
    # Record Counts
    total_records: int = Field(..., description="Total transactions evaluated")
    matched_records: int = Field(..., description="Transactions with actual status MATCHED")
    exception_records: int = Field(..., description="Transactions with actual status EXCEPTION")
    pending_review_records: int = Field(..., description="Transactions with actual status PENDING_REVIEW")
    resolved_records: int = Field(..., description="Deterministically resolved records (MATCHED)")
    unresolved_records: int = Field(..., description="Unresolved records (EXCEPTION + PENDING_REVIEW)")
    
    # Accuracy Rates
    rule_accuracy: Decimal = Field(..., description="Exact rule match rate (actual rule == expected rule)")
    status_accuracy: Decimal = Field(..., description="Exact status match rate (actual status == expected status)")
    
    # Operational Treasury Rates
    deterministic_resolution_rate: Decimal = Field(
        ..., description="Proportion of batch deterministically cleared without human review (resolved / total)"
    )
    exception_rate: Decimal = Field(..., description="Exception rate (exception_records / total)")
    pending_review_rate: Decimal = Field(..., description="Pending review rate (pending_review_records / total)")
    
    # Statistical Matrix & Distributions
    confusion_matrix: ConfusionMatrix = Field(default_factory=ConfusionMatrix)
    category_metrics: Dict[str, CategoryMetrics] = Field(
        default_factory=dict, description="Performance broken down across all ground-truth categories"
    )
    rule_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Distribution of actual assigned rules across the batch"
    )
    
    # Authentic Performance Telemetry
    processing_time_ms: Decimal = Field(..., description="Measured processing latency in milliseconds")
    throughput_per_sec: Decimal = Field(..., description="Measured throughput in records per second")
