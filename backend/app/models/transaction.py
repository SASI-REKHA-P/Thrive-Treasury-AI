from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from pydantic import Field
from .base import FinancialBaseModel


class PaymentRecord(FinancialBaseModel):
    """Observed customer checkout or gateway payment record."""
    order_id: str = Field(..., description="Unique order reference identifier")
    auth_ref: str = Field(..., description="Payment gateway authorization reference")
    gross_amount: Decimal = Field(..., description="Gross payment amount in transaction currency")
    currency: str = Field(..., description="3-letter ISO-4217 currency code")
    payment_method: str = Field(..., description="Payment rail/channel (e.g., UPI, CREDIT_CARD)")
    booking_timestamp: datetime = Field(..., description="Booking creation timestamp in UTC")


class SettlementRecord(FinancialBaseModel):
    """Observed bank clearing or processor settlement record."""
    settlement_id: str = Field(..., description="Unique settlement record identifier")
    order_ref: str = Field(..., description="Associated order reference identifier")
    auth_ref: str = Field(..., description="Matching authorization reference")
    net_deposit: Decimal = Field(..., description="Net deposit amount credited to bank account")
    settlement_currency: str = Field(..., description="3-letter ISO-4217 settlement currency code")
    clearing_timestamp: datetime = Field(..., description="Bank clearing timestamp in UTC")
    bank_account_ref: str = Field(..., description="Destination bank account / clearing ledger ID")


class SyntheticBatch(FinancialBaseModel):
    """Root operational batch container containing observed payment and settlement feeds."""
    batch_id: str = Field(..., description="Batch identifier (e.g. BATCH-2026-SYNTH-120)")
    generated_at: datetime = Field(..., description="Timestamp when batch was compiled")
    description: str = Field(..., description="Human-readable description of batch content")
    payments: List[PaymentRecord] = Field(default_factory=list, description="List of observed payments")
    settlements: List[SettlementRecord] = Field(default_factory=list, description="List of observed settlements")


class GroundTruthEntry(FinancialBaseModel):
    """Benchmark evaluation entry for an individual transaction."""
    order_id: str = Field(..., description="Order identifier matching operational payment")
    ground_truth_category: str = Field(..., description="One of the 8 canonical evaluation categories")
    expected_status: str = Field(..., description="Target reconciliation status (MATCHED / EXCEPTION)")
    expected_rule: str = Field(..., description="Target deterministic rule identifier")


class GroundTruthDataset(FinancialBaseModel):
    """Isolated ground-truth benchmark dataset."""
    batch_id: str = Field(..., description="Associated batch identifier")
    total_records: int = Field(..., description="Total count of ground-truth entries")
    categories_count: Dict[str, int] = Field(default_factory=dict, description="Distribution across 8 categories")
    records: List[GroundTruthEntry] = Field(default_factory=list, description="Individual ground-truth entries")
