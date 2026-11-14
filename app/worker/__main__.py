"""Launch the long-running NASA ingestion worker process."""

from __future__ import annotations

import asyncio
import logging
import signal

import httpx

from app.clients.jpl_ssd import JPLSmallBodyClient
from app.clients.nasa_apod import NasaApodClient
from app.clients.nasa_base import NASAClient
from app.clients.nasa_donki import DONKIClient
from app.clients.nasa_eonet import EONETClient
from app.clients.nasa_media import NASAMediaClient
from app.clients.nasa_neows import NeoWsClient
from app.clients.registry import NASAClients
from app.core.config import get_settings
from app.db.session import create_engine, get_sessionmaker
from app.worker.runtime import IngestionWorker, create_worker_id


async def _run() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signal_name, stop_event.set)

    engine = create_engine(settings.database_url_value, pool_size=settings.db_pool_size)
    timeout = httpx.Timeout(settings.nasa_api_timeout_seconds)
    limits = httpx.Limits(
        max_connections=settings.nasa_max_concurrency,
        max_keepalive_connections=settings.nasa_max_concurrency,
    )
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=False,
        ) as http_client:
            transport = NASAClient(
                http_client,
                max_retries=settings.nasa_max_retries,
                max_response_bytes=settings.nasa_max_response_bytes,
                api_key=settings.nasa_api_key_value,
            )
            clients = NASAClients(
                apod=NasaApodClient(transport, settings.apod_base_url),
                neows=NeoWsClient(transport, settings.neows_base_url),
                donki=DONKIClient(transport, settings.donki_base_url),
                eonet=EONETClient(transport, settings.eonet_base_url),
                media=NASAMediaClient(transport, settings.nasa_media_base_url),
                jpl=JPLSmallBodyClient(
                    transport, settings.jpl_ssd_base_url, settings.jpl_horizons_base_url
                ),
            )
            worker = IngestionWorker(
                session_factory=get_sessionmaker(engine),
                clients=clients,
                worker_id=create_worker_id(),
                poll_interval_seconds=settings.worker_poll_interval_seconds,
                lease_seconds=settings.worker_lease_seconds,
                schedules_enabled=settings.worker_schedules_enabled,
            )
            logging.getLogger("cosmos.worker").info("Worker started")
            await worker.run(stop_event)
            logging.getLogger("cosmos.worker").info("Worker stopped")
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
