from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import router
from app.config import settings
from app.services.catalog_service import CatalogService


def create_app(database_path=None) -> FastAPI:
    app = FastAPI(title="Anime Atlas")

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
    )

    app.state.catalog = CatalogService(
        database_path or settings.database_path
    )

    app.mount(
        "/static",
        StaticFiles(directory="app/static"),
        name="static",
    )

    app.include_router(router)

    return app


app = create_app()