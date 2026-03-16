from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_SOURCE = os.getenv("DATA_SOURCE", "csv")   # change manually later: "csv", "parquet", or "oracle"

CSV_PATH = BASE_DIR / "odd_alerts.csv"
PARQUET_PATH = BASE_DIR / "odd_alerts.parquet"

ORACLE_CONFIG = {
    "username": os.getenv("ORACLE_USERNAME", ""),
    "password": os.getenv("ORACLE_PASSWORD", ""),
    "host": os.getenv("ORACLE_HOST", ""),
    "port": os.getenv("ORACLE_PORT", ""),
    "service_name": os.getenv("ORACLE_SERVICE_NAME", ""),
}