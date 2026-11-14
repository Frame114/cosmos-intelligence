"""FastAPI dependencies for API services and integrations."""

from fastapi import Request

from app.clients.registry import NASAClients
from app.core.errors import FeatureUnavailableError


def get_nasa_clients(request: Request) -> NASAClients:
    """Return the application-scoped NASA client registry."""

    clients = getattr(request.app.state, "nasa_clients", None)
    if not isinstance(clients, NASAClients):
        raise FeatureUnavailableError(
            "nasa_clients_unavailable", "NASA integrations are not available."
        )
    return clients
