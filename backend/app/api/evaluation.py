from fastapi import APIRouter, HTTPException, status

from app.models.evaluation import BatchEvaluation
from app.services.data_loader import DataLoader
from app.services.evaluator import BatchEvaluator, EvaluationError
from app.services.orchestrator import pipeline_state

router = APIRouter(tags=["Evaluation"])


@router.get(
    "/evaluation/metrics",
    response_model=BatchEvaluation,
    status_code=status.HTTP_200_OK,
    summary="Get Batch Evaluation Metrics",
    description=(
        "Retrieve authentic performance evaluation metrics calculated by BatchEvaluator "
        "against isolated ground-truth benchmarks for the latest pipeline run. "
        "Includes accuracy, resolution rate, confusion matrix, and category breakdowns."
    ),
)
def get_evaluation_metrics() -> BatchEvaluation:
    """Retrieve evaluation metrics for the latest reconciliation run."""
    if pipeline_state.latest_results is None or pipeline_state.processing_time_ms is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reconciliation run available. Execute POST /api/reconciliation/run first.",
        )

    # Return cached evaluation if already computed for this run
    if pipeline_state.latest_evaluation is not None:
        return pipeline_state.latest_evaluation

    try:
        loader = DataLoader()
        ground_truth = loader.load_ground_truth()
        evaluation = BatchEvaluator.evaluate(
            results=pipeline_state.latest_results,
            ground_truth=ground_truth,
            processing_time_ms=pipeline_state.processing_time_ms,
        )
        pipeline_state.latest_evaluation = evaluation
        return evaluation
    except EvaluationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch evaluation calculation failed: {str(exc)}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during batch evaluation: {str(exc)}",
        ) from exc
