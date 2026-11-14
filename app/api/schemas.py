"""Stable response envelopes for public API routes."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceResponse(BaseModel):
    source: str
    upstream_id: str
    source_url: str | None = None
    retrieved_at: datetime


class PageResponse[ItemT](BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ItemT]
    page: int
    page_size: int
    total: int
    retrieved_at: datetime
    freshness: Literal["current", "stale", "unknown"] = "current"


class AsteroidOrbitMapItem(BaseModel):
    neo_id: str = Field(pattern=r"^\d{1,20}$")
    name: str = Field(min_length=1, max_length=100)
    diameter_km: float | None = Field(default=None, gt=0, le=1000)
    potentially_hazardous: bool | None = None


class AsteroidOrbitMapRequest(BaseModel):
    objects: list[AsteroidOrbitMapItem] = Field(min_length=1, max_length=50)
    window_days: int = Field(default=7, ge=1, le=15)
