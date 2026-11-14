"""JPL Small-Body Database and Horizons trajectory client."""

from __future__ import annotations

import math
import re
from datetime import date
from time import monotonic
from typing import Any

from app.clients.nasa_base import NASAClient
from app.core.errors import UpstreamError


class JPLSmallBodyClient:
    def __init__(self, transport: NASAClient, sbdb_base_url: str, horizons_base_url: str) -> None:
        self.transport = transport
        self.sbdb_base_url = sbdb_base_url.rstrip("/")
        self.horizons_base_url = horizons_base_url.rstrip("/")
        self._vectors_cache: dict[
            tuple[str, str, str, str], tuple[float, list[dict[str, Any]]]
        ] = {}

    async def trajectory(self, designation: str, start: date, end: date) -> dict[str, Any]:
        if (end - start).days < 1 or (end - start).days > 30:
            raise ValueError("Orbit window must be between 1 and 30 days.")
        designation_match = re.search(r"\(([^()]+)\)", designation)
        search_term = (
            designation_match.group(1).strip() if designation_match else designation.strip()
        )
        body, _, _ = await self.transport.get_json(
            "JPL_SBDB",
            f"{self.sbdb_base_url}/sbdb.api",
            params={"sstr": search_term, "phys-par": "1"},
            max_retries=1,
        )
        obj = body.get("object") if isinstance(body, dict) else None
        spkid = obj.get("spkid") if isinstance(obj, dict) else None
        if not isinstance(spkid, (str, int)) or not str(spkid).isdigit():
            raise UpstreamError(
                "JPL_SBDB",
                "object_not_found",
                "JPL could not resolve this asteroid to an orbital solution.",
                status_code=404,
                retryable=False,
            )

        points = await self.vectors(f"DES={spkid};", start, end, center="500@399")
        orbit = body.get("orbit", {}) if isinstance(body.get("orbit"), dict) else {}
        elements = orbit.get("elements", []) if isinstance(orbit.get("elements"), list) else []
        physical = body.get("phys_par", []) if isinstance(body.get("phys_par"), list) else []
        return {
            "object": obj,
            "orbital_elements": [
                self._element(item) for item in elements if isinstance(item, dict)
            ],
            "physical_parameters": [
                self._element(item) for item in physical if isinstance(item, dict)
            ],
            "points": points,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "center": "Earth geocenter",
            "reference_plane": "Ecliptic",
            "units": {"position": "AU", "distance": "AU"},
        }

    async def vectors_for_designation(
        self, designation: str, start: date, end: date, *, center: str
    ) -> list[dict[str, Any]]:
        match = re.search(r"\(([^()]+)\)", designation)
        search_term = match.group(1).strip() if match else designation.strip()
        if not re.fullmatch(r"[A-Za-z0-9 .'-]{1,50}", search_term):
            raise ValueError("Asteroid designation contains unsupported characters.")
        return await self.vectors(f"DES={search_term};", start, end, center=center)

    async def vectors(
        self, command: str, start: date, end: date, *, center: str
    ) -> list[dict[str, Any]]:
        if (end - start).days < 1 or (end - start).days > 30:
            raise ValueError("Orbit window must be between 1 and 30 days.")
        if command != "399" and not re.fullmatch(r"DES=[A-Za-z0-9 .'-]{1,60};", command):
            raise ValueError("Invalid Horizons target command.")
        cache_key = (command, start.isoformat(), end.isoformat(), center)
        cached = self._vectors_cache.get(cache_key)
        if cached and cached[0] > monotonic():
            return cached[1]
        payload, _, _ = await self.transport.get_json(
            "JPL_HORIZONS",
            f"{self.horizons_base_url}/api/horizons.api",
            params={
                "format": "json",
                "COMMAND": f"'{command}'",
                "OBJ_DATA": "NO",
                "MAKE_EPHEM": "YES",
                "EPHEM_TYPE": "VECTORS",
                "CENTER": center,
                "REF_PLANE": "ECLIPTIC",
                "OUT_UNITS": "AU-D",
                "VEC_TABLE": "2",
                "CSV_FORMAT": "YES",
                "START_TIME": start.isoformat(),
                "STOP_TIME": end.isoformat(),
                "STEP_SIZE": "6 h",
            },
            max_retries=1,
        )
        result = payload.get("result") if isinstance(payload, dict) else None
        if not isinstance(result, str) or "$$SOE" not in result or "$$EOE" not in result:
            raise UpstreamError(
                "JPL_HORIZONS",
                "upstream_schema_error",
                "JPL Horizons returned no trajectory for this date window.",
                status_code=502,
                retryable=False,
            )
        points = self._parse_vectors(result)
        if len(points) < 2:
            raise UpstreamError(
                "JPL_HORIZONS",
                "upstream_schema_error",
                "JPL Horizons returned an incomplete trajectory.",
                status_code=502,
                retryable=False,
            )
        if len(self._vectors_cache) >= 256:
            self._vectors_cache = {
                key: value for key, value in self._vectors_cache.items() if value[0] > monotonic()
            }
        self._vectors_cache[cache_key] = (monotonic() + 1800, points)
        return points

    @staticmethod
    def _element(item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ("name", "title", "value", "units", "sigma")}

    @staticmethod
    def _parse_vectors(result: str) -> list[dict[str, Any]]:
        block = result.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
        points: list[dict[str, Any]] = []
        for line in block.splitlines():
            fields = [part.strip().strip('"') for part in line.split(",")]
            if len(fields) < 5:
                continue
            try:
                jd = float(fields[0])
                x, y, z = (float(fields[i]) for i in (2, 3, 4))
            except (ValueError, IndexError):
                continue
            if not all(math.isfinite(value) for value in (jd, x, y, z)):
                continue
            points.append(
                {
                    "jd_tdb": jd,
                    "date": fields[1],
                    "x_au": x,
                    "y_au": y,
                    "z_au": z,
                    "distance_au": math.sqrt(x * x + y * y + z * z),
                }
            )
        return points
