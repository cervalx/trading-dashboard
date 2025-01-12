from abc import ABC, abstractmethod
from typing import Optional, List
from pydantic.dataclasses import dataclass
from pydantic import model_validator, ValidationError
from loguru import logger
import pandas as pd


@dataclass
class PostData:
    likes: int
    comments: int
    id: str
    posted_date: str
    author: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    link: Optional[str] = None
    category: Optional[str] = None
    content_parsed: Optional[bool] = None
    ticker_notification_sent: Optional[str] = None
    found_tickers: Optional[str] = None

    @model_validator(mode="after")
    @classmethod
    def warn_if_null(cls, values):
        for key, value in values.__dict__.items():
            if value is None and key not in [
                "id",
                "ticker_notification_sent",
                "found_tickers",
                "content_parsed",
                "date",
            ]:
                logger.warning(f"{key} is null")
        return values


class PostRepository(ABC):
    @abstractmethod
    def get_credentials(self):
        pass

    @abstractmethod
    def create_post(self, **kwargs: PostData):
        pass

    @abstractmethod
    def post_exists(self, id: int) -> bool:
        pass

    @abstractmethod
    def get_feed(self, title: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def update_post(self, post: PostData) -> bool:
        pass

    @abstractmethod
    def get_unprocessed_posts(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def update_post_tags(self, id: str):
        pass
