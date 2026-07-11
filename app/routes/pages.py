"""
Rotas de páginas — serve templates HTML com Leaflet.
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

router = APIRouter(tags=["pages"])


@router.get("/")
async def index(request: Request):
    """Página principal com mapa Leaflet."""
    return templates.TemplateResponse("index.html", {"request": request})
