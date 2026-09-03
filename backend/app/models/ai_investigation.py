from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Literal
from pydantic import Field, field_validator
from .base import FinancialBaseModel


class AIClassification(str, Enum):
    """Frozen AI exception classification categories."""
    NON_STANDARD_INTERCHANGE_FEE = "NON_STANDARD_INTERCHANGE_FEE"
    UNEXPLAINED_GATEWAY_SHORTFALL = "UNEXPLAINED_GATEWAY_SHORTFALL"
    CROSS_BORDER_FX_EXPOSURE = "CROSS_BORDER_FX_EXPOSURE"
    INCONCLUSIVE_VARIANCE = "INCONCLUSIVE_VARIANCE"


class AIRecommendedAction(str, Enum):
    """Frozen AI recommended operational actions for finance controllers."""
    APPLY_RATE_CARD_ADJUSTMENT = "APPLY_RATE_CARD_ADJUSTMENT"
    ESCALATE_TO_TREASURY_FX_DESK = "ESCALATE_TO_TREASURY_FX_DESK"
    INITIATE_ACQUIRER_DISPUTE = "INITIATE_ACQUIRER_DISPUTE"
    MANUAL_CONTROLLER_AUDIT = "MANUAL_CONTROLLER_AUDIT"


class AIConfidenceTier(str, Enum):
    """Operational confidence heuristic tiers."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AIInvestigationInput(FinancialBaseModel):
    """Sanitized operational and deterministic facts provided to the AI investigator."""
    order_id: str = Field(..., description="Target order reference identifier")
    auth_ref: str = Field(..., description="Gateway authorization reference")
    gross_amount: Decimal = Field(..., description="Gross payment amount in transaction currency")
    currency: str = Field(..., description="Payment currency code (ISO-4217)")
    payment_method: str = Field(..., description="Payment rail / channel (e.g. UPI, CREDIT_CARD)")
    booking_timestamp: datetime = Field(..., description="Booking creation timestamp in UTC")

    # Observed Settlement Data (if present)
    settlement_id: Optional[str] = Field(default=None, description="Matching settlement identifier if found")
    net_deposit: Optional[Decimal] = Field(default=None, description="Net deposit amount in settlement currency")
    settlement_currency: Optional[str] = Field(default=None, description="Settlement currency code (ISO-4217)")
    clearing_timestamp: Optional[datetime] = Field(default=None, description="Bank clearing timestamp in UTC")
    bank_account_ref: Optional[str] = Field(default=None, description="Destination bank account identifier")

    # Deterministic Engine Findings
    rule_id: str = Field(..., description="Deterministic rule identifier assigned by engine")
    deterministic_status: str = Field(..., description="Deterministic status assigned by engine")
    variance_amount: Optional[Decimal] = Field(default=None, description="Calculated signed difference (payment - settlement)")
    deterministic_explanation: str = Field(..., description="Explainable deterministic statement from engine")

    # Reference Context (Computed deterministically by application)
    standard_expected_fee: Optional[Decimal] = Field(
        default=None, description="Configured expected standard fee (2.0% MDR + 18% GST)"
    )
    effective_implied_rate: Optional[Decimal] = Field(
        default=None, description="Observed derived nominal rate (net_deposit / gross_amount for cross-currency)"
    )


class LLMInvestigationPayload(FinancialBaseModel):
    """Substantive investigation result produced by the AI model."""
    classification: AIClassification = Field(..., description="Classified exception category")
    confidence: Decimal = Field(..., description="Heuristic operational confidence score between 0.00 and 1.00")
    confidence_tier: AIConfidenceTier = Field(..., description="Confidence tier: HIGH (>=0.85), MEDIUM (0.60-0.8499), LOW (<0.60)")
    root_cause_analysis: str = Field(..., description="Contextual analysis citing observed evidence without unsupported claims")
    recommended_action: AIRecommendedAction = Field(..., description="Recommended next action for the controller")
    human_review_required: bool = Field(default=True, description="Whether human review is required")
    evidence_used: List[str] = Field(default_factory=list, description="Citations of operational input fields used in reasoning")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00") or v > Decimal("1.00"):
            raise ValueError(f"Confidence must be between 0.00 and 1.00, got {v}")
        return v


class AIInvestigationOutput(FinancialBaseModel):
    """Complete application-level investigation record attached to ReconciliationResult."""
    investigation_id: str = Field(..., description="Unique UUID for this investigation event")
    order_id: str = Field(..., description="Target order reference identifier")
    investigated_at: datetime = Field(..., description="UTC timestamp of investigation")
    classification: AIClassification = Field(..., description="Classified exception category")
    confidence: Decimal = Field(..., description="Heuristic operational confidence score between 0.00 and 1.00")
    confidence_tier: AIConfidenceTier = Field(..., description="Programmatically enforced confidence tier")
    root_cause_analysis: str = Field(..., description="Contextual analysis citing observed evidence without unsupported claims")
    recommended_action: AIRecommendedAction = Field(..., description="Recommended next action for the controller")
    human_review_required: bool = Field(default=True, description="Programmatically enforced human review requirement")
    evidence_used: List[str] = Field(default_factory=list, description="Citations of operational input fields used in reasoning")
