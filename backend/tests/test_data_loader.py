import json
import pytest
from pathlib import Path
from app.core.config import settings
from app.services.data_loader import DataLoader, DatasetLoadError
from app.models.transaction import SyntheticBatch, GroundTruthDataset


def test_data_loader_success():
    """Verify that synthetic dataset loads and validates successfully from real file."""
    loader = DataLoader()
    batch = loader.load_synthetic_batch()

    assert isinstance(batch, SyntheticBatch)
    assert batch.batch_id == "BATCH-2026-SYNTH-120"
    assert len(batch.payments) == 120
    assert len(batch.settlements) == 117


def test_data_loader_ground_truth_success():
    """Verify that ground-truth dataset loads and validates successfully."""
    loader = DataLoader()
    gt = loader.load_ground_truth()

    assert isinstance(gt, GroundTruthDataset)
    assert gt.batch_id == "BATCH-2026-SYNTH-120"
    assert gt.total_records == 120
    assert len(gt.records) == 120


def test_data_loader_missing_file_error(tmp_path: Path):
    """Verify that loader raises DatasetLoadError when target file does not exist."""
    loader = DataLoader()
    non_existent = tmp_path / "missing_dataset.json"

    with pytest.raises(DatasetLoadError) as exc_info:
        loader.load_synthetic_batch(non_existent)
    assert "not found" in str(exc_info.value).lower()


def test_data_loader_malformed_json_error(tmp_path: Path):
    """Verify that loader raises DatasetLoadError when target file contains invalid JSON."""
    bad_json_file = tmp_path / "corrupted.json"
    bad_json_file.write_text("{ this is not valid json }", encoding="utf-8")

    loader = DataLoader()
    with pytest.raises(DatasetLoadError) as exc_info:
        loader.load_synthetic_batch(bad_json_file)
    assert "malformed json" in str(exc_info.value).lower()


def test_data_loader_schema_invalid_error(tmp_path: Path):
    """Verify that loader raises DatasetLoadError when JSON schema is missing mandatory fields."""
    invalid_schema_file = tmp_path / "invalid_schema.json"
    invalid_data = {
        "batch_id": "BATCH-INVALID",
        # Missing generated_at and description
        "payments": [
            {
                "order_id": "ORD-BROKEN",
                # Missing auth_ref, gross_amount, currency, payment_method, booking_timestamp
            }
        ],
        "settlements": []
    }
    invalid_schema_file.write_text(json.dumps(invalid_data), encoding="utf-8")

    loader = DataLoader()
    with pytest.raises(DatasetLoadError) as exc_info:
        loader.load_synthetic_batch(invalid_schema_file)
    assert "validation failed" in str(exc_info.value).lower()
