"""The configured NASA adapters available to request handlers."""

from dataclasses import dataclass

from app.clients.gdelt import GDELTClient
from app.clients.jpl_ssd import JPLSmallBodyClient
from app.clients.nasa_apod import NasaApodClient
from app.clients.nasa_donki import DONKIClient
from app.clients.nasa_eonet import EONETClient
from app.clients.nasa_media import NASAMediaClient
from app.clients.nasa_neows import NeoWsClient


@dataclass(frozen=True, slots=True)
class NASAClients:
    apod: NasaApodClient
    neows: NeoWsClient
    donki: DONKIClient
    eonet: EONETClient
    media: NASAMediaClient
    jpl: JPLSmallBodyClient | None = None
    gdelt: GDELTClient | None = None
