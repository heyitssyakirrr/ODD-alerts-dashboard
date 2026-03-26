from abc import ABC, abstractmethod
import polars as pl


class BaseAlertRepository(ABC):
    @abstractmethod
    def load_data(self) -> pl.DataFrame:
        """Return alert data in normalized dashboard shape."""
        raise NotImplementedError