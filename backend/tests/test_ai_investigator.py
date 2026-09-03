from decimal import Decimal
import copy
import pytest

from app.models.normalized import NormalizedPayment, NormalizedSettlement
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
from app.services.data_loader import DataLoader
from app.services.normalizer import Normalizer
from app.services.engine import DeterministicReconciliationEngine
from app.services.ai_provider import BaseAIProvider, MockAIProvider, AIProviderError
from app.services.ai_investigator import AIInvestigatorService


@pytest.fixture
def batch_and_reconciliation():
    """Load, normalize, and reconcile the full synthetic batch."""
    loader = DataLoader()
    raw_batch = loader.load_synthetic_batch()
    norm_batch = Normalizer.normalize_batch(raw_batch)
    engine = DeterministicReconciliationEngine()
    results = engine.reconcile_batch(norm_batch)
    return norm_batch, results


# A & B: Eligibility and Routing Counts
def test_ai_eligibility_by_rule():
    """Verify that only RULE_08 and RULE_04 are AI-eligible, all others are not."""
    service = AIInvestigatorService()

    eligible_rules = [
        ReconciliationRule.RULE_08_AMOUNT_MISMATCH,
        ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK,
    ]
    non_eligible_rules = [
        ReconciliationRule.RULE_01_EXACT_MATCH,
        ReconciliationRule.RULE_02_EXPECTED_FEE,
        ReconciliationRule.RULE_03_DATE_TOLERANCE,
        ReconciliationRule.RULE_05_MISSING_SETTLEMENT,
        ReconciliationRule.RULE_06_DUPLICATE_CHECK,
        ReconciliationRule.RULE_07_CURRENCY_MISMATCH,
    ]

    for rule in eligible_rules:
        dummy = ReconciliationResult(
            order_id="ORD-TEST",
            status=ReconciliationStatus.EXCEPTION,
            rule_id=rule,
            match_method="Test",
            payment_amount=Decimal("100.00"),
            payment_currency="INR",
            reason="Test reason",
        )
        assert service.is_ai_eligible(dummy) is True

    for rule in non_eligible_rules:
        dummy = ReconciliationResult(
            order_id="ORD-TEST",
            status=ReconciliationStatus.MATCHED,
            rule_id=rule,
            match_method="Test",
            payment_amount=Decimal("100.00"),
            payment_currency="INR",
            reason="Test reason",
        )
        assert service.is_ai_eligible(dummy) is False


def test_batch_routing_counts(batch_and_reconciliation):
    """Verify that out of 120 batch records, exactly 13 are AI-eligible and 107 are not."""
    norm_batch, results = batch_and_reconciliation
    service = AIInvestigatorService()

    eligible_results = [r for r in results if service.is_ai_eligible(r)]
    non_eligible_results = [r for r in results if not service.is_ai_eligible(r)]

    assert len(results) == 120
    assert len(eligible_results) == 13
    assert len(non_eligible_results) == 107

    rule_08_count = sum(1 for r in eligible_results if r.rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH)
    rule_04_count = sum(1 for r in eligible_results if r.rule_id == ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK)

    assert rule_08_count == 8
    assert rule_04_count == 5


def test_non_eligible_rule_rejection_on_direct_call(batch_and_reconciliation):
    """Verify direct investigation call on a non-eligible rule raises ValueError."""
    norm_batch, results = batch_and_reconciliation
    service = AIInvestigatorService()

    exact_match = next(r for r in results if r.rule_id == ReconciliationRule.RULE_01_EXACT_MATCH)
    payment = next(p for p in norm_batch.payments if p.order_id == exact_match.order_id)

    with pytest.raises(ValueError) as exc_info:
        service.investigate_transaction(exact_match, payment, None)
    assert "is not AI-eligible" in str(exc_info.value)


