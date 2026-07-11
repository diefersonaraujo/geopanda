"""
Serviço de consultas IBGE — agregações, joins, filtros temáticos.
"""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_populacao_por_estado(db: AsyncSession) -> dict:
    """Retorna população total por estado em formato GeoJSON."""
    query = """
        SELECT ST_AsGeoJSON(ST_Transform(e.geom, 4326)) as geojson,
               e.nome as estado,
               e.uf,
               COALESCE(SUM(m.populacao), 0) as populacao_total,
               COUNT(m.codigo_ibge) as num_municipios
        FROM estados e
        LEFT JOIN municipios m ON m.estado_codigo = e.codigo_ibge
        GROUP BY e.id, e.nome, e.uf, e.geom
        ORDER BY e.nome
    """
    result = await db.execute(text(query))
    rows = result.fetchall()

    features = []
    for row in rows:
        geojson = json.loads(row[0]) if row[0] else None
        features.append({
            "type": "Feature",
            "geometry": geojson,
            "properties": {
                "estado": row[1],
                "uf": row[2],
                "populacao_total": int(row[3]),
                "num_municipios": int(row[4]),
            },
        })

    return {"type": "FeatureCollection", "features": features}


async def get_municipios_por_estado(db: AsyncSession, state_code: str) -> dict:
    """Retorna municípios de um estado em formato GeoJSON."""
    query = """
        SELECT ST_AsGeoJSON(ST_Transform(m.geom, 4326)) as geojson,
               m.codigo_ibge,
               m.nome,
               m.populacao,
               m.area_km2,
               m.ddd
        FROM municipios m
        WHERE m.estado_codigo = :state_code
        ORDER BY m.nome
    """
    result = await db.execute(text(query), {"state_code": state_code})
    rows = result.fetchall()

    features = []
    for row in rows:
        geojson = json.loads(row[0]) if row[0] else None
        features.append({
            "type": "Feature",
            "geometry": geojson,
            "properties": {
                "codigo_ibge": row[1],
                "nome": row[2],
                "populacao": int(row[3]) if row[3] else None,
                "area_km2": float(row[4]) if row[4] else None,
                "ddd": row[5],
            },
        })

    return {"type": "FeatureCollection", "features": features}


async def get_setores_por_municipio(db: AsyncSession, municipio_code: str) -> dict:
    """Retorna setores censitários de um município."""
    query = """
        SELECT ST_AsGeoJSON(ST_Transform(s.geom, 4326)) as geojson,
               s.codigo_ibge,
               s.populacao,
               s.domicilios,
               s.area_km2
        FROM setores_censitarios s
        WHERE s.municipio_codigo = :municipio_code
        ORDER BY s.codigo_ibge
    """
    result = await db.execute(text(query), {"municipio_code": municipio_code})
    rows = result.fetchall()

    features = []
    for row in rows:
        geojson = json.loads(row[0]) if row[0] else None
        features.append({
            "type": "Feature",
            "geometry": geojson,
            "properties": {
                "codigo_ibge": row[1],
                "populacao": int(row[2]) if row[2] else None,
                "domicilios": int(row[3]) if row[3] else None,
                "area_km2": float(row[4]) if row[4] else None,
            },
        })

    return {"type": "FeatureCollection", "features": features}


async def get_municipios_mais_populosos(db: AsyncSession, limit: int = 20) -> dict:
    """Retorna os N municípios mais populosos com geometria."""
    query = """
        SELECT ST_AsGeoJSON(ST_Transform(m.geom, 4326)) as geojson,
               m.codigo_ibge,
               m.nome,
               m.populacao,
               m.area_km2,
               e.nome as estado,
               e.uf
        FROM municipios m
        JOIN estados e ON e.codigo_ibge = m.estado_codigo
        WHERE m.populacao IS NOT NULL
        ORDER BY m.populacao DESC
        LIMIT :limit
    """
    result = await db.execute(text(query), {"limit": limit})
    rows = result.fetchall()

    features = []
    for row in rows:
        geojson = json.loads(row[0]) if row[0] else None
        features.append({
            "type": "Feature",
            "geometry": geojson,
            "properties": {
                "codigo_ibge": row[1],
                "nome": row[2],
                "populacao": int(row[3]) if row[3] else None,
                "area_km2": float(row[4]) if row[4] else None,
                "estado": row[5],
                "uf": row[6],
            },
        })

    return {"type": "FeatureCollection", "features": features}


async def search_municipios(db: AsyncSession, query_text: str, limit: int = 20) -> dict:
    """Busca municípios por nome (parcial, case-insensitive)."""
    query = """
        SELECT ST_AsGeoJSON(ST_Transform(m.geom, 4326)) as geojson,
               m.codigo_ibge,
               m.nome,
               m.populacao,
               e.nome as estado,
               e.uf
        FROM municipios m
        JOIN estados e ON e.codigo_ibge = m.estado_codigo
        WHERE m.nome ILIKE :search
        ORDER BY m.populacao DESC NULLS LAST
        LIMIT :limit
    """
    result = await db.execute(text(query), {"search": f"%{query_text}%", "limit": limit})
    rows = result.fetchall()

    features = []
    for row in rows:
        geojson = json.loads(row[0]) if row[0] else None
        features.append({
            "type": "Feature",
            "geometry": geojson,
            "properties": {
                "codigo_ibge": row[1],
                "nome": row[2],
                "populacao": int(row[3]) if row[3] else None,
                "estado": row[4],
                "uf": row[5],
            },
        })

    return {"type": "FeatureCollection", "features": features}
