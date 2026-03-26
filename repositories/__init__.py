from config.settings import DATA_SOURCE
from repositories.detica_parquet_repostiory import DeticaParquetAlertRepository

def get_alert_repository():
    if DATA_SOURCE == "detica_parquet":
        return DeticaParquetAlertRepository()

    raise ValueError(f"Unsupported data source: {DATA_SOURCE}")