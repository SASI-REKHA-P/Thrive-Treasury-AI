from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import Field
from .base import FinancialBaseModel


class ExceptionRecord(FinancialBaseModel):
    """Isolated exception record routed for investigation or specialist review."""
    exception_id: str = Field(..., description="Unique exception identifier")
    order_id: str = Field(..., description="Associated order reference")
    batch_id: str = Field(..., description="Batch identifier in which exception occurred")
    exception_type: Literal[
        "AMOUNT_MISMATCH",
        "CROSS_CURRENCY_AMBIGUITY",
        "DUPLICATE_SETTLEMENT",
        "MISSING_SETTLEMENT",
        "TIMING_WINDOW_BREACH",
        "CURRENCY_MISMATCH"
    ] = Field(..., description="Classified exception category")
    discrepancy_amount: Optional[Decimal] = Field(default=None, description="Quantified monetary difference if any")
    currency: str = Field(default="INR", description="Currency of the discrepancy")
    severity: Literal["LOW", "MEDIUM", "HIGH"] = Field(default="MEDIUM", description="Operational triage severity")
    assigned_to: Literal["AI_INVESTIGATION", "HUMAN_REVIEW_QUEUE"] = Field(
        ..., description="Designated resolution channel"
    )
    status: Literal["OPEN", "IN_REVIEW", "RESOLVED"] = Field(default="OPEN", description="Current workflow status")
    created_at: datetime = Field(..., description="Timestamp when exception was isolated")
