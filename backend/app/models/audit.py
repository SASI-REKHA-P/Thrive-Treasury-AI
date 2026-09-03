from datetime import datetime
from typing import Dict, Any, Optional, Literal
from pydantic import Field
from .base import FinancialBaseModel


class AuditEvent(FinancialBaseModel):
    """Chronological event entry tracking lifecycle events and decision traceability."""
    event_id: str = Field(..., description="Unique UUID event identifier")
    timestamp: datetime = Field(..., description="High-resolution UTC event timestamp")
    batch_id: str = Field(..., description="Target batch identifier")
    order_id: Optional[str] = Field(default=None, description="Specific transaction reference if applicable")
    event_type: Literal[
        "BATCH_LOADED",
        "RECORDS_NORMALIZED",
        "RULE_EVALUATED",
        "MATCHED",
        "EXCEPTION_DETECTED",
        "AI_INVESTIGATION_PENDING",
        "HUMAN_REVIEW_QUEUED",
        "DECISION_RECORDED"
    ] = Field(..., description="Categorized lifecycle event type")
    actor: str = Field(default="SYSTEM:DETERMINISTIC_ENGINE", description="Component or agent generating the event")
    rule_id: Optional[str] = Field(default=None, description="Deterministic rule identifier if applicable")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured payload of event parameters")


class AuditClearResponse(FinancialBaseModel):
    """Response returned when in-memory audit trail is cleared."""
    cleared: bool = Field(default=True, description="Whether audit trail was successfully cleared")
    count: int = Field(..., description="Number of audit events removed")

