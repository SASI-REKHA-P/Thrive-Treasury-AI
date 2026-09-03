from datetime import datetime, timezone
from decimal import Decimal
import re
from typing import Dict, List, Optional
import uuid

from app.core.config import settings
from app.models.normalized import NormalizedBatch, NormalizedPayment, NormalizedSettlement
from app.models.reconciliation import (
    ReconciliationResult,
    ReconciliationRule,
    ReconciliationStatus,
)
from app.models.ai_investigation import (
    AIClassification,
    AIRecommendedAction,
    AIConfidenceTier,
    AIInvestigationInput,
    LLMInvestigationPayload,
    AIInvestigationOutput,
)
from app.services.ai_provider import (
    BaseAIProvider,
    MockAIProvider,
    GeminiAIProvider,
    AIProviderError,
)


class AIInvestigatorService:
    """
    Service responsible for contextual AI exception investigation.
    
    Enforces selective routing, programmatic confidence tiers, strict human-in-the-loop
    governance, evidence validation, and safe error fallback. AI outcomes are strictly advisory
    and NEVER mutate deterministic reconciliation rules or statuses.
    """

    AI_ELIGIBLE_RULES = {
        ReconciliationRule.RULE_08_AMOUNT_MISMATCH.value,
        ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK.value,
    }

    def __init__(self, provider: Optional[BaseAIProvider] = None):
        if provider is not None:
            self.provider = provider
        elif settings.ai_provider.lower() == "gemini":
            self.provider = GeminiAIProvider()
        else:
            self.provider = MockAIProvider()

    @classmethod
    def is_ai_eligible(cls, result: ReconciliationResult) -> bool:
        """Determine whether a deterministic reconciliation result is eligible for AI investigation."""
        return result.rule_id.value in cls.AI_ELIGIBLE_RULES

    @classmethod
    def derive_confidence_tier(cls, confidence: Decimal) -> AIConfidenceTier:
        """
        Programmatically derive confidence tier from numeric confidence.
        
        HIGH:   confidence >= 0.85
        MEDIUM: 0.60 <= confidence < 0.85
        LOW:    confidence < 0.60
        """
        if confidence < Decimal("0.00") or confidence > Decimal("1.00"):
            raise ValueError(f"Confidence score {confidence} is out of valid range [0.00, 1.00]")
        if confidence >= Decimal("0.85"):
            return AIConfidenceTier.HIGH
        elif confidence >= Decimal("0.60"):
            return AIConfidenceTier.MEDIUM
        else:
            return AIConfidenceTier.LOW

    @classmethod
    def determine_human_review_required(
        cls, rule_id: str, confidence: Decimal, variance: Optional[Decimal]
    ) -> bool:
        """
        Enforce programmatic human review policy.
        
        - RULE_04_CROSS_CURRENCY_CHECK: ALWAYS requires human review (no confidence can bypass).
        - RULE_08_AMOUNT_MISMATCH: Requires human review if confidence < 0.85 OR discrepancy > ₹500.00.
        """
        if rule_id == ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK.value:
            return True

        if rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH.value:
            if confidence < Decimal("0.85"):
                return True
            if variance is not None and abs(variance) > Decimal("500.00"):
                return True
            return False

        return True

    @classmethod
    def validate_evidence(
        cls, evidence_used: List[str], input_data: AIInvestigationInput
    ) -> bool:
        """
        Validate that evidence citations do not reference foreign/unknown identifiers.
        Returns True if valid, False if unknown IDs or ground-truth keywords are detected.
        """
        forbidden_terms = ["ground_truth", "expected_status", "expected_rule"]
        order_id_pattern = re.compile(r"ORD-[A-Za-z0-9\-]+")
        settlement_id_pattern = re.compile(r"SET-[A-Za-z0-9\-]+")

        for item in evidence_used:
            # Check forbidden leakages
            for term in forbidden_terms:
                if term in item.lower():
                    return False

            # Check order ID citations
            for found_ord in order_id_pattern.findall(item):
                if found_ord != input_data.order_id:
                    return False

            # Check settlement ID citations
            if input_data.settlement_id:
                for found_set in settlement_id_pattern.findall(item):
                    if found_set != input_data.settlement_id:
                        return False

        return True

    @classmethod
    def build_investigation_input(
        cls,
        result: ReconciliationResult,
        payment: NormalizedPayment,
        settlement: Optional[NormalizedSettlement] = None,
    ) -> AIInvestigationInput:
        """Construct sanitized operational input payload with zero ground-truth data."""
        # Calculate standard 2% MDR + 18% GST fee if single currency
        standard_expected_fee: Optional[Decimal] = None
        effective_implied_rate: Optional[Decimal] = None

        if settlement and payment.currency == settlement.settlement_currency:
            mdr = (payment.gross_amount * Decimal("0.02")).quantize(Decimal("0.01"))
            gst = (mdr * Decimal("0.18")).quantize(Decimal("0.01"))
            standard_expected_fee = mdr + gst

        # Calculate implied rate for cross-currency Nostro clearing
        if (
            settlement
            and payment.currency != settlement.settlement_currency
            and payment.gross_amount > Decimal("0.00")
        ):
            effective_implied_rate = (settlement.net_deposit / payment.gross_amount).quantize(
                Decimal("0.01")
            )

        return AIInvestigationInput(
            order_id=payment.order_id,
            auth_ref=payment.auth_ref,
            gross_amount=payment.gross_amount,
            currency=payment.currency,
            payment_method=payment.payment_method,
            booking_timestamp=payment.booking_timestamp,
            settlement_id=settlement.settlement_id if settlement else None,
            net_deposit=settlement.net_deposit if settlement else None,
            settlement_currency=settlement.settlement_currency if settlement else None,
            clearing_timestamp=settlement.clearing_timestamp if settlement else None,
            bank_account_ref=settlement.bank_account_ref if settlement else None,
            rule_id=result.rule_id.value,
            deterministic_status=result.status.value,
            variance_amount=result.difference,
            deterministic_explanation=result.reason,
            standard_expected_fee=standard_expected_fee,
            effective_implied_rate=effective_implied_rate,
        )

    def _create_fallback_output(
        self, order_id: str, reason: str = "AI investigation unavailable or invalid; routed safely to Human Review Queue."
    ) -> AIInvestigationOutput:
        """Generate safe fallback investigation report conforming to Section 11."""
        return AIInvestigationOutput(
            investigation_id=str(uuid.uuid4()),
            order_id=order_id,
            investigated_at=datetime.now(timezone.utc),
            classification=AIClassification.INCONCLUSIVE_VARIANCE,
            confidence=Decimal("0.00"),
            confidence_tier=AIConfidenceTier.LOW,
            root_cause_analysis=reason,
            recommended_action=AIRecommendedAction.MANUAL_CONTROLLER_AUDIT,
            human_review_required=True,
            evidence_used=[],
        )

    def investigate_transaction(
        self,
        result: ReconciliationResult,
        payment: NormalizedPayment,
        settlement: Optional[NormalizedSettlement] = None,
    ) -> AIInvestigationOutput:
        """
        Execute AI investigation for a single eligible transaction.
        Raises ValueError if transaction is not AI-eligible.
        Fails safely on provider or validation errors.
        """
        if not self.is_ai_eligible(result):
            raise ValueError(
                f"Transaction '{result.order_id}' with rule '{result.rule_id.value}' is not AI-eligible. "
                "Only RULE_08_AMOUNT_MISMATCH and RULE_04_CROSS_CURRENCY_CHECK may be investigated."
            )

        input_data = self.build_investigation_input(result, payment, settlement)

        # Execute provider call with safe fallback
        try:
            payload = self.provider.investigate(input_data)
        except Exception:
            return self._create_fallback_output(input_data.order_id)

        # Validate confidence range
        if payload.confidence < Decimal("0.00") or payload.confidence > Decimal("1.00"):
            return self._create_fallback_output(
                input_data.order_id, reason="Provider returned confidence outside valid range [0.00, 1.00]."
            )

        # Programmatically enforce confidence tier
        derived_tier = self.derive_confidence_tier(payload.confidence)

        # Programmatically enforce human-review policy
        human_review = self.determine_human_review_required(
            result.rule_id.value, payload.confidence, result.difference
        )

        # Validate evidence citations
        if not self.validate_evidence(payload.evidence_used, input_data):
            return self._create_fallback_output(
                input_data.order_id, reason="Provider returned invalid evidence citations."
            )

        return AIInvestigationOutput(
            investigation_id=str(uuid.uuid4()),
            order_id=input_data.order_id,
            investigated_at=datetime.now(timezone.utc),
            classification=payload.classification,
            confidence=payload.confidence,
            confidence_tier=derived_tier,
            root_cause_analysis=payload.root_cause_analysis,
            recommended_action=payload.recommended_action,
            human_review_required=human_review,
            evidence_used=payload.evidence_used,
        )

    def investigate_batch(
        self,
        results: List[ReconciliationResult],
        batch: NormalizedBatch,
    ) -> List[ReconciliationResult]:
        """
        Investigate all AI-eligible transactions in a reconciled batch.
        
        Updates:
          - ai_investigation (attached report)
          - ai_status ("INVESTIGATED" or "NOT_REQUIRED")
          - requires_human_review (set to True if required by investigation policy)
          - human_review_status (set to "REVIEW_REQUIRED" if human review is needed)
          
        Guarantees:
          - status is NEVER modified (EXCEPTION remains EXCEPTION; PENDING_REVIEW remains PENDING_REVIEW)
          - rule_id is NEVER modified
        """
        # Index batch by order_id
        payment_map: Dict[str, NormalizedPayment] = {p.order_id: p for p in batch.payments}
        settlement_map: Dict[str, NormalizedSettlement] = {
            s.order_ref: s for s in batch.settlements if s.order_ref
        }

        updated_results: List[ReconciliationResult] = []

        for r in results:
            # Shallow clone or update in place
            payment = payment_map.get(r.order_id)
            settlement = settlement_map.get(r.order_id)

            if payment and self.is_ai_eligible(r):
                investigation = self.investigate_transaction(r, payment, settlement)
                r.ai_investigation = investigation
                r.ai_status = "INVESTIGATED"

                # Update human review flags according to policy
                if investigation.human_review_required:
                    r.requires_human_review = True
                    r.human_review_status = "REVIEW_REQUIRED"
            else:
                r.ai_status = "NOT_REQUIRED"
                r.ai_investigation = None

            updated_results.append(r)

        return updated_results
