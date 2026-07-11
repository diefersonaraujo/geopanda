"""
GeoPanda SIG — Aplicação principal FastAPI

Sistema de Informação Geográfica para visualização de dados do IBGE
com GeoPandas, PostGIS e Leaflet.js.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.routes import geo_routes, pages

settings = get_settings()

static_dir = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("GeoPanda SIG iniciado!")
    yield
    print("GeoPanda SIG encerrado.")


app = FastAPI(
    title="GeoPanda SIG",
    description="Sistema de Informação Geográfica — Visualização de dados IBGE com GeoPandas",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(geo_routes.router)
app.include_router(pages.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
    )
