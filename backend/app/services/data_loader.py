import json
from pathlib import Path
from typing import Optional
from pydantic import ValidationError
from app.core.config import settings
from app.models.transaction import SyntheticBatch, GroundTruthDataset


class DatasetLoadError(Exception):
    """Raised when dataset loading, parsing, or validation fails."""
    pass


class DataLoader:
    """Service responsible for loading and validating operational and benchmark datasets."""

    def __init__(self, default_batch_path: Optional[Path] = None, default_ground_truth_path: Optional[Path] = None):
        self.batch_path = default_batch_path or settings.synthetic_dataset_path
        self.ground_truth_path = default_ground_truth_path or settings.ground_truth_dataset_path

    def load_synthetic_batch(self, file_path: Optional[Path] = None) -> SyntheticBatch:
        """
        Load, parse, and validate the operational synthetic batch from JSON.
        
        Args:
            file_path: Optional custom path. If None, uses configured synthetic_dataset_path.
            
        Returns:
            Validated SyntheticBatch instance.
            
        Raises:
            DatasetLoadError: If file is missing, contains invalid JSON, or fails Pydantic schema validation.
        """
        target_path = Path(file_path) if file_path else self.batch_path

        if not target_path.exists():
            raise DatasetLoadError(f"Synthetic dataset file not found at: {target_path}")

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as exc:
            raise DatasetLoadError(f"Malformed JSON in synthetic dataset '{target_path}': {exc}") from exc
        except Exception as exc:
            raise DatasetLoadError(f"Failed to read synthetic dataset '{target_path}': {exc}") from exc

        try:
            batch = SyntheticBatch.model_validate(raw_data)
        except ValidationError as exc:
            raise DatasetLoadError(f"Synthetic dataset schema validation failed for '{target_path}': {exc}") from exc

        return batch

    def load_ground_truth(self, file_path: Optional[Path] = None) -> GroundTruthDataset:
        """
        Load, parse, and validate the isolated ground-truth dataset from JSON.
        
        Args:
            file_path: Optional custom path. If None, uses configured ground_truth_dataset_path.
            
        Returns:
            Validated GroundTruthDataset instance.
            
        Raises:
            DatasetLoadError: If file is missing, contains invalid JSON, or fails Pydantic schema validation.
        """
        target_path = Path(file_path) if file_path else self.ground_truth_path

        if not target_path.exists():
            raise DatasetLoadError(f"Ground-truth dataset file not found at: {target_path}")

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as exc:
            raise DatasetLoadError(f"Malformed JSON in ground-truth dataset '{target_path}': {exc}") from exc
        except Exception as exc:
            raise DatasetLoadError(f"Failed to read ground-truth dataset '{target_path}': {exc}") from exc

        try:
            ground_truth = GroundTruthDataset.model_validate(raw_data)
        except ValidationError as exc:
            raise DatasetLoadError(f"Ground-truth schema validation failed for '{target_path}': {exc}") from exc

        return ground_truth
