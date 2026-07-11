# Plano de Implementação — GeoPanda SIG

## Fase 1: Estrutura Base ✅

- [x] Criar virtual environment com Python 3.12
- [x] Configurar `requirements.txt` com todas as dependências
- [x] Criar `.gitignore` e `.env.example`
- [x] Criar estrutura de diretórios do projeto

## Fase 2: Banco de Dados ✅

- [x] Criar `scripts/setup_postgis.sql` com schema completo
  - Tabelas: regioes, estados, mesorregioes, microrregioes, municipios, setores_censitarios
  - Índices GIST espaciais para todas as tabelas
  - Índices de FK para joins performáticos
- [x] Criar ORM models com GeoAlchemy2 (`app/models/spatial.py`)
- [x] Configurar engine async + sync (`app/database.py`)

## Fase 3: Ingestão de Dados ✅

- [x] Criar `scripts/download_ibge.py`
  - Download da malha territorial do IBGE via API REST
  - Suporte a todas as escalas (regiões → setores censitários)
  - Filtro por UF
  - Extração automática de shapefiles ZIP
- [x] Criar `scripts/load_ibge.py`
  - Leitura de shapefiles com GeoPandas
  - Reprojeção automática para SIRGAS 2000 (EPSG:4674)
  - Mapeamento de colunas por escala
  - Validação e reparo de geometrias
  - Inserção em massa no PostGIS

## Fase 4: Backend API ✅

- [x] Criar configurações (`app/config.py`)
  - Pydantic Settings com leitura de `.env`
  - Variáveis: DATABASE_URL, paths, host/port
- [x] Criar serviços
  - `app/services/geo_service.py`: consultas espaciais, GeoJSON, bbox, stats
  - `app/services/ibge_service.py`: joins, agregações, buscas
- [x] Criar rotas
  - `app/routes/geo_routes.py`: endpoints REST da API
  - `app/routes/pages.py`: serve templates HTML
- [x] Criar `app/main.py` com FastAPI app

## Fase 5: Frontend ✅

- [x] Criar `app/templates/base.html`
  - Layout com sidebar + mapa
  - CDN Leaflet.js + MarkerCluster
  - Font Awesome para ícones
- [x] Criar `app/templates/index.html`
  - Extends base.html
- [x] Criar `app/static/css/style.css`
  - Tema dark (blue/purple/red)
  - Sidebar responsiva
  - Popups estilizados
  - Loading overlay com spinner
- [x] Criar `app/static/js/map.js`
  - Inicialização do Leaflet.js
  - Carregamento dinâmico de camadas via API
  - Toggle de camadas com checkboxes
  - Filtro por estado (dropdown)
  - Busca de municípios (input + enter)
  - Temas de visualização (população, área)
  - Slider de opacidade
  - Hover highlight nas feições
  - Popups e sidebar de detalhes

## Fase 6: Análise Exploratória ✅

- [x] Criar notebook `notebooks/exploracao_ibge.ipynb`
  - Leitura de shapefiles com GeoPandas
  - Reprojeção de CRS
  - Visualização com Matplotlib
  - Cálculo de áreas
  - Operações espaciais (buffer)
  - Exportação para GeoJSON

## Fase 7: Documentação ✅

- [x] Criar `README.md` com instruções completas
- [x] Criar `design.md` com arquitetura e decisões
- [x] Criar `plan.md` com este plano

## Fase 8: Controle de Versão ✅

- [x] Inicializar repositório Git
- [x] Commit inicial com todos os arquivos

## Deploy (Próximos Passos)

- [ ] Configurar PostgreSQL + PostGIS (local ou cloud)
- [ ] Executar `setup_postgis.sql`
- [ ] Baixar malhas do IBGE (`download_ibge.py`)
- [ ] Carregar dados no PostGIS (`load_ibge.py`)
- [ ] Iniciar servidor FastAPI
- [ ] Testar endpoints na documentação Swagger

## Endpoints Implementados

| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| GET | `/api/layers` | ✅ |
| GET | `/api/geojson/{layer}` | ✅ |
| GET | `/api/geojson/{layer}?bbox=...` | ✅ |
| GET | `/api/geojson/{layer}?uf=...` | ✅ |
| GET | `/api/feature/{layer}/{code}` | ✅ |
| GET | `/api/states` | ✅ |
| GET | `/api/stats/{layer}` | ✅ |
| GET | `/api/ibge/populacao-estados` | ✅ |
| GET | `/api/ibge/municipios/{code}` | ✅ |
| GET | `/api/ibge/setores/{code}` | ✅ |
| GET | `/api/ibge/mais-populosos` | ✅ |
| GET | `/api/ibge/buscar?q=...` | ✅ |
