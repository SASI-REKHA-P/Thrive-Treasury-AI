from abc import ABC, abstractmethod
from decimal import Decimal
import json
from typing import Optional
import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.models.ai_investigation import (
    AIClassification,
    AIRecommendedAction,
    AIConfidenceTier,
    AIInvestigationInput,
    LLMInvestigationPayload,
)


class AIProviderError(Exception):
    """Raised when an AI provider fails to return a valid response."""
    pass


class BaseAIProvider(ABC):
    """Abstract interface for exception investigation AI providers."""

    @abstractmethod
    def investigate(self, input_data: AIInvestigationInput) -> LLMInvestigationPayload:
        """Generate substantive investigation payload for an eligible exception."""
        pass


class MockAIProvider(BaseAIProvider):
    """
    Deterministic offline provider for automated testing and local execution.
    
    Generates rule-specific, pre-calibrated substantive investigation payloads based
    strictly on observed input facts. Zero external network calls; zero ground-truth leakage.
    """

    def investigate(self, input_data: AIInvestigationInput) -> LLMInvestigationPayload:
        rule = input_data.rule_id

        # RULE_04: Cross-currency briefing
        if rule == "RULE_04_CROSS_CURRENCY_CHECK":
            return LLMInvestigationPayload(
                classification=AIClassification.CROSS_BORDER_FX_EXPOSURE,
                confidence=Decimal("0.90"),
                confidence_tier=AIConfidenceTier.HIGH,
                root_cause_analysis=(
                    f"Payment of {input_data.gross_amount} {input_data.currency} cleared in "
                    f"{input_data.settlement_currency} at an observed implied rate of "
                    f"{input_data.effective_implied_rate}. Settlement delay reflects multi-day "
                    f"Nostro bank clearing. FX conversion rate verification required by treasury controller."
                ),
                recommended_action=AIRecommendedAction.ESCALATE_TO_TREASURY_FX_DESK,
                human_review_required=True,
                evidence_used=[
                    f"Order: {input_data.order_id}",
                    f"Payment: {input_data.gross_amount} {input_data.currency}",
                    f"Settlement: {input_data.net_deposit} {input_data.settlement_currency}",
                    f"Implied Rate: {input_data.effective_implied_rate}",
                ],
            )

        # RULE_08: Amount mismatch investigation
        if rule == "RULE_08_AMOUNT_MISMATCH":
            variance = input_data.variance_amount or Decimal("0.00")
            expected_fee = input_data.standard_expected_fee or Decimal("0.00")

            if variance <= Decimal("500.00"):
                unexplained = variance - expected_fee
                return LLMInvestigationPayload(
                    classification=AIClassification.NON_STANDARD_INTERCHANGE_FEE,
                    confidence=Decimal("0.85"),
                    confidence_tier=AIConfidenceTier.HIGH,
                    root_cause_analysis=(
                        f"Payment of {input_data.gross_amount} {input_data.currency} settled at "
                        f"{input_data.net_deposit} {input_data.settlement_currency}, resulting in a "
                        f"variance of {variance} {input_data.currency}. Discrepancy exceeds standard configured "
                        f"2% MDR fee ({expected_fee}) by {unexplained}. Consistent with commercial or "
                        f"corporate card rate-card adjustments."
                    ),
                    recommended_action=AIRecommendedAction.APPLY_RATE_CARD_ADJUSTMENT,
                    human_review_required=False,  # Enforced/adjusted programmatically by service
                    evidence_used=[
                        f"Order: {input_data.order_id}",
                        f"Gross: {input_data.gross_amount}",
                        f"Net: {input_data.net_deposit}",
                        f"Variance: {variance}",
                    ],
                )
            else:
                return LLMInvestigationPayload(
                    classification=AIClassification.UNEXPLAINED_GATEWAY_SHORTFALL,
                    confidence=Decimal("0.80"),
                    confidence_tier=AIConfidenceTier.MEDIUM,
                    root_cause_analysis=(
                        f"Payment of {input_data.gross_amount} {input_data.currency} settled at "
                        f"{input_data.net_deposit} {input_data.settlement_currency}, resulting in a "
                        f"variance of {variance} {input_data.currency}. The shortfall significantly exceeds "
                        f"the standard configured fee ({expected_fee}). Inquiry with acquirer recommended "
                        f"to identify unaccounted deductions."
                    ),
                    recommended_action=AIRecommendedAction.INITIATE_ACQUIRER_DISPUTE,
                    human_review_required=True,
                    evidence_used=[
                        f"Order: {input_data.order_id}",
                        f"Gross: {input_data.gross_amount}",
                        f"Net: {input_data.net_deposit}",
                        f"Variance: {variance}",
                    ],
                )

        # Fallback / Inconclusive
        return LLMInvestigationPayload(
            classification=AIClassification.INCONCLUSIVE_VARIANCE,
            confidence=Decimal("0.40"),
            confidence_tier=AIConfidenceTier.LOW,
            root_cause_analysis="Observed variance cannot be classified with available evidence. Manual controller audit required.",
            recommended_action=AIRecommendedAction.MANUAL_CONTROLLER_AUDIT,
            human_review_required=True,
            evidence_used=[f"Order: {input_data.order_id}"],
        )


class GeminiAIProvider(BaseAIProvider):
    """
    Live Google Gemini REST provider utilizing structured JSON schema output.
    Uses httpx for lightweight REST integration without extra SDK dependencies.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 15.0,
    ):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.timeout = timeout

    def investigate(self, input_data: AIInvestigationInput) -> LLMInvestigationPayload:
        if not self.api_key:
            raise AIProviderError("Gemini API key is not configured in settings.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        system_instruction = (
            "You are an AI Treasury Auditor investigating financial reconciliation exceptions. "
            "Use ONLY the exact financial facts provided. Do NOT invent exchange rates, fee percentages, "
            "transaction IDs, settlement records, or external bank policies. "
            "If evidence does not support a clear conclusion, return INCONCLUSIVE_VARIANCE with confidence 0.40, "
            "confidence_tier LOW, and recommended_action MANUAL_CONTROLLER_AUDIT."
        )

        user_content = json.dumps(input_data.model_dump(mode="json"), indent=2)

        payload = {
            "contents": [{"parts": [{"text": user_content}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed_json = json.loads(candidate_text)
            return LLMInvestigationPayload.model_validate(parsed_json)
        except httpx.TimeoutException as exc:
            raise AIProviderError(f"Gemini API request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Gemini API HTTP request failed: {exc}") from exc
        except (KeyError, json.JSONDecodeError, ValidationError) as exc:
            raise AIProviderError(f"Gemini API returned malformed or schema-invalid JSON: {exc}") from exc
        except Exception as exc:
            raise AIProviderError(f"Unexpected error communicating with Gemini API: {exc}") from exc
