"""The HTTP API."""

from fastapi import FastAPI

from incidentdesk import __version__
from incidentdesk.api import incidents, postmortems, services, timeline


def create_app() -> FastAPI:
    app = FastAPI(title="IncidentDesk", version=__version__)
    app.include_router(services.router)
    app.include_router(incidents.router)
    app.include_router(timeline.router)
    app.include_router(postmortems.router)
    return app


app = create_app()
