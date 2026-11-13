"""Validated model for one item from NASA's APOD Basic feed."""

from datetime import date

from pydantic import BaseModel, ConfigDict, HttpUrl

from fastapi import APIRouter

router = APIRouter(prefix="/nasa", tags=["nasa"])  # Create a router to hold the APOD model's endpoints.


class ApodRecord(BaseModel):
    """Represent the APOD fields used by Cosmos Intelligence."""

    # NASA may add fields; this model keeps the fields we use and ignores the rest.
    model_config = ConfigDict(extra="ignore")

    date: date
    post_id: int
    title: str
    permalink: HttpUrl
    media_type: str
    explanation: str
    credit: str | None = None
    copyright: str | None = None
    alt: str | None = None
    url: HttpUrl
    hdurl: str | None = None
