from typing import Any, Dict, List, Optional
import json
from fastapi import APIRouter, HTTPException, Query, Response, status

from app.models.reconciliation import (
    ReconciliationResult,
    ReconciliationRule,
    ReconciliationStatus,
)
from app.models.ai_investigation import AIInvestigationOutput
from app.models.audit import AuditEvent, AuditClearResponse
from app.services.orchestrator import (

    PipelineOrchestrator,
    PipelineRunSummary,
    pipeline_state,
)
from app.services.audit_service import audit_service
from app.services.review_service import (
    ReviewRequest,
    ReviewResponse,
    review_service,
)
from app.services.export_service import export_service

router = APIRouter(tags=["Reconciliation"])




@router.post(
    "/reconciliation/run",
    response_model=PipelineRunSummary,
    status_code=status.HTTP_200_OK,
    summary="Execute Complete Reconciliation Pipeline",
    description=(
        "Executes the full operational pipeline: DataLoader -> Normalizer -> "
        "DeterministicReconciliationEngine -> AIInvestigatorService. "
        "Stores the latest run in memory and returns a structured summary."
    ),
)
def run_reconciliation() -> PipelineRunSummary:
    """Trigger complete operational reconciliation pipeline run."""
    try:
        orchestrator = PipelineOrchestrator()
        return orchestrator.run_pipeline()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation pipeline execution failed: {str(exc)}",
        ) from exc


@router.get(
    "/reconciliation/transactions",
    response_model=List[ReconciliationResult],
    status_code=status.HTTP_200_OK,
    summary="Query Reconciliation Results",
    description=(
        "Retrieve transaction results from the latest pipeline run. "
        "Supports filtering by status, rule_id, and requires_ai using AND semantics."
    ),
)
def get_transactions(
    status_filter: Optional[ReconciliationStatus] = Query(
        default=None, alias="status", description="Filter by reconciliation status"
    ),
    rule_id: Optional[ReconciliationRule] = Query(
        default=None, description="Filter by deterministic rule identifier"
    ),
    requires_ai: Optional[bool] = Query(
        default=None, description="Filter by AI investigation requirement flag"
    ),
) -> List[ReconciliationResult]:
    """Retrieve filtered transaction results from the latest pipeline run."""
    if pipeline_state.latest_results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reconciliation run available. Execute POST /api/reconciliation/run first.",
        )

    results = pipeline_state.latest_results

    if status_filter is not None:
        results = [r for r in results if r.status == status_filter]

    if rule_id is not None:
        results = [r for r in results if r.rule_id == rule_id]

    if requires_ai is not None:
        if requires_ai:
            results = [r for r in results if r.requires_ai or r.ai_status == "INVESTIGATED"]
        else:
            results = [r for r in results if not r.requires_ai and r.ai_status != "INVESTIGATED"]

    return results



@router.get(
    "/reconciliation/transactions/{order_id}",
    response_model=ReconciliationResult,
    status_code=status.HTTP_200_OK,
    summary="Get Single Transaction Result",
    description="Retrieve a single transaction result by order_id from the latest pipeline run.",
)
def get_transaction_by_id(order_id: str) -> ReconciliationResult:
    """Retrieve an individual transaction result by order_id."""
    if pipeline_state.latest_results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reconciliation run available. Execute POST /api/reconciliation/run first.",
        )

    for r in pipeline_state.latest_results:
        if r.order_id == order_id:
            return r

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Transaction with order_id '{order_id}' not found in the latest reconciliation run.",
    )


