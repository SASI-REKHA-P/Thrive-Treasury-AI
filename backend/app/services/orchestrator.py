from datetime import datetime, timezone
from decimal import Decimal
import time
from typing import Dict, List, Optional
import uuid
from pydantic import Field

from app.models.base import FinancialBaseModel
from app.models.normalized import NormalizedBatch
from app.models.reconciliation import ReconciliationResult
from app.models.evaluation import BatchEvaluation
from app.services.data_loader import DataLoader
from app.services.normalizer import Normalizer
from app.services.engine import DeterministicReconciliationEngine
from app.services.ai_investigator import AIInvestigatorService


class PipelineRunSummary(FinancialBaseModel):
    """Structured summary returned upon pipeline execution."""
    run_id: str = Field(..., description="Unique pipeline execution identifier")
    timestamp: datetime = Field(..., description="UTC execution timestamp")
    total: int = Field(..., description="Total transactions processed")
    matched: int = Field(..., description="Count of deterministically matched transactions")
    exceptions: int = Field(..., description="Count of transactions flagged as exceptions")
    pending_review: int = Field(..., description="Count of transactions routed to pending review")
    ai_investigated: int = Field(..., description="Count of transactions selectively investigated by AI")
    processing_time_ms: Decimal = Field(..., description="Measured execution latency in milliseconds")


class PipelineState:
    """
    In-memory store retaining the latest successful pipeline run.
    
    NOTE: This is intentionally an in-memory process-level store for the hackathon MVP.
    State is reset when the application process restarts. Persistent storage is not part of Step 2.7.
    """

    def __init__(self) -> None:
        self.latest_run_summary: Optional[PipelineRunSummary] = None
        self.latest_results: Optional[List[ReconciliationResult]] = None
        self.latest_normalized_batch: Optional[NormalizedBatch] = None
        self.processing_time_ms: Optional[Decimal] = None
        self.latest_evaluation: Optional[BatchEvaluation] = None

    def clear(self) -> None:
        """Clear in-memory state (useful for testing and resets)."""
        self.latest_run_summary = None
        self.latest_results = None
        self.latest_normalized_batch = None
        self.processing_time_ms = None
        self.latest_evaluation = None
        from app.services.audit_service import audit_service
        audit_service.clear()



# Global singleton in-memory state for process lifetime
pipeline_state = PipelineState()


class PipelineOrchestrator:
    """
    Orchestration service coordinating data loading, normalization,
    deterministic reconciliation, and selective AI investigation.
    
    Uses existing services as the single source of truth. Does NOT duplicate business logic,
    reconciliation rules, or access ground-truth benchmark data.
    """

    def __init__(
        self,
        loader: Optional[DataLoader] = None,
        normalizer: Optional[Normalizer] = None,
        engine: Optional[DeterministicReconciliationEngine] = None,
        investigator: Optional[AIInvestigatorService] = None,
        state: Optional[PipelineState] = None,
    ) -> None:
        self.loader = loader or DataLoader()
        self.normalizer = normalizer or Normalizer()
        self.engine = engine or DeterministicReconciliationEngine()
        self.investigator = investigator or AIInvestigatorService()
        self.state = state or pipeline_state

    def run_pipeline(self) -> PipelineRunSummary:
        """
        Execute the complete operational pipeline:
        1. Load synthetic operational batch (DataLoader)
        2. Normalize records (Normalizer)
        3. Deterministic reconciliation (DeterministicReconciliationEngine)
        4. Selective AI investigation (AIInvestigatorService)
        5. Store latest results in memory
        6. Return structured pipeline summary
        """
        start_time = time.perf_counter()

        # Step 1: Load operational batch (no ground truth)
        raw_batch = self.loader.load_synthetic_batch()

        # Step 2: Normalize
        normalized_batch = self.normalizer.normalize_batch(raw_batch)

        # Step 3: Deterministic reconciliation
        reconciled_results = self.engine.reconcile_batch(normalized_batch)

        # Step 4: Selective AI investigation (13 eligible cases, 107 bypassed)
        investigated_results = self.investigator.investigate_batch(
            reconciled_results, normalized_batch
        )

        end_time = time.perf_counter()
        raw_latency_ms = (end_time - start_time) * 1000.0
        # Ensure minimum positive latency for clean throughput calculations
        processing_time_ms = Decimal(str(max(round(raw_latency_ms, 2), 1.00)))

        # Step 5: Compute summary metrics from actual output
        total = len(investigated_results)
        matched = sum(1 for r in investigated_results if r.status.value == "MATCHED")
        exceptions = sum(1 for r in investigated_results if r.status.value == "EXCEPTION")
        pending_review = sum(1 for r in investigated_results if r.status.value == "PENDING_REVIEW")
        ai_investigated = sum(1 for r in investigated_results if r.ai_status == "INVESTIGATED")

        summary = PipelineRunSummary(
            run_id=f"RUN-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now(timezone.utc),
            total=total,
            matched=matched,
            exceptions=exceptions,
            pending_review=pending_review,
            ai_investigated=ai_investigated,
            processing_time_ms=processing_time_ms,
        )

        # Step 6: Retain in memory
        self.state.latest_run_summary = summary
        self.state.latest_results = investigated_results
        self.state.latest_normalized_batch = normalized_batch
        self.state.processing_time_ms = processing_time_ms
        self.state.latest_evaluation = None  # Reset evaluation cache on new run

        # Step 7: Record BATCH_LOADED audit event
        from app.models.audit import AuditEvent
        from app.services.audit_service import audit_service
        audit_service.append_event(
            AuditEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                timestamp=datetime.now(timezone.utc),
                batch_id=normalized_batch.batch_id,
                event_type="BATCH_LOADED",
                actor="SYSTEM:ORCHESTRATOR",
                details={
                    "total": total,
                    "matched": matched,
                    "exceptions": exceptions,
                    "pending_review": pending_review,
                    "processing_time_ms": str(processing_time_ms),
                },
            )
        )

        return summary

