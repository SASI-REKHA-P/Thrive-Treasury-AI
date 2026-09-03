from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import Field, field_validator
from .base import FinancialBaseModel


class NormalizedPayment(FinancialBaseModel):
    """Normalized internal representation of a payment record for reconciliation."""
    order_id: str = Field(..., description="Canonical trimmed order reference")
    auth_ref: str = Field(..., description="Canonical trimmed gateway authorization reference")
    gross_amount: Decimal = Field(..., description="Exact gross payment amount in Decimal")
    currency: str = Field(..., description="Canonical uppercase ISO-4217 currency code")
    payment_method: str = Field(..., description="Canonical trimmed payment channel/rail")
    booking_timestamp: datetime = Field(..., description="Timezone-aware booking timestamp in UTC")

    @field_validator("booking_timestamp")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("booking_timestamp must be timezone-aware (naive datetimes are prohibited)")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("order_id", "auth_ref", "payment_method")
    @classmethod
    def trim_text(cls, v: str) -> str:
        return v.strip()


class NormalizedSettlement(FinancialBaseModel):
    """Normalized internal representation of a settlement record for reconciliation."""
    settlement_id: str = Field(..., description="Canonical trimmed settlement record identifier")
    order_ref: str = Field(..., description="Canonical trimmed associated order reference")
    auth_ref: str = Field(..., description="Canonical trimmed matching authorization reference")
    net_deposit: Decimal = Field(..., description="Exact net deposit amount in Decimal")
    settlement_currency: str = Field(..., description="Canonical uppercase ISO-4217 settlement currency code")
    clearing_timestamp: datetime = Field(..., description="Timezone-aware clearing timestamp in UTC")
    bank_account_ref: str = Field(..., description="Canonical trimmed bank account clearing identifier")

    @field_validator("clearing_timestamp")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("clearing_timestamp must be timezone-aware (naive datetimes are prohibited)")
        return v

    @field_validator("settlement_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("settlement_id", "order_ref", "auth_ref", "bank_account_ref")
    @classmethod
    def trim_text(cls, v: str) -> str:
        return v.strip()


class NormalizedBatch(FinancialBaseModel):
    """Normalized operational batch container ready for the deterministic reconciliation engine."""
    batch_id: str = Field(..., description="Batch identifier")
    generated_at: datetime = Field(..., description="Timezone-aware batch generation timestamp")
    description: str = Field(..., description="Batch description")
    payments: List[NormalizedPayment] = Field(default_factory=list, description="List of normalized payments")
    settlements: List[NormalizedSettlement] = Field(default_factory=list, description="List of normalized settlements")
