import polars as pl

from app.repositories import get_alert_repository


class AlertDataService:
    _repository = get_alert_repository()

    @classmethod
    def load_df(cls) -> pl.DataFrame:
        return cls._repository.load_data()