"""FastAPI application entry point.

The first API slice is intentionally limited to service health. NASA integration
will be added after its live response contract has been inspected and tested.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Cosmos Intelligence API",
    description="Scientific data integration and intelligence platform.",
    version="0.1.0",
)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    """Return a lightweight process health response."""
    return {"status": "ok", "service": "cosmos-intelligence"}
