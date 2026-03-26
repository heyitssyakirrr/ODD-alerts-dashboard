from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_SOURCE = os.getenv("DATA_SOURCE", "detica_parquet")

CSV_PATH = Path(
    os.getenv("CSV_PATH", BASE_DIR / "odd_alerts.csv")
)

ALERT_HEADER_PATH = Path(
    os.getenv("ALERT_HEADER_PATH", BASE_DIR / "mock_alert_header.parquet")
)

WORKFLOW_STATUSES_PATH = Path(
    os.getenv("WORKFLOW_STATUSES_PATH", BASE_DIR / "mock_workflow_statuses.parquet")
)

ODD_EXCLUDED_DOMAIN = "SUSPICIOUS ACTIVITY"