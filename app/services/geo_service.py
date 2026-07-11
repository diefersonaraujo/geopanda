"""
Serviço de operações geoespaciais com GeoPandas.

Fornece funções para:
- Consultar PostGIS e retornar GeoJSON
- Transformar e filtrar dados espaciais
- Processar bounding box e interseções espaciais
"""

import json
from io import BytesIO
from pathlib import Path

import geopandas as gpd
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from shapely.geometry import box

from app.config import get_settings

settings = get_settings()

AVAILABLE_LAYERS = {
    "regioes": {
        "table": "regioes",
        "geometry_type": "MultiPolygon",
        "label_column": "nome",
        "code_column": "codigo_ibge",
    },
    "estados": {
        "table": "estados",
        "geometry_type": "MultiPolygon",
        "label_column": "nome",
        "code_column": "codigo_ibge",
        "extra_columns": ["uf"],
    },
    "mesorregioes": {
        "table": "mesorregioes",
        "geometry_type": "MultiPolygon",
        "label_column": "nome",
        "code_column": "codigo_ibge",
    },
    "microrregioes": {
        "table": "microrregioes",
        "geometry_type": "MultiPolygon",
        "label_column": "nome",
        "code_column": "codigo_ibge",
    },
    "municipios": {
        "table": "municipios",
        "geometry_type": "MultiPolygon",
        "label_column": "nome",
        "code_column": "codigo_ibge",
        "extra_columns": ["uf", "populacao", "area_km2", "ddd"],
    },
    "setores_censitarios": {
        "table": "setores_censitarios",
        "geometry_type": "Polygon",
        "label_column": "nome",
        "code_column": "codigo_ibge",
        "extra_columns": ["populacao", "domicilios", "area_km2"],
    },
}


async def get_available_layers() -> list[dict]:
    """Retorna lista de camadas disponíveis com metadados."""
    layers = []
    for key, config in AVAILABLE_LAYERS.items():
        layers.append({
            "id": key,
            "table": config["table"],
            "geometry_type": config["geometry_type"],
            "label_column": config["label_column"],
        })
    return layers


async def get_layer_geojson(
    db: AsyncSession,
    layer_name: str,
    bbox: tuple[float, float, float, float] | None = None,
    state_code: str | None = None,
    limit: int = 5000,
) -> dict:
    """
    Consulta PostGIS e retorna GeoJSON de uma camada.

    Args:
        db: sessão async do banco
        layer_name: nome da camada (ex: municipios)
        bbox: (min_lon, min_lat, max_lon, max_lat)
        state_code: código IBGE do estado para filtrar
        limit: limite de registros

    Returns:
        dict no formato GeoJSON FeatureCollection
    """
    config = AVAILABLE_LAYERS.get(layer_name)
    if not config:
        raise ValueError(f"Camada '{layer_name}' não existe. Disponíveis: {list(AVAILABLE_LAYERS.keys())}")

    table = config["table"]
    geom_col = "geom"
    select_cols = ["codigo_ibge", "nome"]

    if "extra_columns" in config:
        select_cols.extend(config["extra_columns"])

    col_str = ", ".join(select_cols)

    query = f"SELECT ST_AsGeoJSON(ST_Transform({geom_col}, 4326)) as geojson, {col_str} FROM {table}"
    conditions = []
    params = {}

    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox
        conditions.append(
            f"{geom_col} && ST_Transform(ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326), 4674)"
        )
        params.update({
            "min_lon": min_lon, "min_lat": min_lat,
            "max_lon": max_lon, "max_lat": max_lat,
        })

    if state_code and "estado_codigo" in _get_columns(table):
        conditions.append("estado_codigo = :state_code")
        params["state_code"] = state_code

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" LIMIT :limit"
    params["limit"] = limit

    result = await db.execute(text(query), params)
    rows = result.fetchall()

    features = []
    for row in rows:
        geojson_str = row[0]
        if not geojson_str:
            continue

        geometry = json.loads(geojson_str)
        properties = {}
        for i, col_name in enumerate(select_cols):
            properties[col_name] = row[i + 1]

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


async def get_feature_detail(
    db: AsyncSession,
    layer_name: str,
    feature_code: str,
) -> dict | None:
    """Retorna detalhes de uma feição específica pelo código IBGE."""
    config = AVAILABLE_LAYERS.get(layer_name)
    if not config:
        raise ValueError(f"Camada '{layer_name}' não existe.")

    table = config["table"]
    query = f"""
        SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) as geojson, *
        FROM {table}
        WHERE codigo_ibge = :code
        LIMIT 1
    """

    result = await db.execute(text(query), {"code": feature_code})
    row = result.fetchone()

    if not row:
        return None

    geojson_str = row[0]
    geometry = json.loads(geojson_str) if geojson_str else None

    # Pega todas as colunas (exceto geojson e geom)
    columns = await db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
    col_names = [c[0] for c in columns.fetchall()]

    properties = {}
    for i, col_name in enumerate(col_names):
        if col_name == "geom":
            continue
        val = row[i + 1]
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        properties[col_name] = val

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties,
    }


async def get_states_for_layer(db: AsyncSession) -> list[dict]:
    """Retorna lista de estados para filtros."""
    query = "SELECT codigo_ibge, nome, uf FROM estados ORDER BY nome"
    result = await db.execute(text(query))
    rows = result.fetchall()
    return [{"codigo_ibge": r[0], "nome": r[1], "uf": r[2]} for r in rows]


async def get_layer_stats(db: AsyncSession, layer_name: str) -> dict:
    """Retorna estatísticas básicas de uma camada."""
    config = AVAILABLE_LAYERS.get(layer_name)
    if not config:
        raise ValueError(f"Camada '{layer_name}' não existe.")

    table = config["table"]
    query = f"""
        SELECT
            COUNT(*) as total_features,
            SUM(CASE WHEN geom IS NOT NULL THEN 1 ELSE 0 END) as com_geom,
            ST_Extent(geom) as bounding_box
        FROM {table}
    """
    result = await db.execute(text(query))
    row = result.fetchone()

    return {
        "total_features": row[0],
        "features_with_geometry": row[1],
        "layer": layer_name,
    }


def _get_columns(table_name: str) -> list[str]:
    """Retorna colunas conhecidas de uma tabela."""
    for config in AVAILABLE_LAYERS.values():
        if config["table"] == table_name:
            cols = ["codigo_ibge", "nome"]
            if "extra_columns" in config:
                cols.extend(config["extra_columns"])
            return cols
    return ["codigo_ibge", "nome"]
