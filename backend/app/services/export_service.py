import csv
from datetime import datetime, timezone
import io
import json
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from app.models.reconciliation import ReconciliationResult
from app.services.orchestrator import pipeline_state
from app.services.audit_service import audit_service, AuditService


LEDGER_CSV_HEADERS = [
    "order_id",
    "auth_ref",
    "settlement_ids",
    "payment_amount",
    "payment_currency",
    "settlement_amount",
    "settlement_currency",
    "variance",
    "status",
    "rule_id",
    "deterministic_reason",
    "human_review_status",
    "review_required",
    "ai_investigated",
    "ai_classification",
    "ai_confidence",
    "ai_confidence_tier",
    "ai_recommended_action",
]

DISPUTES_CSV_HEADERS = [
    "order_id",
    "auth_ref",
    "settlement_ids",
    "payment_amount",
    "payment_currency",
    "settlement_amount",
    "settlement_currency",
    "variance",
    "rule_id",
    "deterministic_reason",
    "human_review_status",
    "ai_investigated",
    "ai_classification",
    "ai_confidence",
    "ai_confidence_tier",
    "ai_root_cause",
    "ai_recommended_action",
    "ai_evidence",
    "controller_actor",
    "controller_decision",
    "controller_notes",
    "review_timestamp",
]

AUDIT_CSV_HEADERS = [
    "event_id",
    "timestamp",
    "batch_id",
    "order_id",
    "event_type",
    "actor",
    "rule_id",
    "action",
    "notes",
    "details_summary",
]


