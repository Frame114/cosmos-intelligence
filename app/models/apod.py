"""Validated APOD Basic response fields used by the product API."""

from datetime import date

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class ApodRecord(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    date: date
    post_id: int | None = None
    title: str = Field(min_length=1, max_length=500)
    permalink: AnyUrl | None = None
    media_type: str = Field(min_length=1, max_length=40)
    explanation: str = ""
    credit: str | None = None
    copyright: str | None = None
    alt: str | None = None
    url: AnyUrl | None = None
    hdurl: AnyUrl | None = None
    basic_html: str | None = None
    basic_html_url: AnyUrl | None = None

    @property
    def source_url(self) -> str:
        return str(self.permalink or self.url or "https://apod.nasa.gov/")

    @property
    def media_url(self) -> str | None:
        return str(self.hdurl or self.url) if (self.hdurl or self.url) else None
