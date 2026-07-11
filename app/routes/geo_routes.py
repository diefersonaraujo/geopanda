"""
Rotas de API GeoJSON — endpoints para dados espaciais.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import geo_service, ibge_service

router = APIRouter(prefix="/api", tags=["geo"])


@router.get("/layers")
async def list_layers(db: AsyncSession = Depends(get_db)):
    """Lista todas as camadas geográficas disponíveis."""
    layers = await geo_service.get_available_layers()
    for layer in layers:
        stats = await geo_service.get_layer_stats(db, layer["id"])
        layer["total_features"] = stats["total_features"]
    return {"layers": layers}


@router.get("/geojson/{layer}")
async def get_geojson(
    layer: str,
    bbox: str | None = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    uf: str | None = Query(None, description="Código da UF para filtrar"),
    limit: int = Query(5000, ge=1, le=50000),
    db: AsyncSession = Depends(get_db),
):
    """Retorna GeoJSON de uma camada com filtros opcionais."""
    bbox_tuple = None
    if bbox:
        parts = [float(x.strip()) for x in bbox.split(",")]
        if len(parts) == 4:
            bbox_tuple = tuple(parts)

    geojson = await geo_service.get_layer_geojson(
        db, layer, bbox=bbox_tuple, state_code=uf, limit=limit
    )
    return geojson


@router.get("/feature/{layer}/{code}")
async def get_feature(
    layer: str,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """Retorna detalhes de uma feição específica."""
    feature = await geo_service.get_feature_detail(db, layer, code)
    if not feature:
        return {"error": "Feição não encontrada"}, 404
    return feature


@router.get("/states")
async def list_states(db: AsyncSession = Depends(get_db)):
    """Lista todos os estados."""
    states = await geo_service.get_states_for_layer(db)
    return {"states": states}


@router.get("/stats/{layer}")
async def layer_stats(layer: str, db: AsyncSession = Depends(get_db)):
    """Retorna estatísticas de uma camada."""
    stats = await geo_service.get_layer_stats(db, layer)
    return stats


@router.get("/ibge/populacao-estados")
async def populacao_estados(db: AsyncSession = Depends(get_db)):
    """Retorna GeoJSON com população por estado (join estados + municípios)."""
    return await ibge_service.get_populacao_por_estado(db)


@router.get("/ibge/municipios/{state_code}")
async def municipios_por_estado(state_code: str, db: AsyncSession = Depends(get_db)):
    """Retorna GeoJSON dos municípios de um estado."""
    return await ibge_service.get_municipios_por_estado(db, state_code)


@router.get("/ibge/setores/{municipio_code}")
async def setores_por_municipio(municipio_code: str, db: AsyncSession = Depends(get_db)):
    """Retorna GeoJSON dos setores censitários de um município."""
    return await ibge_service.get_setores_por_municipio(db, municipio_code)


@router.get("/ibge/mais-populosos")
async def mais_populosos(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Retorna os N municípios mais populosos do Brasil."""
    return await ibge_service.get_municipios_mais_populosos(db, limit)


@router.get("/ibge/buscar")
async def buscar_municipio(
    q: str = Query(..., min_length=2, description="Nome do município para buscar"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Busca municípios por nome (parcial)."""
    return await ibge_service.search_municipios(db, q, limit)
