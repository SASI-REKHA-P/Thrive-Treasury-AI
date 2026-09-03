from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime

from app.core.config import settings
from app.models.normalized import NormalizedBatch, NormalizedPayment, NormalizedSettlement
from app.models.reconciliation import (
    ReconciliationResult,
    ReconciliationChecks,
    ReconciliationRule,
    ReconciliationStatus,
)


class DeterministicReconciliationEngine:
    """
    Deterministic Financial Reconciliation Engine.
    
    Executes a strict 10-step auditable decision hierarchy over normalized transaction feeds.
    Uses indexed lookup (O(N + M)) and 100% Decimal financial precision.
    Produces deterministic, explainable outcomes with zero AI involvement.
    """

    def __init__(
        self,
        standard_clearing_window_hours: Optional[float] = None,
        max_date_tolerance_hours: Optional[float] = None,
        mdr_rate: Optional[Decimal] = None,
        gst_rate: Optional[Decimal] = None,
        nostro_clearing_account: Optional[str] = None,
        base_operating_currency: Optional[str] = None,
    ):
        self.standard_clearing_window_hours = (
            standard_clearing_window_hours or settings.standard_clearing_window_hours
        )
        self.max_date_tolerance_hours = (
            max_date_tolerance_hours or settings.max_date_tolerance_hours
        )
        self.mdr_rate = mdr_rate or settings.default_mdr_rate
        self.gst_rate = gst_rate or settings.default_gst_rate
        self.nostro_clearing_account = (
            nostro_clearing_account or settings.nostro_clearing_account
        )
        self.base_operating_currency = (
            base_operating_currency or settings.base_operating_currency
        )

    def calculate_expected_fee(self, gross_amount: Decimal) -> Decimal:
        """
        Calculate expected fee using standard merchant schedule:
        MDR = 2.0% of gross
        GST = 18.0% of MDR
        Total = MDR + GST (quantized to 2 decimal places)
        """
        mdr = (gross_amount * self.mdr_rate).quantize(Decimal("0.01"))
        gst = (mdr * self.gst_rate).quantize(Decimal("0.01"))
        return mdr + gst

    def reconcile_payment(
        self,
        payment: NormalizedPayment,
        matching_settlements: List[NormalizedSettlement],
    ) -> ReconciliationResult:
        """
        Evaluate a single payment against associated settlements following the 10-step hierarchy.
        """
        # STEP 2: DUPLICATE CHECK
        # If multiple settlements correspond to the same order reference, flag as duplicate exception
        if len(matching_settlements) > 1:
            settlement_ids = [s.settlement_id for s in matching_settlements]
            first_settlement = matching_settlements[0]
            return ReconciliationResult(
                order_id=payment.order_id,
                status=ReconciliationStatus.EXCEPTION,
                rule_id=ReconciliationRule.RULE_06_DUPLICATE_CHECK,
                match_method=ReconciliationRule.RULE_06_DUPLICATE_CHECK.value,
                payment_amount=payment.gross_amount,
                payment_currency=payment.currency,
                settlement_amount=first_settlement.net_deposit,
                settlement_currency=first_settlement.settlement_currency,
                difference=payment.gross_amount - first_settlement.net_deposit,
                settlement_ids=settlement_ids,
                checks=ReconciliationChecks(
                    reference_match=True,
                    currency_match=(payment.currency == first_settlement.settlement_currency),
                    amount_match=False,
                    date_tolerance=False,
                    duplicate_check=True,
                    settlement_present=True,
                ),
                requires_ai=False,
                requires_human_review=True,
                reason="Multiple settlement records were found for the same payment reference.",
                human_review_status="REVIEW_REQUIRED",
            )

        # STEP 4: MISSING SETTLEMENT
        # If no settlement exists for the payment, flag as missing settlement exception
        if len(matching_settlements) == 0:
            return ReconciliationResult(
                order_id=payment.order_id,
                status=ReconciliationStatus.EXCEPTION,
                rule_id=ReconciliationRule.RULE_05_MISSING_SETTLEMENT,
                match_method=ReconciliationRule.RULE_05_MISSING_SETTLEMENT.value,
                payment_amount=payment.gross_amount,
                payment_currency=payment.currency,
                settlement_amount=None,
                settlement_currency=None,
                difference=payment.gross_amount,
                settlement_ids=[],
                checks=ReconciliationChecks(
                    reference_match=False,
                    currency_match=False,
                    amount_match=False,
                    date_tolerance=False,
                    duplicate_check=False,
                    settlement_present=False,
                ),
                requires_ai=False,
                requires_human_review=True,
                reason="No settlement record was found for the payment.",
                human_review_status="REVIEW_REQUIRED",
            )

        # Exactly one settlement record is paired
        settlement = matching_settlements[0]
        ref_match = (
            settlement.order_ref == payment.order_id
            and settlement.auth_ref == payment.auth_ref
        )
        settlement_ids = [settlement.settlement_id]

        # STEP 5: CURRENCY CHECK
        # Distinguish cross-currency ambiguity from general currency mismatch
        if payment.currency != settlement.settlement_currency:
            # 5A: Cross-Currency Ambiguity
            # Inbound foreign currency (USD, EUR, GBP) clearing via designated Nostro account into base currency (INR)
            is_nostro_fx = (
                settlement.settlement_currency == self.base_operating_currency
                and settlement.bank_account_ref == self.nostro_clearing_account
            )
            if is_nostro_fx:
                return ReconciliationResult(
                    order_id=payment.order_id,
                    status=ReconciliationStatus.PENDING_REVIEW,
                    rule_id=ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK,
                    match_method=ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK.value,
                    payment_amount=payment.gross_amount,
                    payment_currency=payment.currency,
                    settlement_amount=settlement.net_deposit,
                    settlement_currency=settlement.settlement_currency,
                    difference=None,  # No raw subtraction across disparate currencies
                    settlement_ids=settlement_ids,
                    checks=ReconciliationChecks(
                        reference_match=ref_match,
                        currency_match=False,
                        amount_match=False,
                        date_tolerance=False,
                        duplicate_check=False,
                        settlement_present=True,
                    ),
                    requires_ai=False,
                    requires_human_review=True,
                    reason="Payment and settlement currencies differ; FX conversion is unavailable, so the transaction requires review.",
                    human_review_status="REVIEW_REQUIRED",
                )
            else:
                # 5B: Currency Mismatch on standard clearing channel
                return ReconciliationResult(
                    order_id=payment.order_id,
                    status=ReconciliationStatus.EXCEPTION,
                    rule_id=ReconciliationRule.RULE_07_CURRENCY_MISMATCH,
                    match_method=ReconciliationRule.RULE_07_CURRENCY_MISMATCH.value,
                    payment_amount=payment.gross_amount,
                    payment_currency=payment.currency,
                    settlement_amount=settlement.net_deposit,
                    settlement_currency=settlement.settlement_currency,
                    difference=None,
                    settlement_ids=settlement_ids,
                    checks=ReconciliationChecks(
                        reference_match=ref_match,
                        currency_match=False,
                        amount_match=False,
                        date_tolerance=False,
                        duplicate_check=False,
                        settlement_present=True,
                    ),
                    requires_ai=False,
                    requires_human_review=True,
                    reason="Settlement currency does not match payment currency on standard clearing channel.",
                    human_review_status="REVIEW_REQUIRED",
                )

        # Currencies match identically
        currency_match = True
        difference = payment.gross_amount - settlement.net_deposit
        time_delta_seconds = (
            settlement.clearing_timestamp - payment.booking_timestamp
        ).total_seconds()
        delta_hours = max(0.0, time_delta_seconds / 3600.0)

        # STEP 6 & 7: EXACT AMOUNT MATCH & DATE TOLERANCE
        if payment.gross_amount == settlement.net_deposit:
            # Check if clearing delay exceeds standard same-day window but is within date tolerance
            if (
                delta_hours > self.standard_clearing_window_hours
                and delta_hours <= self.max_date_tolerance_hours
            ):
                return ReconciliationResult(
                    order_id=payment.order_id,
                    status=ReconciliationStatus.MATCHED,
                    rule_id=ReconciliationRule.RULE_03_DATE_TOLERANCE,
                    match_method=ReconciliationRule.RULE_03_DATE_TOLERANCE.value,
                    payment_amount=payment.gross_amount,
                    payment_currency=payment.currency,
                    settlement_amount=settlement.net_deposit,
                    settlement_currency=settlement.settlement_currency,
                    difference=Decimal("0.00"),
                    settlement_ids=settlement_ids,
                    checks=ReconciliationChecks(
                        reference_match=ref_match,
                        currency_match=currency_match,
                        amount_match=True,
                        date_tolerance=True,
                        duplicate_check=False,
                        settlement_present=True,
                    ),
                    requires_ai=False,
                    requires_human_review=False,
                    reason="Settlement amount matches and clearing occurred within the configured date tolerance.",
                )
            else:
                # Standard same-day or intraday exact match
                return ReconciliationResult(
                    order_id=payment.order_id,
                    status=ReconciliationStatus.MATCHED,
                    rule_id=ReconciliationRule.RULE_01_EXACT_MATCH,
                    match_method=ReconciliationRule.RULE_01_EXACT_MATCH.value,
                    payment_amount=payment.gross_amount,
                    payment_currency=payment.currency,
                    settlement_amount=settlement.net_deposit,
                    settlement_currency=settlement.settlement_currency,
                    difference=Decimal("0.00"),
                    settlement_ids=settlement_ids,
                    checks=ReconciliationChecks(
                        reference_match=ref_match,
                        currency_match=currency_match,
                        amount_match=True,
                        date_tolerance=True,
                        duplicate_check=False,
                        settlement_present=True,
                    ),
                    requires_ai=False,
                    requires_human_review=False,
                    reason="Settlement amount exactly matches the payment amount.",
                )

        # STEP 8: EXPECTED FEE MATCH
        expected_fee = self.calculate_expected_fee(payment.gross_amount)
        expected_net = payment.gross_amount - expected_fee

        if settlement.net_deposit == expected_net:
            return ReconciliationResult(
                order_id=payment.order_id,
                status=ReconciliationStatus.MATCHED,
                rule_id=ReconciliationRule.RULE_02_EXPECTED_FEE,
                match_method=ReconciliationRule.RULE_02_EXPECTED_FEE.value,
                payment_amount=payment.gross_amount,
                payment_currency=payment.currency,
                settlement_amount=settlement.net_deposit,
                settlement_currency=settlement.settlement_currency,
                difference=difference,
                settlement_ids=settlement_ids,
                checks=ReconciliationChecks(
                    reference_match=ref_match,
                    currency_match=currency_match,
                    amount_match=False,
                    date_tolerance=True,
                    duplicate_check=False,
                    settlement_present=True,
                ),
                requires_ai=False,
                requires_human_review=False,
                reason="Settlement matches the expected net amount after 2% MDR and 18% GST on MDR.",
            )

        # STEP 9: AMOUNT MISMATCH
        # Discrepancy is neither exact nor expected fee adjusted
        return ReconciliationResult(
            order_id=payment.order_id,
            status=ReconciliationStatus.EXCEPTION,
            rule_id=ReconciliationRule.RULE_08_AMOUNT_MISMATCH,
            match_method=ReconciliationRule.RULE_08_AMOUNT_MISMATCH.value,
            payment_amount=payment.gross_amount,
            payment_currency=payment.currency,
            settlement_amount=settlement.net_deposit,
            settlement_currency=settlement.settlement_currency,
            difference=difference,
            settlement_ids=settlement_ids,
            checks=ReconciliationChecks(
                reference_match=ref_match,
                currency_match=currency_match,
                amount_match=False,
                date_tolerance=True,
                duplicate_check=False,
                settlement_present=True,
            ),
            requires_ai=True,
            requires_human_review=False,
            reason="Settlement amount does not match the payment amount or expected fee-adjusted amount.",
            ai_status="PENDING",
        )

    def reconcile_batch(self, batch: NormalizedBatch) -> List[ReconciliationResult]:
        """
        Reconcile an entire normalized batch using indexed lookups (O(N + M)).
        
        Guarantees that every payment produces exactly one ReconciliationResult.
        """
        # Step 3: Index settlements by order_ref for O(1) lookup
        settlements_index: Dict[str, List[NormalizedSettlement]] = {}
        for settlement in batch.settlements:
            settlements_index.setdefault(settlement.order_ref, []).append(settlement)

        results: List[ReconciliationResult] = []
        for payment in batch.payments:
            matching_settlements = settlements_index.get(payment.order_id, [])
            result = self.reconcile_payment(payment, matching_settlements)
            results.append(result)

        return results