# C & O: RULE_08 Amount Mismatch Behavior
def test_rule_08_investigation_and_status_immutability(batch_and_reconciliation):
    """Verify RULE_08 receives advisory AI report and deterministic EXCEPTION status is preserved."""
    norm_batch, results = batch_and_reconciliation
    service = AIInvestigatorService()

    r08_results = [r for r in results if r.rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH]
    assert len(r08_results) == 8

    updated_results = service.investigate_batch(results, norm_batch)
    investigated_r08 = [r for r in updated_results if r.rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH]

    for r in investigated_r08:
        # Deterministic status and rule are completely unchanged
        assert r.status == ReconciliationStatus.EXCEPTION
        assert r.rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH

        # AI investigation is attached and lifecycle marked INVESTIGATED
        assert r.ai_status == "INVESTIGATED"
        assert r.ai_investigation is not None
        assert isinstance(r.ai_investigation, AIInvestigationOutput)
        assert r.ai_investigation.order_id == r.order_id
        assert r.ai_investigation.classification in [
            AIClassification.NON_STANDARD_INTERCHANGE_FEE,
            AIClassification.UNEXPLAINED_GATEWAY_SHORTFALL,
            AIClassification.INCONCLUSIVE_VARIANCE,
        ]


# D, E & N: RULE_04 Cross-Currency Behavior & Mandatory Human Review
def test_rule_04_cross_currency_briefing_and_mandatory_human_review(batch_and_reconciliation):
    """
    Test Section 16:
    Input: RULE_04_CROSS_CURRENCY_CHECK
    Output: classification == CROSS_BORDER_FX_EXPOSURE
    Regardless of confidence: human_review_required == True
    ReconciliationResult.status remains PENDING_REVIEW
    ReconciliationResult.rule_id remains RULE_04_CROSS_CURRENCY_CHECK
    """
    norm_batch, results = batch_and_reconciliation
    service = AIInvestigatorService()

    updated_results = service.investigate_batch(results, norm_batch)
    r04_results = [r for r in updated_results if r.rule_id == ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK]

    assert len(r04_results) == 5

    for r in r04_results:
        # Strict human-in-the-loop and status immutability
        assert r.status == ReconciliationStatus.PENDING_REVIEW
        assert r.rule_id == ReconciliationRule.RULE_04_CROSS_CURRENCY_CHECK
        assert r.ai_status == "INVESTIGATED"
        assert r.requires_human_review is True
        assert r.human_review_status == "REVIEW_REQUIRED"

        inv = r.ai_investigation
        assert inv is not None
        assert inv.classification == AIClassification.CROSS_BORDER_FX_EXPOSURE
        assert inv.recommended_action == AIRecommendedAction.ESCALATE_TO_TREASURY_FX_DESK
        assert inv.human_review_required is True

    # Anchor case ORD-8494: USD 500 -> INR 41,200, implied rate = 82.40
    ord_8494 = next(r for r in r04_results if r.order_id == "ORD-8494")
    assert "82.4" in ord_8494.ai_investigation.root_cause_analysis


# F: RULE_08 Confidence and Discrepancy Human Review Logic
def test_rule_08_human_review_threshold_policy():
    """Verify human review policy for RULE_08."""
    # confidence < 0.85 -> human review required
    assert AIInvestigatorService.determine_human_review_required(
        rule_id="RULE_08_AMOUNT_MISMATCH",
        confidence=Decimal("0.80"),
        variance=Decimal("200.00"),
    ) is True

    # discrepancy > 500 -> human review required
    assert AIInvestigatorService.determine_human_review_required(
        rule_id="RULE_08_AMOUNT_MISMATCH",
        confidence=Decimal("0.90"),
        variance=Decimal("600.00"),
    ) is True

    # confidence >= 0.85 AND discrepancy <= 500 -> human review not required
    assert AIInvestigatorService.determine_human_review_required(
        rule_id="RULE_08_AMOUNT_MISMATCH",
        confidence=Decimal("0.85"),
        variance=Decimal("300.00"),
    ) is False

    # RULE_04 always requires human review regardless of values
    assert AIInvestigatorService.determine_human_review_required(
        rule_id="RULE_04_CROSS_CURRENCY_CHECK",
        confidence=Decimal("0.99"),
        variance=Decimal("10.00"),
    ) is True


