CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS regioes (
    id SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(2) UNIQUE,
    nome VARCHAR(100),
    geom GEOMETRY(MULTIPOLYGON, 4674)
);

CREATE TABLE IF NOT EXISTS estados (
    id SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(2) UNIQUE,
    nome VARCHAR(100),
    uf VARCHAR(2),
    regiao_codigo VARCHAR(2),
    area_km2 FLOAT,
    geom GEOMETRY(MULTIPOLYGON, 4674)
);

CREATE TABLE IF NOT EXISTS mesorregioes (
    id SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(4) UNIQUE,
    nome VARCHAR(200),
    estado_codigo VARCHAR(2),
    area_km2 FLOAT,
    geom GEOMETRY(MULTIPOLYGON, 4674)
);

CREATE TABLE IF NOT EXISTS microrregioes (
    id SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(5) UNIQUE,
    nome VARCHAR(200),
    mesorregiao_codigo VARCHAR(4),
    area_km2 FLOAT,
    geom GEOMETRY(MULTIPOLYGON, 4674)
);

CREATE TABLE IF NOT EXISTS municipios (
    id SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(7) UNIQUE,
    nome VARCHAR(200),
    estado_codigo VARCHAR(2),
    mesorregiao_codigo VARCHAR(4),
    microrregiao_codigo VARCHAR(5),
    area_km2 FLOAT,
    populacao INTEGER,
    ddd VARCHAR(2),
    geom GEOMETRY(MULTIPOLYGON, 4674)
);

CREATE TABLE IF NOT EXISTS setores_censitarios (
    id SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(15) UNIQUE,
    municipio_codigo VARCHAR(7),
    codigo_estado VARCHAR(2),
    nome TEXT,
    populacao INTEGER,
    domicilios INTEGER,
    area_km2 FLOAT,
    geom GEOMETRY(POLYGON, 4674)
);

CREATE INDEX IF NOT EXISTS idx_regioes_geom ON regioes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_estados_geom ON estados USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_mesorregioes_geom ON mesorregioes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_microrregioes_geom ON microrregioes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_municipios_geom ON municipios USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_setores_geom ON setores_censitarios USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_municipios_estado ON municipios(estado_codigo);
CREATE INDEX IF NOT EXISTS idx_setores_municipio ON setores_censitarios(municipio_codigo);