class ExportService:
    """
    Service responsible strictly for formatting operational reconciliation results,
    dispute packages, and audit trails for external download.
    
    CRITICAL SAFETY RULES:
    - Strictly READ-ONLY: Never alters pipeline state, transactions, or review statuses.
    - Zero Ground-Truth Access: Strictly isolated from benchmark evaluation schemas.
    - Decimal Precision: Preserves exact string decimal amounts (e.g. '1200.00').
    - Standard Library: Uses Python's built-in csv and io modules.
    """


    def __init__(self, audit_svc: Optional[AuditService] = None) -> None:
        self.audit_service = audit_svc or audit_service

    def _ensure_pipeline_run(self) -> List[ReconciliationResult]:
        """Ensure an operational pipeline run exists and return the results."""
        if pipeline_state.latest_results is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No reconciliation run available. Execute POST /api/reconciliation/run first.",
            )
        return pipeline_state.latest_results

    def _get_auth_ref_map(self) -> Dict[str, str]:
        """Build mapping of order_id to gateway auth_ref if normalized batch is available."""
        mapping: Dict[str, str] = {}
        if pipeline_state.latest_normalized_batch and pipeline_state.latest_normalized_batch.payments:
            for p in pipeline_state.latest_normalized_batch.payments:
                mapping[p.order_id] = p.auth_ref
        return mapping

    def generate_ledger_csv(self) -> str:
        """
        Generate full operational reconciliation ledger CSV.
        Contains all records from the current batch run.
        """
        results = self._ensure_pipeline_run()
        auth_map = self._get_auth_ref_map()

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(LEDGER_CSV_HEADERS)

        for r in results:
            settlement_ids_str = "; ".join(r.settlement_ids) if r.settlement_ids else ""
            payment_amt_str = f"{r.payment_amount:.2f}"
            settlement_amt_str = f"{r.settlement_amount:.2f}" if r.settlement_amount is not None else ""
            diff_str = f"{r.difference:.2f}" if r.difference is not None else ""

            ai_inv = r.ai_investigation
            is_ai = "TRUE" if (r.ai_status == "INVESTIGATED" and ai_inv) else "FALSE"
            ai_cls = ai_inv.classification.value if ai_inv else ""
            ai_conf = f"{ai_inv.confidence:.2f}" if ai_inv else ""
            ai_tier = ai_inv.confidence_tier.value if ai_inv else ""
            ai_act = ai_inv.recommended_action.value if ai_inv else ""

            writer.writerow([
                r.order_id,
                auth_map.get(r.order_id, ""),
                settlement_ids_str,
                payment_amt_str,
                r.payment_currency,
                settlement_amt_str,
                r.settlement_currency or "",
                diff_str,
                r.status.value,
                r.rule_id.value if r.rule_id else "",
                r.reason,
                r.human_review_status,
                "TRUE" if r.requires_human_review else "FALSE",
                is_ai,
                ai_cls,
                ai_conf,
                ai_tier,
                ai_act,
            ])

        return output.getvalue()

    def generate_disputes_csv(self) -> str:
        """
        Generate acquirer dispute packet CSV.
        Contains ONLY transactions that have been explicitly escalated (human_review_status == 'ESCALATED').
        If no cases have been escalated, returns a valid CSV with headers only.
        """
        results = self._ensure_pipeline_run()
        auth_map = self._get_auth_ref_map()

        # Filter strictly for escalated cases
        escalated_cases = [r for r in results if r.human_review_status == "ESCALATED"]

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(DISPUTES_CSV_HEADERS)

        for r in escalated_cases:
            settlement_ids_str = "; ".join(r.settlement_ids) if r.settlement_ids else ""
            payment_amt_str = f"{r.payment_amount:.2f}"
            settlement_amt_str = f"{r.settlement_amount:.2f}" if r.settlement_amount is not None else ""
            diff_str = f"{r.difference:.2f}" if r.difference is not None else ""

            ai_inv = r.ai_investigation
            is_ai = "TRUE" if (r.ai_status == "INVESTIGATED" and ai_inv) else "FALSE"
            ai_cls = ai_inv.classification.value if ai_inv else ""
            ai_conf = f"{ai_inv.confidence:.2f}" if ai_inv else ""
            ai_tier = ai_inv.confidence_tier.value if ai_inv else ""
            ai_cause = ai_inv.root_cause_analysis if ai_inv else ""
            ai_act = ai_inv.recommended_action.value if ai_inv else ""
            ai_ev = "; ".join(ai_inv.evidence_used) if (ai_inv and ai_inv.evidence_used) else ""

            # Extract latest controller review decision from audit trail
            order_events = self.audit_service.get_events(order_id=r.order_id)
            decision_event = next((e for e in order_events if e.event_type == "DECISION_RECORDED"), None)

            actor = decision_event.actor if decision_event else ""
            decision = decision_event.details.get("action", "") if decision_event else ""
            notes = decision_event.details.get("notes", "") if decision_event else ""
            rev_time = decision_event.timestamp.isoformat() if decision_event else ""

            writer.writerow([
                r.order_id,
                auth_map.get(r.order_id, ""),
                settlement_ids_str,
                payment_amt_str,
                r.payment_currency,
                settlement_amt_str,
                r.settlement_currency or "",
                diff_str,
                r.rule_id.value if r.rule_id else "",
                r.reason,
                r.human_review_status,
                is_ai,
                ai_cls,
                ai_conf,
                ai_tier,
                ai_cause,
                ai_act,
                ai_ev,
                actor,
                decision,
                notes,
                rev_time,
            ])

        return output.getvalue()

    def generate_single_case_dispute(self, order_id: str) -> Dict[str, Any]:
        """
        Generate structured JSON dispute package for a single escalated transaction.
        Rejects non-existent orders with HTTP 404, and non-escalated cases with HTTP 409.
        """
        results = self._ensure_pipeline_run()
        auth_map = self._get_auth_ref_map()

        target: Optional[ReconciliationResult] = None
        for r in results:
            if r.order_id == order_id:
                target = r
                break

        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with order_id '{order_id}' not found in the latest reconciliation run.",
            )

        # Enforce dispute eligibility
        if target.human_review_status != "ESCALATED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Transaction '{order_id}' is not an eligible dispute package. "
                    f"Current review status is '{target.human_review_status}'. "
                    f"Only cases with review status 'ESCALATED' can be exported as dispute packages."
                ),
            )

        # Extract audit history
        order_events = self.audit_service.get_events(order_id=order_id)
        decision_event = next((e for e in order_events if e.event_type == "DECISION_RECORDED"), None)

        ai_inv = target.ai_investigation
        ai_advisory = None
        if ai_inv:
            ai_advisory = {
                "advisory_disclaimer": "AI investigation is advisory intelligence only. Not an admission or confirmation of financial liability.",
                "classification": ai_inv.classification.value,
                "confidence": f"{ai_inv.confidence:.2f}",
                "confidence_tier": ai_inv.confidence_tier.value,
                "root_cause_hypothesis": ai_inv.root_cause_analysis,
                "recommended_action": ai_inv.recommended_action.value,
                "evidence_citations": ai_inv.evidence_used,
            }

        return {
            "packet_type": "ACQUIRER_DISPUTE_PACKET",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "case": {
                "order_id": target.order_id,
                "auth_ref": auth_map.get(target.order_id, ""),
                "settlement_ids": target.settlement_ids,
                "reconciliation_status": target.status.value,
                "rule_id": target.rule_id.value if target.rule_id else None,
                "amounts": {
                    "payment_gross": f"{target.payment_amount:.2f}",
                    "payment_currency": target.payment_currency,
                    "settlement_net": f"{target.settlement_amount:.2f}" if target.settlement_amount is not None else None,
                    "settlement_currency": target.settlement_currency,
                    "variance": f"{target.difference:.2f}" if target.difference is not None else None,
                },
                "human_review_status": target.human_review_status,
            },
            "deterministic_findings": {
                "rule_id": target.rule_id.value if target.rule_id else None,
                "reason": target.reason,
                "checks": target.checks.model_dump() if target.checks else {},
            },
            "ai_advisory": ai_advisory,
            "controller_review": {
                "actor": decision_event.actor if decision_event else None,
                "decision": decision_event.details.get("action") if decision_event else None,
                "notes": decision_event.details.get("notes") if decision_event else None,
                "review_timestamp": decision_event.timestamp.isoformat() if decision_event else None,
            },
            "audit_context": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "actor": e.actor,
                    "timestamp": e.timestamp.isoformat(),
                    "details": e.details,
                }
                for e in order_events
            ],
        }

    def generate_audit_trail_csv(self) -> str:
        """
        Generate compliance audit trail CSV.
        Contains chronological audit events recorded during batch cycles and controller reviews.
        """
        self._ensure_pipeline_run()
        events = self.audit_service.get_events()

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(AUDIT_CSV_HEADERS)

        for e in events:
            details = e.details or {}
            action = details.get("action", "")
            notes = details.get("notes", "")

            # Create clean details summary string without leaking internal secrets
            summary_parts = []
            for k, v in details.items():
                if k not in ("action", "notes"):
                    summary_parts.append(f"{k}={v}")
            details_summary = "; ".join(summary_parts)

            writer.writerow([
                e.event_id,
                e.timestamp.isoformat(),
                e.batch_id,
                e.order_id or "",
                e.event_type,
                e.actor,
                e.rule_id or "",
                action,
                notes,
                details_summary,
            ])

        return output.getvalue()


# Global singleton export service
export_service = ExportService()