# G: Confidence Tier Boundaries
def test_confidence_tier_boundaries():
    """
    Test Section 14.G:
    - 0.85 -> HIGH
    - 0.8499 -> MEDIUM
    - 0.60 -> MEDIUM
    - 0.5999 -> LOW
    """
    assert AIInvestigatorService.derive_confidence_tier(Decimal("0.85")) == AIConfidenceTier.HIGH
    assert AIInvestigatorService.derive_confidence_tier(Decimal("1.00")) == AIConfidenceTier.HIGH
    assert AIInvestigatorService.derive_confidence_tier(Decimal("0.8499")) == AIConfidenceTier.MEDIUM
    assert AIInvestigatorService.derive_confidence_tier(Decimal("0.60")) == AIConfidenceTier.MEDIUM
    assert AIInvestigatorService.derive_confidence_tier(Decimal("0.5999")) == AIConfidenceTier.LOW
    assert AIInvestigatorService.derive_confidence_tier(Decimal("0.00")) == AIConfidenceTier.LOW


# H: Confidence Validation
def test_confidence_validation_rejects_out_of_range():
    """Verify confidence values outside [0.00, 1.00] raise ValueError."""
    with pytest.raises(ValueError):
        AIInvestigatorService.derive_confidence_tier(Decimal("-0.01"))

    with pytest.raises(ValueError):
        AIInvestigatorService.derive_confidence_tier(Decimal("1.01"))

    with pytest.raises(ValueError):
        LLMInvestigationPayload(
            classification=AIClassification.INCONCLUSIVE_VARIANCE,
            confidence=Decimal("-0.50"),
            confidence_tier=AIConfidenceTier.LOW,
            root_cause_analysis="Test",
            recommended_action=AIRecommendedAction.MANUAL_CONTROLLER_AUDIT,
            human_review_required=True,
            evidence_used=[],
        )


# I: Evidence Validation
def test_evidence_validation_rejects_foreign_identifiers():
    """Verify validate_evidence rejects citations of foreign order/settlement IDs."""
    dummy_input = AIInvestigationInput(
        order_id="ORD-1001",
        auth_ref="AUTH-1001",
        gross_amount=Decimal("1000.00"),
        currency="INR",
        payment_method="UPI",
        booking_timestamp="2026-03-01T10:00:00Z",
        settlement_id="SET-1001",
        rule_id="RULE_08_AMOUNT_MISMATCH",
        deterministic_status="EXCEPTION",
        deterministic_explanation="Amount mismatch",
    )

    valid_evidence = ["Order: ORD-1001", "Settlement: SET-1001", "Gross: 1000.00"]
    assert AIInvestigatorService.validate_evidence(valid_evidence, dummy_input) is True

    # Foreign order ID
    invalid_order = ["Order: ORD-9999", "Settlement: SET-1001"]
    assert AIInvestigatorService.validate_evidence(invalid_order, dummy_input) is False

    # Foreign settlement ID
    invalid_settlement = ["Order: ORD-1001", "Settlement: SET-9999"]
    assert AIInvestigatorService.validate_evidence(invalid_settlement, dummy_input) is False

    # Ground truth leakage attempt
    leaked_evidence = ["Order: ORD-1001", "ground_truth_category: AMOUNT_MISMATCH"]
    assert AIInvestigatorService.validate_evidence(leaked_evidence, dummy_input) is False


