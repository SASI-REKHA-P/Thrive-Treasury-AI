from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from fastapi import HTTPException, status
from pydantic import Field, field_validator

from app.models.base import FinancialBaseModel
from app.models.audit import AuditEvent
from app.models.reconciliation import ReconciliationResult
from app.services.orchestrator import pipeline_state
from app.services.audit_service import audit_service, AuditService


class ControllerAction(str, Enum):
    APPROVE_ADVISORY = "APPROVE_ADVISORY"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    ESCALATE_DISPUTE = "ESCALATE_DISPUTE"


class ReviewRequest(FinancialBaseModel):
    """Payload submitted by a finance controller to record an operational decision."""
    action: ControllerAction = Field(..., description="Controller action decision")
    actor: str = Field(..., min_length=1, max_length=100, description="Controller username or ID")
    notes: Optional[str] = Field(default="", max_length=1000, description="Controller operational rationale or notes")

    @field_validator("actor")
    @classmethod
    def validate_actor(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Actor identifier cannot be empty or whitespace only.")
        return trimmed


class ReviewResponse(FinancialBaseModel):
    """Structured response confirming recorded review decision and audit trail event."""
    order_id: str
    action: ControllerAction
    actor: str
    notes: str
    previous_human_review_status: str
    resulting_human_review_status: str
    timestamp: datetime
    audit_event_id: str


class ReviewService:
    """
    Operational service encapsulating human controller review decisions and audit logging.
    Strictly preserves deterministic reconciliation status and rule classifications.
    """

    def __init__(self, audit_svc: Optional[AuditService] = None) -> None:
        self.audit_service = audit_svc or audit_service

    def submit_decision(self, order_id: str, request: ReviewRequest) -> ReviewResponse:
        """
        Record a controller decision on an eligible transaction.
        Updates only human_review_status and records an immutable AuditEvent.
        """
        if pipeline_state.latest_results is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No reconciliation run available. Execute POST /api/reconciliation/run first.",
            )

        # Locate target transaction
        target_txn: Optional[ReconciliationResult] = None
        for r in pipeline_state.latest_results:
            if r.order_id == order_id:
                target_txn = r
                break

        if target_txn is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with order_id '{order_id}' not found in latest reconciliation run.",
            )

        # Check review eligibility
        if not target_txn.requires_human_review and target_txn.human_review_status == "NOT_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction '{order_id}' does not require human controller review.",
            )

        # Check if already resolved
        if target_txn.human_review_status == "RESOLVED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Transaction '{order_id}' has already been resolved and cannot be modified.",
            )

        # Determine resulting workflow status
        previous_status = target_txn.human_review_status
        if request.action == ControllerAction.APPROVE_ADVISORY:
            resulting_status = "RESOLVED"
        elif request.action == ControllerAction.MANUAL_OVERRIDE:
            resulting_status = "RESOLVED"
        elif request.action == ControllerAction.ESCALATE_DISPUTE:
            resulting_status = "ESCALATED"
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported controller action: {request.action}",
            )

        # Update ONLY workflow-level status (deterministic status remains untouched!)
        target_txn.human_review_status = resulting_status

        # Create and append immutable audit event
        now = datetime.now(timezone.utc)
        event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        audit_event = AuditEvent(
            event_id=event_id,
            timestamp=now,
            batch_id="BATCH-2026-SYNTH-120",
            order_id=order_id,
            event_type="DECISION_RECORDED",
            actor=request.actor,
            rule_id=target_txn.rule_id.value if target_txn.rule_id else None,
            details={
                "action": request.action.value,
                "notes": request.notes.strip() if request.notes else "",
                "previous_human_review_status": previous_status,
                "resulting_human_review_status": resulting_status,
                "deterministic_status": target_txn.status.value,
                "deterministic_rule": target_txn.rule_id.value if target_txn.rule_id else None,
            },
        )
        self.audit_service.append_event(audit_event)

        return ReviewResponse(
            order_id=order_id,
            action=request.action,
            actor=request.actor,
            notes=request.notes.strip() if request.notes else "",
            previous_human_review_status=previous_status,
            resulting_human_review_status=resulting_status,
            timestamp=now,
            audit_event_id=event_id,
        )


# Global singleton review service
review_service = ReviewService()
