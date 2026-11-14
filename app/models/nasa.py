"""Normalized provider-facing models for external NASA payloads."""

from datetime import date, datetime
from typing import Any

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class NASARecord(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)


class CloseApproach(BaseModel):
    close_approach_date: date
    close_approach_date_full: str | None = None
    epoch_date_close_approach: int | None = None
    relative_velocity: dict[str, str] = Field(default_factory=dict)
    miss_distance: dict[str, str] = Field(default_factory=dict)
    orbiting_body: str = "Earth"


class NeoObject(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    id: str
    neo_reference_id: str | None = None
    name: str
    absolute_magnitude_h: float | None = None
    estimated_diameter: dict[str, dict[str, float]] = Field(default_factory=dict)
    is_potentially_hazardous_asteroid: bool | None = None
    is_sentry_object: bool | None = None
    close_approach_data: list[CloseApproach] = Field(default_factory=list)
    nasa_jpl_url: AnyUrl | None = None


class EONETGeometry(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    date: datetime | None = None
    type: str
    coordinates: Any
    magnitudeValue: float | None = None
    magnitudeUnit: str | None = None


class EONETEvent(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    id: str
    title: str
    description: str | None = None
    link: AnyUrl | None = None
    closed: datetime | None = None
    categories: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    geometry: list[EONETGeometry] = Field(default_factory=list)


class NASACollectionItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: list[dict[str, Any]] = Field(default_factory=list)
    links: list[dict[str, Any]] = Field(default_factory=list)


class NASACollection(BaseModel):
    items: list[NASACollectionItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    links: list[dict[str, Any]] = Field(default_factory=list)


class NASAImageSearchResponse(BaseModel):
    collection: NASACollection
