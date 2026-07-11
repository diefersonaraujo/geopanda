# Design — GeoPanda SIG

## Visão Geral

Sistema de Informação Geográfica (SIG) para visualização e análise de dados espaciais do IBGE, construído com Python, PostGIS e Leaflet.js.

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Browser)                 │
│  ┌───────────┐  ┌─────────────┐  ┌───────────────┐ │
│  │ Leaflet.js │  │ Sidebar UI  │  │  Search/Filter │ │
│  └─────┬─────┘  └──────┬──────┘  └───────┬───────┘ │
│        └────────────────┼─────────────────┘         │
│                         │ fetch() / GeoJSON         │
├─────────────────────────┼───────────────────────────┤
│                   Backend (FastAPI)                  │
│  ┌─────────────┐  ┌─────┴─────┐  ┌──────────────┐  │
│  │  Routes      │  │ Services  │  │  Models/ORM   │  │
│  │  /api/*      │──│ GeoPandas │──│ GeoAlchemy2   │  │
│  │  /pages      │  │ IBGE svc  │  │               │  │
│  └──────────────┘  └───────────┘  └───────┬──────┘  │
├───────────────────────────────────────────┼─────────┤
│                   Database                 │         │
│  ┌──────────────────────────────────────┐ │         │
│  │         PostgreSQL + PostGIS          │─┘         │
│  │  regioes | estados | municipios      │           │
│  │  mesorregioes | microrregioes        │           │
│  │  setores_censitarios                 │           │
│  │  (índices GIST espaciais)            │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

## Camadas do Sistema

### 1. Apresentação (Frontend)

- **Leaflet.js** renderiza mapas interativos no browser
- **Tema dark** com sidebar de controles
- Camadas toggleáveis via checkboxes
- Filtros por estado e busca por município
- Popups interativos com informações das feições
- Temas de visualização: padrão, população, área

### 2. API (Backend)

- **FastAPI** expõe endpoints REST
- Geração automática de documentação Swagger
- Endpoints para GeoJSON por camada, filtros espaciais e buscas
- Async/await com SQLAlchemy assíncrono

### 3. Serviços (Business Logic)

- **geo_service.py**: consultas PostGIS, conversão para GeoJSON, filtros bbox
- **ibge_service.py**: joins, agregações, buscas temáticas

### 4. Persistência (Database)

- **PostGIS** com extensões espaciais
- Índices GIST para consultas rápidas
- Reprojeção para SIRGAS 2000 (EPSG:4674)

## Camadas Geográficas (IBGE)

| Camada | Tabela | Nível | Geometria |
|--------|--------|-------|-----------|
| Regiões | regioes | Brasil | MultiPolygon |
| Estados | estados | UF | MultiPolygon |
| Mesorregiões | mesorregioes | UF/Região | MultiPolygon |
| Microrregiões | microrregioes | UF/Mesorregião | MultiPolygon |
| Municípios | municipios | Município | MultiPolygon |
| Setores Censitários | setores_censitarios | Município | Polygon |

## Fluxo de Dados

```
IBGE (download) → Shapefiles → GeoPandas → PostGIS
                                                   │
                                                   ▼
                                          FastAPI /api/geojson
                                                   │
                                                   ▔▔▔
                                                   │ fetch()
                                                   ▼
                                            Leaflet.js (mapa)
```

## Decisões de Design

1. **FastAPI sobre Flask**: performance async nativa, documentação Swagger automática
2. **Leaflet.js puro sobre Folium**: mais controle no frontend, interatividade dinâmica
3. **PostGIS sobre SQLite/SpatiaLite**: suporte a múltiplas conexões, escalabilidade
4. **GeoAlchemy2**: ORM nativo para operações espaciais no SQLAlchemy
5. **Tema dark**: melhor visualização de mapas, reduz fadiga visual