@router.get(
    "/investigations/{order_id}",
    response_model=AIInvestigationOutput,
    status_code=status.HTTP_200_OK,
    summary="Get AI Investigation Brief",
    description="Retrieve the AI exception investigation brief attached to a specific transaction.",
)
def get_investigation_by_id(order_id: str) -> AIInvestigationOutput:
    """Retrieve the AI investigation brief for a specific order_id."""
    if pipeline_state.latest_results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reconciliation run available. Execute POST /api/reconciliation/run first.",
        )

    target: Optional[ReconciliationResult] = None
    for r in pipeline_state.latest_results:
        if r.order_id == order_id:
            target = r
            break

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with order_id '{order_id}' not found in the latest reconciliation run.",
        )

    if target.ai_investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Transaction '{order_id}' was not investigated by AI "
                f"(rule: {target.rule_id.value}, ai_status: {target.ai_status})."
            ),
        )

    return target.ai_investigation


@router.post(
    "/reconciliation/review/{order_id}",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Human Controller Review Decision",
    description=(
        "Records an authoritative review decision (APPROVE_ADVISORY, MANUAL_OVERRIDE, "
        "or ESCALATE_DISPUTE) by a human finance controller. Updates the workflow status "
        "and appends an immutable AuditEvent to the audit log while preserving deterministic "
        "reconciliation rules, amounts, and statuses."
    ),
)
def submit_review_decision(
    order_id: str,
    request: ReviewRequest,
) -> ReviewResponse:
    """Submit a controller decision on an eligible transaction."""
    return review_service.submit_decision(order_id, request)


@router.get(
    "/reconciliation/audit-trail",
    response_model=List[AuditEvent],
    status_code=status.HTTP_200_OK,
    summary="Retrieve Audit Trail",
    description="Retrieve chronological audit trail entries, optionally filtered by order_id.",
)
def get_audit_trail(
    order_id: Optional[str] = Query(
        default=None, description="Filter audit trail events by order_id"
    ),
) -> List[AuditEvent]:
    """Retrieve chronological audit events from the in-memory audit store."""
    return audit_service.get_events(order_id)


@router.delete(
    "/reconciliation/audit-trail",
    response_model=AuditClearResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear Audit Trail",
    description="Clear all in-memory audit events without modifying reconciliation results or pipeline state.",
)
def clear_audit_trail() -> AuditClearResponse:
    """Clear all in-memory audit events and return the count of removed events."""
    count = audit_service.clear()
    return AuditClearResponse(cleared=True, count=count)



@router.get(
    "/reconciliation/export/ledger",
    summary="Export Full Reconciliation Ledger (CSV)",
    description="Export complete operational reconciliation ledger in CSV format.",
    response_class=Response,
)
def export_ledger() -> Response:
    """Download the complete operational reconciliation ledger as a CSV file."""
    csv_content = export_service.generate_ledger_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'attachment; filename="reconciliation_ledger.csv"',
        },
    )


@router.get(
    "/reconciliation/export/disputes",
    summary="Export Acquirer Dispute Packet (CSV)",
    description="Export only cases that have been explicitly escalated by a controller in CSV format.",
    response_class=Response,
)
def export_disputes() -> Response:
    """Download the active acquirer dispute packet as a CSV file."""
    csv_content = export_service.generate_disputes_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'attachment; filename="acquirer_dispute_packet.csv"',
        },
    )


@router.get(
    "/reconciliation/export/disputes/{order_id}",
    summary="Export Single Case Dispute Packet (JSON)",
    description="Export structured dispute file with deterministic findings, AI advisory, and controller audit context.",
    response_class=Response,
)
def export_single_dispute(order_id: str) -> Response:
    """Download an individual escalated case dispute packet as a JSON file."""
    packet_data = export_service.generate_single_case_dispute(order_id)
    json_content = json.dumps(packet_data, indent=2)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Content-Disposition": f'attachment; filename="dispute_packet_{order_id}.json"',
        },
    )


@router.get(
    "/reconciliation/export/audit-trail",
    summary="Export Compliance Audit Trail (CSV)",
    description="Export chronological audit trail events in CSV format.",
    response_class=Response,
)
def export_audit_trail() -> Response:
    """Download the compliance audit trail as a CSV file."""
    csv_content = export_service.generate_audit_trail_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'attachment; filename="audit_trail.csv"',
        },
    )


