from pathlib import Path
import os

DATA_SOURCE = os.getenv("DATA_SOURCE", "detica_parquet")

ALERT_HEADER_PATH = Path(
    os.getenv("ALERT_HEADER_PATH", "/parquet/current/DETICA/alert_header.parquet")
)

WORKFLOW_STATUSES_PATH = Path(
    os.getenv("WORKFLOW_STATUSES_PATH", "/parquet/current/DETICA/workflow_statuses.parquet")
)

ODD_EXCLUDED_DOMAIN = "SUSPICIOUS ACTIVITY"