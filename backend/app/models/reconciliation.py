from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Literal
from pydantic import Field
from .base import FinancialBaseModel
from .ai_investigation import AIInvestigationOutput


class ReconciliationRule(str, Enum):
    """Frozen deterministic reconciliation rule identifiers."""
    RULE_01_EXACT_MATCH = "RULE_01_EXACT_MATCH"
    RULE_02_EXPECTED_FEE = "RULE_02_EXPECTED_FEE"
    RULE_03_DATE_TOLERANCE = "RULE_03_DATE_TOLERANCE"
    RULE_04_CROSS_CURRENCY_CHECK = "RULE_04_CROSS_CURRENCY_CHECK"
    RULE_05_MISSING_SETTLEMENT = "RULE_05_MISSING_SETTLEMENT"
    RULE_06_DUPLICATE_CHECK = "RULE_06_DUPLICATE_CHECK"
    RULE_07_CURRENCY_MISMATCH = "RULE_07_CURRENCY_MISMATCH"
    RULE_08_AMOUNT_MISMATCH = "RULE_08_AMOUNT_MISMATCH"


class ReconciliationStatus(str, Enum):
    """Canonical lifecycle reconciliation statuses."""
    MATCHED = "MATCHED"
    EXCEPTION = "EXCEPTION"
    PENDING_REVIEW = "PENDING_REVIEW"


class ReconciliationChecks(FinancialBaseModel):
    """Deterministic check booleans evaluated for a transaction pair."""
    reference_match: bool = Field(default=False, description="Whether auth/order reference matches")
    currency_match: bool = Field(default=False, description="Whether currencies match exactly")
    amount_match: bool = Field(default=False, description="Whether amounts match exactly")
    date_tolerance: bool = Field(default=False, description="Whether settlement cleared within window (<=72h)")
    duplicate_check: bool = Field(default=False, description="Whether duplicate settlements were detected")
    settlement_present: bool = Field(default=False, description="Whether a settlement record exists")


class ReconciliationResult(FinancialBaseModel):
    """Structured reconciliation output produced by the deterministic engine."""
    order_id: str = Field(..., description="Target order reference")
    status: ReconciliationStatus = Field(..., description="Reconciliation classification outcome")
    rule_id: ReconciliationRule = Field(..., description="Deterministic rule identifier that caused the decision")
    match_method: str = Field(..., description="Human-readable rule or method descriptor")
    payment_amount: Decimal = Field(..., description="Normalized gross payment amount")
    payment_currency: str = Field(..., description="Payment currency code")
    settlement_amount: Optional[Decimal] = Field(default=None, description="Normalized net settlement amount if available")
    settlement_currency: Optional[str] = Field(default=None, description="Settlement currency code if available")
    difference: Optional[Decimal] = Field(default=None, description="Signed variance (Payment - Settlement) if available")
    settlement_ids: List[str] = Field(default_factory=list, description="Associated settlement record identifiers")
    checks: ReconciliationChecks = Field(default_factory=ReconciliationChecks, description="Rule evaluation flags")
    requires_ai: bool = Field(default=False, description="Whether contextual AI investigation is required")
    requires_human_review: bool = Field(default=False, description="Whether human review queue escalation is required")
    reason: str = Field(..., description="Concise explainable deterministic statement for the outcome")
    ai_status: Literal["NOT_REQUIRED", "PENDING", "INVESTIGATED"] = Field(
        default="NOT_REQUIRED", description="Lifecycle status of AI investigation"
    )
    human_review_status: Literal["NOT_REQUIRED", "REVIEW_REQUIRED", "RESOLVED", "ESCALATED"] = Field(
        default="NOT_REQUIRED", description="Lifecycle status of human review queue"
    )

    ai_investigation: Optional[AIInvestigationOutput] = Field(
        default=None, description="Advisory AI exception investigation report"
    )
