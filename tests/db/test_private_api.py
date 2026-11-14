"""PostgreSQL-backed user ownership, comparison, and stored summary route checks."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_nasa_clients
from app.clients.registry import NASAClients
from app.core.auth import UserContext, require_admin
from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.db.models import AIReport, DataSource, IngestionJob, PromptVersion
from app.main import create_app
from app.models.apod import ApodRecord
from app.models.nasa import NeoObject

TEST_DATABASE_URL = os.environ.get("COSMOS_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="No disposable PostgreSQL URL configured."
)


def _application() -> FastAPI:
    settings = Settings(
        _env_file=None,
        app_env="development",
        dev_auth_enabled=True,
        database_url=TEST_DATABASE_URL,
    )
    application = create_app(settings)

    @application.post("/_integration/report/{subject}")
    async def seed_report(
        subject: str,
        session: AsyncSession = Depends(get_db_session),
    ) -> dict[str, str]:
        from sqlalchemy import select

        from app.db.models import UserAccount

        user = await session.scalar(select(UserAccount).where(UserAccount.oidc_subject == subject))
        assert user is not None
        prompt = PromptVersion(
            name="test-report",
            version=f"v-{uuid4()}",
            system_template="Test-only prompt.",
            checksum="a" * 64,
            active=False,
        )
        session.add(prompt)
        await session.flush()
        report = AIReport(
            user_id=user.id,
            prompt_version_id=prompt.id,
            title="Private report",
            question="Test-only question",
            structured_answer={"summary": "Fixture report."},
            model_id="test-fixture",
        )
        session.add(report)
        await session.flush()
        return {"id": str(report.id)}

    @application.post("/_integration/failed-job")
    async def seed_failed_job(session: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        await session.execute(
            pg_insert(DataSource)
            .values(code="APOD", display_name="Test APOD", base_host="science.nasa.gov")
            .on_conflict_do_nothing(index_elements=[DataSource.code])
        )
        now = datetime.now(UTC)
        job = IngestionJob(
            source_code="APOD",
            job_type="apod_daily",
            state="failed",
            attempts=5,
            next_run_at=now,
            finished_at=now,
            safe_error_code="upstream_timeout",
        )
        session.add(job)
        await session.flush()
        return {"id": str(job.id)}

    return application


def _clients(
    *,
    apod: object | None = None,
    neows: object | None = None,
    donki: object | None = None,
    media: object | None = None,
) -> NASAClients:
    return NASAClients(
        apod=apod,  # type: ignore[arg-type]
        neows=neows,  # type: ignore[arg-type]
        donki=donki,  # type: ignore[arg-type]
        eonet=None,  # type: ignore[arg-type]
        media=media,  # type: ignore[arg-type]
    )


def test_saved_records_and_conversations_are_owner_scoped() -> None:
    application = _application()

    class FakeApodClient:
        async def get_by_date(self, _apod_date: date) -> ApodRecord:
            return ApodRecord(
                date=date(2026, 11, 12),
                post_id=9912,
                title="Private flow fixture",
                media_type="image",
                explanation="A test record.",
                permalink="https://science.nasa.gov/astronomy/apod/fixture/",
                url="https://images.nasa.gov/fixture.jpg",
            )

    application.dependency_overrides[get_nasa_clients] = lambda: _clients(apod=FakeApodClient())
    owner_subject = f"ownership-test-owner-{uuid4().hex}"
    other_subject = f"ownership-test-other-{uuid4().hex}"
    owner = {"X-Dev-User": owner_subject}
    other = {"X-Dev-User": other_subject}

    with TestClient(application) as client:
        source = client.get("/api/v1/astronomy/apod/2026-11-12")
        account = client.get("/api/v1/auth/me", headers=owner)
        saved = client.post(
            "/api/v1/saved-records",
            headers=owner,
            json={"source_code": "APOD", "upstream_id": "2026-11-12"},
        )
        duplicate = client.post(
            "/api/v1/saved-records",
            headers=owner,
            json={"source_code": "APOD", "upstream_id": "2026-11-12"},
        )
        owner_list = client.get("/api/v1/saved-records", headers=owner)
        other_list = client.get("/api/v1/saved-records", headers=other)
        stranger_delete = client.delete(
            f"/api/v1/saved-records/{saved.json()['id']}", headers=other
        )
        owner_delete = client.delete(f"/api/v1/saved-records/{saved.json()['id']}", headers=owner)

        conversation = client.post(
            "/api/v1/research/conversations", headers=owner, json={"title": "Owned thread"}
        )
        hidden_conversation = client.get(
            f"/api/v1/research/conversations/{conversation.json()['id']}", headers=other
        )
        owner_conversation = client.get(
            f"/api/v1/research/conversations/{conversation.json()['id']}", headers=owner
        )
        message = client.post(
            f"/api/v1/research/conversations/{conversation.json()['id']}/messages",
            headers=owner,
            json={"content": "This must not be sent to a provider."},
        )
        stranger_delete_conversation = client.delete(
            f"/api/v1/research/conversations/{conversation.json()['id']}", headers=other
        )
        owner_delete_conversation = client.delete(
            f"/api/v1/research/conversations/{conversation.json()['id']}", headers=owner
        )

    assert source.status_code == account.status_code == 200
    assert saved.status_code == 201
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == saved.json()["id"]
    assert saved.json()["record"]["source_code"] == "APOD"
    assert owner_list.json()["total"] == 1
    assert other_list.json()["total"] == 0
    assert stranger_delete.status_code == 404
    assert owner_delete.status_code == 204
    assert conversation.status_code == 201
    assert hidden_conversation.status_code == 404
    assert owner_conversation.status_code == 200
    assert owner_conversation.json()["messages"] == []
    assert message.status_code == 503
    assert message.json()["code"] == "assistant_policy_unavailable"
    assert stranger_delete_conversation.status_code == 404
    assert owner_delete_conversation.status_code == 204


def test_report_access_and_delete_are_owner_scoped() -> None:
    application = _application()
    owner_subject = f"report-test-owner-{uuid4().hex}"
    owner = {"X-Dev-User": owner_subject}
    other = {"X-Dev-User": f"report-test-other-{uuid4().hex}"}

    with TestClient(application) as client:
        client.get("/api/v1/auth/me", headers=owner)
        client.get("/api/v1/auth/me", headers=other)
        seeded = client.post(f"/_integration/report/{owner_subject}")
        report_id = seeded.json()["id"]
        owner_list = client.get("/api/v1/reports", headers=owner)
        other_list = client.get("/api/v1/reports", headers=other)
        hidden = client.get(f"/api/v1/reports/{report_id}", headers=other)
        stranger_delete = client.delete(f"/api/v1/reports/{report_id}", headers=other)
        owner_delete = client.delete(f"/api/v1/reports/{report_id}", headers=owner)

    assert seeded.status_code == 200
    assert owner_list.json()["total"] >= 1
    assert any(report["id"] == report_id for report in owner_list.json()["items"])
    assert all(report["id"] != report_id for report in other_list.json()["items"])
    assert hidden.status_code == stranger_delete.status_code == 404
    assert owner_delete.status_code == 204


def test_asteroid_comparison_keeps_missing_values_and_units_explicit() -> None:
    application = _application()

    class FakeNeoWsClient:
        async def get(self, neo_id: str) -> NeoObject:
            if neo_id == "10001":
                return NeoObject(
                    id=neo_id,
                    name="Object with estimates",
                    absolute_magnitude_h=21.1,
                    estimated_diameter={"kilometers": {"estimated_diameter_min": 0.1}},
                    close_approach_data=[],
                )
            return NeoObject(
                id=neo_id,
                name="Object with missing estimates",
                absolute_magnitude_h=None,
                estimated_diameter={},
                close_approach_data=[],
            )

    application.dependency_overrides[get_nasa_clients] = lambda: _clients(neows=FakeNeoWsClient())
    subject = f"compare-test-user-{uuid4().hex}"
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/asteroids/compare",
            headers={"X-Dev-User": subject},
            json={"neo_ids": ["10001", "10002"]},
        )
        too_few = client.post(
            "/api/v1/asteroids/compare",
            headers={"X-Dev-User": subject},
            json={"neo_ids": ["10001"]},
        )
        duplicates = client.post(
            "/api/v1/asteroids/compare",
            headers={"X-Dev-User": subject},
            json={"neo_ids": ["10001", "10001"]},
        )

    assert response.status_code == 200
    assert response.json()["units"] == {
        "diameter": "km",
        "relative_velocity": "km/s",
        "miss_distance": "km",
    }
    assert response.json()["objects"][0]["estimated_diameter_km"] == {"min": 0.1, "max": None}
    assert response.json()["objects"][1]["absolute_magnitude"] is None
    assert "not an impact prediction" in response.json()["disclaimer"]
    assert too_few.status_code == 422
    assert duplicates.status_code == 422


def test_admin_routes_require_explicit_admin_role() -> None:
    application = _application()
    with TestClient(application) as client:
        forbidden = client.get(
            "/api/v1/admin/sources",
            headers={"X-Dev-User": f"regular-local-user-{uuid4().hex}"},
        )

    assert forbidden.status_code == 403


def test_admin_sources_response_contains_no_raw_user_content() -> None:
    application = _application()
    application.dependency_overrides[require_admin] = lambda: UserContext(
        "local-admin-test", frozenset(), frozenset({"cosmos_admin"})
    )

    with TestClient(application) as client:
        response = client.get("/api/v1/admin/sources")

    assert response.status_code == 200
    assert "items" in response.json()
    assert all("raw_payload" not in item for item in response.json()["items"])


def test_report_creation_remains_blocked_without_approval() -> None:
    application = _application()
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/reports",
            headers={"X-Dev-User": f"report-gate-user-{uuid4().hex}"},
            json={"question": "Do not send this to a provider."},
        )

    assert response.status_code == 503
    assert response.json()["code"] == "assistant_policy_unavailable"


def test_space_weather_summary_reports_stored_donki_counts() -> None:
    application = _application()

    class FakeDONKIClient:
        async def events(self, _event_type: str, _start: date, _end: date) -> list[dict[str, Any]]:
            return [
                {
                    "activityID": f"SUMMARY-{uuid4().hex}",
                    "type": "CME",
                    "startTime": "2026-11-13T11:30:00Z",
                    "messageBody": "A fixture-only CME summary.",
                    "link": "https://ccmc.gsfc.nasa.gov/DONKI/view/CME/summary-fixture",
                }
            ]

    application.dependency_overrides[get_nasa_clients] = lambda: _clients(donki=FakeDONKIClient())
    with TestClient(application) as client:
        loaded = client.get(
            "/api/v1/space-weather/events",
            params={"type": "CME", "start_date": "2026-11-13", "end_date": "2026-11-13"},
        )
        summary = client.get(
            "/api/v1/space-weather/summary",
            params={"start_date": "2026-11-13", "end_date": "2026-11-13"},
        )
        event_id = loaded.json()["items"][0]["provenance"]["upstream_id"]
        detail = client.get(f"/api/v1/space-weather/events/{event_id}")

    assert loaded.status_code == 200
    assert summary.status_code == 200
    assert summary.json()["total"] >= 1
    assert summary.json()["by_type"]["CME"] >= 1
    assert "Stored DONKI records only" in summary.json()["coverage"]
    assert detail.status_code == 200
    assert detail.json()["summary"] == "A fixture-only CME summary."
    assert detail.json()["provenance"]["upstream_id"] == event_id


def test_nasa_media_detail_loads_and_persists_one_item() -> None:
    application = _application()
    nasa_id = f"DETAIL-{uuid4().hex}"

    class FakeMediaClient:
        async def search(self, **_kwargs: object) -> dict[str, object]:
            return {
                "collection": {
                    "items": [
                        {
                            "data": [
                                {
                                    "nasa_id": nasa_id,
                                    "title": "Media detail fixture",
                                    "media_type": "image",
                                    "description": "A test-only media description.",
                                    "date_created": "2026-11-13T00:00:00Z",
                                    "photographer": "Fixture creator",
                                    "rights": "Check original item terms.",
                                }
                            ],
                            "links": [
                                {
                                    "rel": "preview",
                                    "href": "https://images.nasa.gov/preview/detail.jpg",
                                }
                            ],
                        }
                    ]
                }
            }

    application.dependency_overrides[get_nasa_clients] = lambda: _clients(media=FakeMediaClient())
    with TestClient(application) as client:
        response = client.get(f"/api/v1/media/{nasa_id}")

    assert response.status_code == 200
    assert response.json()["nasa_id"] == nasa_id
    assert response.json()["rights_note"] == "Check original item terms."
    assert response.json()["provenance"]["source"] == "NASA_MEDIA"
