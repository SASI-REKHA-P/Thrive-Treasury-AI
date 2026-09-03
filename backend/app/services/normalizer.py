from decimal import Decimal
from typing import List
from pydantic import ValidationError
from app.models.transaction import PaymentRecord, SettlementRecord, SyntheticBatch
from app.models.normalized import NormalizedPayment, NormalizedSettlement, NormalizedBatch


class NormalizationError(Exception):
    """Raised when record normalization or structural validation fails."""
    pass


class Normalizer:
    """
    Deterministic normalization service converting raw transaction records into 
    canonical internal models without altering financial values or performing matching logic.
    """

    @classmethod
    def normalize_payment(cls, record: PaymentRecord) -> NormalizedPayment:
        """
        Normalize a single payment record into its canonical internal representation.
        
        Rules:
        - Timestamp must be timezone-aware (rejects naive datetimes).
        - Currency code normalized to uppercase.
        - Trims leading/trailing whitespace from string identifiers.
        - Preserves exact Decimal amount without binary float conversion or rounding.
        - Retains source order_id and auth_ref for auditability.
        """
        if record.booking_timestamp.tzinfo is None:
            raise NormalizationError(
                f"Payment record '{record.order_id}' has naive booking_timestamp. "
                "All timestamps must be timezone-aware."
            )

        try:
            return NormalizedPayment(
                order_id=record.order_id.strip(),
                auth_ref=record.auth_ref.strip(),
                gross_amount=Decimal(str(record.gross_amount)),
                currency=record.currency.strip().upper(),
                payment_method=record.payment_method.strip(),
                booking_timestamp=record.booking_timestamp,
            )
        except (ValueError, ValidationError) as exc:
            raise NormalizationError(
                f"Failed to normalize payment record '{record.order_id}': {exc}"
            ) from exc

    @classmethod
    def normalize_settlement(cls, record: SettlementRecord) -> NormalizedSettlement:
        """
        Normalize a single settlement record into its canonical internal representation.
        
        Rules:
        - Timestamp must be timezone-aware (rejects naive datetimes).
        - Currency code normalized to uppercase.
        - Trims leading/trailing whitespace from string identifiers.
        - Preserves exact Decimal amount without binary float conversion or rounding.
        - Retains source settlement_id, order_ref, and auth_ref for auditability.
        """
        if record.clearing_timestamp.tzinfo is None:
            raise NormalizationError(
                f"Settlement record '{record.settlement_id}' has naive clearing_timestamp. "
                "All timestamps must be timezone-aware."
            )

        try:
            return NormalizedSettlement(
                settlement_id=record.settlement_id.strip(),
                order_ref=record.order_ref.strip(),
                auth_ref=record.auth_ref.strip(),
                net_deposit=Decimal(str(record.net_deposit)),
                settlement_currency=record.settlement_currency.strip().upper(),
                clearing_timestamp=record.clearing_timestamp,
                bank_account_ref=record.bank_account_ref.strip(),
            )
        except (ValueError, ValidationError) as exc:
            raise NormalizationError(
                f"Failed to normalize settlement record '{record.settlement_id}': {exc}"
            ) from exc

    @classmethod
    def normalize_batch(cls, batch: SyntheticBatch) -> NormalizedBatch:
        """
        Normalize an entire operational batch deterministically.
        
        Preserves all 120 payments and 117 settlements without dropping, filtering,
        or matching any records.
        """
        if batch.generated_at.tzinfo is None:
            raise NormalizationError("Batch generated_at timestamp must be timezone-aware.")

        normalized_payments: List[NormalizedPayment] = [
            cls.normalize_payment(payment) for payment in batch.payments
        ]

        normalized_settlements: List[NormalizedSettlement] = [
            cls.normalize_settlement(settlement) for settlement in batch.settlements
        ]

        return NormalizedBatch(
            batch_id=batch.batch_id.strip(),
            generated_at=batch.generated_at,
            description=batch.description.strip(),
            payments=normalized_payments,
            settlements=normalized_settlements,
        )