# J: Ground Truth Isolation
def test_ground_truth_isolation(batch_and_reconciliation):
    """Verify that AIInvestigationInput contains zero ground truth fields or labels."""
    norm_batch, results = batch_and_reconciliation
    service = AIInvestigatorService()

    r08 = next(r for r in results if r.rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH)
    payment = next(p for p in norm_batch.payments if p.order_id == r08.order_id)
    settlement = next(s for s in norm_batch.settlements if s.order_ref == r08.order_id)

    input_data = service.build_investigation_input(r08, payment, settlement)
    input_dict = input_data.model_dump()

    # Assert ground-truth benchmark fields are completely absent
    assert "expected_rule" not in input_dict
    assert "expected_status" not in input_dict
    assert "ground_truth_category" not in input_dict
    assert "confusion_matrix" not in input_dict
    assert "accuracy" not in input_dict


# K & L: Safe Fallback on Provider Failures
class FailingProvider(BaseAIProvider):
    def investigate(self, input_data: AIInvestigationInput) -> LLMInvestigationPayload:
        raise AIProviderError("Simulated provider connection timeout or rate limit.")


class BadEvidenceProvider(BaseAIProvider):
    def investigate(self, input_data: AIInvestigationInput) -> LLMInvestigationPayload:
        return LLMInvestigationPayload(
            classification=AIClassification.NON_STANDARD_INTERCHANGE_FEE,
            confidence=Decimal("0.85"),
            confidence_tier=AIConfidenceTier.HIGH,
            root_cause_analysis="Bad citation",
            recommended_action=AIRecommendedAction.APPLY_RATE_CARD_ADJUSTMENT,
            human_review_required=False,
            evidence_used=["Order: ORD-ALIEN-9999"],  # Foreign ID
        )


def test_safe_fallback_on_provider_exception(batch_and_reconciliation):
    """Verify provider exception triggers safe fallback conforming to Section 11."""
    norm_batch, results = batch_and_reconciliation
    service = AIInvestigatorService(provider=FailingProvider())

    r08 = next(r for r in results if r.rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH)
    payment = next(p for p in norm_batch.payments if p.order_id == r08.order_id)

    output = service.investigate_transaction(r08, payment, None)

    assert output.classification == AIClassification.INCONCLUSIVE_VARIANCE
    assert output.confidence == Decimal("0.00")
    assert output.confidence_tier == AIConfidenceTier.LOW
    assert output.recommended_action == AIRecommendedAction.MANUAL_CONTROLLER_AUDIT
    assert output.human_review_required is True
    assert output.evidence_used == []


def test_safe_fallback_on_invalid_evidence_citation(batch_and_reconciliation):
    """Verify invalid evidence citations trigger safe fallback."""
    norm_batch, results = batch_and_reconciliation
    service = AIInvestigatorService(provider=BadEvidenceProvider())

    r08 = next(r for r in results if r.rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH)
    payment = next(p for p in norm_batch.payments if p.order_id == r08.order_id)

    output = service.investigate_transaction(r08, payment, None)

    assert output.classification == AIClassification.INCONCLUSIVE_VARIANCE
    assert output.confidence == Decimal("0.00")
    assert output.human_review_required is True


# M: Deterministic Repeatability
def test_mock_provider_deterministic_repeatability(batch_and_reconciliation):
    """Verify repeated runs with MockAIProvider produce 100% identical substantive results."""
    norm_batch, results = batch_and_reconciliation
    service1 = AIInvestigatorService()
    service2 = AIInvestigatorService()

    r08 = next(r for r in results if r.rule_id == ReconciliationRule.RULE_08_AMOUNT_MISMATCH)
    payment = next(p for p in norm_batch.payments if p.order_id == r08.order_id)
    settlement = next(s for s in norm_batch.settlements if s.order_ref == r08.order_id)

    out1 = service1.investigate_transaction(r08, payment, settlement)
    out2 = service2.investigate_transaction(r08, payment, settlement)

    assert out1.order_id == out2.order_id
    assert out1.classification == out2.classification
    assert out1.confidence == out2.confidence
    assert out1.confidence_tier == out2.confidence_tier
    assert out1.recommended_action == out2.recommended_action
    assert out1.human_review_required == out2.human_review_required
    assert out1.root_cause_analysis == out2.root_cause_analysis
    assert out1.evidence_used == out2.evidence_used
