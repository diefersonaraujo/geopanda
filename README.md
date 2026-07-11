# GeoPanda SIG

Sistema de Informação Geográfica para visualização de dados do IBGE com GeoPandas, PostGIS e Leaflet.js.

## Estrutura

```
geopanda/
├── app/                          # Aplicação FastAPI
│   ├── main.py                   # Entry point
│   ├── config.py                 # Configurações (.env)
│   ├── database.py               # Engine async PostGIS
│   ├── models/spatial.py         # ORM GeoAlchemy2
│   ├── routes/
│   │   ├── geo_routes.py         # API REST (GeoJSON, layers, buscas)
│   │   └── pages.py              # Serve HTML
│   ├── services/
│   │   ├── geo_service.py        # Consultas PostGIS → GeoJSON
│   │   └── ibge_service.py       # Agregações IBGE
│   ├── static/css/style.css      # Tema dark
│   ├── static/js/map.js          # Leaflet.js completo
│   └── templates/                # HTML (Leaflet + sidebar)
├── scripts/
│   ├── setup_postgis.sql         # Schema + índices GIST
│   ├── download_ibge.py          # Baixa malhas do IBGE
│   └── load_ibge.py              # Shapefile → PostGIS
├── notebooks/exploracao_ibge.ipynb
├── .env                          # Variáveis de ambiente
├── .gitignore
└── requirements.txt
```

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + Uvicorn |
| Geo Processing | GeoPandas, Shapely, Fiona, pyproj |
| Banco Espacial | PostgreSQL + PostGIS (SQLAlchemy + GeoAlchemy2) |
| Frontend Mapa | Leaflet.js (client-side, consome GeoJSON da API) |

## Requisitos

- Python 3.12+
- PostgreSQL com PostGIS habilitado

## Configuração

1. Criar o banco de dados:

```bash
createdb -U postgres geopanda
```

2. Editar `.env` com suas credenciais:

```
DATABASE_URL=postgresql+asyncpg://postgres:sua_senha@localhost:5432/geopanda
DATABASE_URL_SYNC=postgresql://postgres:sua_senha@localhost:5432/geopanda
```

3. Instalar dependências (já configurado no `.venv`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

### Baixar dados do IBGE

```bash
# Baixar malhas territoriais (estados, municípios, etc.)
.venv/bin/python scripts/download_ibge.py --escala estados
.venv/bin/python scripts/download_ibge.py --escala municipios
.venv/bin/python scripts/download_ibge.py --escala setores_censitarios
.venv/bin/python scripts/download_ibge.py --escala mesorregioes
.venv/bin/python scripts/download_ibge.py --escala microrregioes

# Baixar apenas uma UF específica
.venv/bin/python scripts/download_ibge.py --escala municipios --uf 33
```

### Carregar dados no PostGIS

```bash
# Setup do schema PostGIS (executa uma vez)
psql -U postgres -d geopanda -f scripts/setup_postgis.sql

# Carregar shapefiles no banco
.venv/bin/python scripts/load_ibge.py --escala estados --clear
.venv/bin/python scripts/load_ibge.py --escala municipios
.venv/bin/python scripts/load_ibge.py --escala setores_censitarios

# Carregar um shapefile específico
.venv/bin/python scripts/load_ibge.py --escala municipios --shapefile ./data/raw/municipios/33/33MUE250GC_SIR.shp
```

### Iniciar o servidor

```bash
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Mapa interativo:** http://localhost:8000
- **Documentação Swagger:** http://localhost:8000/docs

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Página HTML com mapa Leaflet |
| GET | `/api/layers` | Lista camadas disponíveis |
| GET | `/api/geojson/{layer}` | GeoJSON de uma camada |
| GET | `/api/geojson/{layer}?bbox=...` | GeoJSON filtrado por bounding box |
| GET | `/api/geojson/{layer}?uf=33` | GeoJSON filtrado por estado |
| GET | `/api/feature/{layer}/{code}` | Detalhes de uma feição |
| GET | `/api/states` | Lista de estados |
| GET | `/api/stats/{layer}` | Estatísticas de uma camada |
| GET | `/api/ibge/populacao-estados` | População por estado |
| GET | `/api/ibge/municipios/{code}` | Municípios de um estado |
| GET | `/api/ibge/setores/{code}` | Setores censitários de um município |
| GET | `/api/ibge/mais-populosos` | Municípios mais populosos |
| GET | `/api/ibge/buscar?q=nome` | Busca municípios por nome |
