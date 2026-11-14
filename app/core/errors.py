"""Stable, safe application errors and RFC 9457-compatible responses."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AppError(Exception):
    code: str
    title: str
    detail: str
    status_code: int = 500
    retryable: bool = False
    upstream: str | None = None
    extra: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.detail


class NotFoundError(AppError):
    def __init__(self, detail: str = "The requested record was not found.") -> None:
        super().__init__("not_found", "Not found", detail, status_code=404)


class UpstreamError(AppError):
    def __init__(
        self,
        upstream: str,
        code: str = "upstream_unavailable",
        detail: str = "The data source is temporarily unavailable.",
        *,
        status_code: int = 503,
        retryable: bool = True,
    ) -> None:
        super().__init__(
            code, "Upstream service unavailable", detail, status_code, retryable, upstream
        )


class FeatureUnavailableError(AppError):
    def __init__(
        self, code: str = "feature_unavailable", detail: str = "This feature is not configured."
    ) -> None:
        super().__init__(code, "Feature unavailable", detail, status_code=503)
