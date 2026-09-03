from pathlib import Path
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

# Determine repository root reliably using pathlib
# config.py -> core -> app -> backend -> repo root
CORE_DIR = Path(__file__).resolve().parent
APP_DIR = CORE_DIR.parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

DATA_DIR = ROOT_DIR / "data"
SYNTHETIC_DATASET_PATH = DATA_DIR / "synthetic_batch_120.json"
GROUND_TRUTH_DATASET_PATH = DATA_DIR / "ground_truth_120.json"


class Settings(BaseModel):
    app_name: str = "Thrive Treasury AI Backend"
    api_prefix: str = "/api"
    environment: str = "development"
    version: str = "0.1.0"
    
    # Filesystem Paths
    root_dir: Path = ROOT_DIR
    data_dir: Path = DATA_DIR
    synthetic_dataset_path: Path = SYNTHETIC_DATASET_PATH
    ground_truth_dataset_path: Path = GROUND_TRUTH_DATASET_PATH

    # Reconciliation Engine Configuration Parameters
    standard_clearing_window_hours: float = Field(
        default=24.0,
        description="Standard intraday settlement threshold (<=24h considered exact match)"
    )
    max_date_tolerance_hours: float = Field(
        default=72.0,
        description="Maximum permitted multi-day settlement window for date tolerance matching"
    )
    default_mdr_rate: Decimal = Field(
        default=Decimal("0.02"),
        description="Standard merchant discount rate (2.0%)"
    )
    default_gst_rate: Decimal = Field(
        default=Decimal("0.18"),
        description="Goods and Services Tax on MDR (18.0%)"
    )
    nostro_clearing_account: str = Field(
        default="SBI-NOSTRO-01",
        description="Designated Nostro bank account reference for cross-border foreign exchange clearing"
    )
    base_operating_currency: str = Field(
        default="INR",
        description="Base treasury operating settlement currency"
    )

    # AI Exception Investigation Configuration
    ai_provider: str = Field(
        default="mock",
        description="AI provider implementation: 'mock' or 'gemini'"
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key for live AI investigations"
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Google Gemini model identifier"
    )

    # Helpers
    def verify_paths(self) -> dict[str, bool]:
        """Verify that dataset files exist at configured paths."""
        return {
            "root_exists": self.root_dir.exists(),
            "data_dir_exists": self.data_dir.exists(),
            "synthetic_batch_exists": self.synthetic_dataset_path.exists(),
            "ground_truth_exists": self.ground_truth_dataset_path.exists(),
        }


settings = Settings()
