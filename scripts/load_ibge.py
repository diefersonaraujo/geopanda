"""
Script de carregamento de shapefiles do IBGE no PostGIS via GeoPandas.

Uso:
    python scripts/load_ibge.py --escala municipios
    python scripts/load_ibge.py --escala setores_censitarios --uf 33
    python scripts/load_ibge.py --escala estados --shapefile ./data/raw/estados/BRUFE500GC_SIR.shp
"""

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import make_valid
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

import os

DATABASE_URL = os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:postgres@localhost:5432/geopanda")
DATA_DIR = Path(os.getenv("IBGE_DATA_DIR", "./data/raw"))


COLUNAS_MAPEAMENTO = {
    "municipios": {
        "cod_ibge": "codigo_ibge",
        "CD_MUN": "codigo_ibge",
        "NM_MUN": "nome",
        "SIGLA_UF": "uf",
        "SIGLA": "uf",
        "geometry": "geom",
    },
    "estados": {
        "cod_ibge": "codigo_ibge",
        "CD_UF": "codigo_ibge",
        "NM_UF": "nome",
        "SIGLA_UF": "uf",
        "SIGLA": "uf",
        "geometry": "geom",
    },
    "regioes": {
        "cod_ibge": "codigo_ibge",
        "CD_REGIAO": "codigo_ibge",
        "NM_REGIAO": "nome",
        "geometry": "geom",
    },
    "mesorregioes": {
        "cod_ibge": "codigo_ibge",
        "CD_MESO": "codigo_ibge",
        "NM_MESO": "nome",
        "CD_UF": "estado_codigo",
        "geometry": "geom",
    },
    "microrregioes": {
        "cod_ibge": "codigo_ibge",
        "CD_MICRO": "codigo_ibge",
        "NM_MICRO": "nome",
        "CD_MESO": "mesorregiao_codigo",
        "geometry": "geom",
    },
    "setores_censitarios": {
        "cod_ibge": "codigo_ibge",
        "CD_GEOCOD": "codigo_ibge",
        "CD_GEOCODM": "municipio_codigo",
        "geometry": "geom",
    },
}

COLUNAS_AREA = {
    "municipios": "area_km2",
    "estados": "area_km2",
    "mesorregioes": "area_km2",
    "microrregioes": "area_km2",
    "setores_censitarios": "area_km2",
}


def find_shapefiles(base_dir: Path) -> list[Path]:
    """Encontra todos os arquivos .shp no diretório, recursivamente."""
    return sorted(base_dir.rglob("*.shp"))


def load_shapefile_to_postgis(
    shapefile_path: Path,
    table_name: str,
    engine,
    chunk_size: int = 5000,
):
    """Carrega um shapefile para uma tabela PostGIS usando GeoPandas."""
    print(f"\n  Lendo shapefile: {shapefile_path}")

    gdf = gpd.read_file(shapefile_path, encoding="latin-1")
    print(f"  Colunas originais: {list(gdf.columns)}")
    print(f"  Registros: {len(gdf)}")
    print(f"  CRS original: {gdf.crs}")

    # Reprojetar para SIRGAS 2000 (EPSG:4674) se necessário
    if gdf.crs is not None and gdf.crs.to_epsg() != 4674:
        print(f"  Reprojetando de {gdf.crs.to_epsg()} para EPSG:4674...")
        gdf = gdf.to_crs(epsg=4674)

    # Renomear colunas conforme mapeamento
    mapping = COLUNAS_MAPEAMENTO.get(table_name, {})
    rename_map = {}
    for original, target in mapping.items():
        if original in gdf.columns and original != "geometry":
            rename_map[original] = target
    if rename_map:
        gdf = gdf.rename(columns=rename_map)

    # Calcular área em km²
    area_col = COLUNAS_AREA.get(table_name)
    if area_col and area_col not in gdf.columns:
        try:
            area_series = gdf.geometry.area / 1000000  # m² → km² no SIRGAS 2000
            gdf[area_col] = area_series.round(4)
        except Exception:
            pass

    # Garantir geometrias válidas
    print("  Validando geometrias...")
    gdf["geometry"] = gdf["geometry"].apply(lambda g: make_valid(g) if g and not g.is_valid else g)
    gdf = gdf[~gdf.geometry.isna() & ~gdf.geometry.is_empty]

    # Garantir SRID correto
    gdf = gdf.set_crs(epsg=4674, allow_override=True)

    # Converter colunas numéricas
    for col in gdf.columns:
        if col == "geometry":
            continue
        try:
            gdf[col] = pd.to_numeric(gdf[col])
        except (ValueError, TypeError):
            pass

    # Inserir no PostGIS
    print(f"  Inserindo na tabela '{table_name}'...")
    gdf.to_postgis(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=chunk_size,
    )
    print(f"  OK: {len(gdf)} registros inseridos em '{table_name}'.")


def setup_database(engine):
    """Executa o script SQL de setup do PostGIS."""
    sql_path = Path(__file__).parent / "setup_postgis.sql"
    if sql_path.exists():
        print("Executando setup_postgis.sql...")
        with engine.connect() as conn:
            sql = sql_path.read_text()
            conn.execute(text(sql))
            conn.commit()
        print("Setup concluído!")


def clear_table(engine, table_name: str):
    """Limpa registros existentes na tabela."""
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM {table_name}"))
        conn.commit()
    print(f"  Tabela '{table_name}' limpa.")


def main():
    parser = argparse.ArgumentParser(description="Carrega shapefiles IBGE no PostGIS")
    parser.add_argument("--escala", type=str, required=True,
                        choices=list(COLUNAS_MAPEAMENTO.keys()),
                        help="Escala da malha para carregar")
    parser.add_argument("--uf", type=str, default=None,
                        help="Código da UF para filtrar (carrega apenas uma UF)")
    parser.add_argument("--shapefile", type=str, default=None,
                        help="Caminho direto para um shapefile específico")
    parser.add_argument("--clear", action="store_true",
                        help="Limpa a tabela antes de inserir")
    parser.add_argument("--no-setup", action="store_true",
                        help="Pula a execução do setup_postgis.sql")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)

    if not args.no_setup:
        setup_database(engine)

    if args.shapefile:
        shapefile = Path(args.shapefile)
        if not shapefile.exists():
            print(f"ERRO: Shapefile não encontrado: {shapefile}")
            return
        if args.clear:
            clear_table(engine, args.escala)
        load_shapefile_to_postgis(shapefile, args.escala, engine)
        return

    # Determinar diretório de busca
    escala_dir = DATA_DIR / args.escala
    if not escala_dir.exists():
        print(f"ERRO: Diretório não encontrado: {escala_dir}")
        print(f"Execute primeiro o script de download:")
        print(f"  python scripts/download_ibge.py --escala {args.escala}")
        return

    if args.uf:
        escala_dir = escala_dir / args.uf
        if not escala_dir.exists():
            print(f"ERRO: Diretório da UF não encontrado: {escala_dir}")
            return

    if args.clear:
        clear_table(engine, args.escala)

    # Encontrar e carregar shapefiles
    shp_files = find_shapefiles(escala_dir)
    if not shp_files:
        print(f"Nenhum .shp encontrado em: {escala_dir}")
        return

    print(f"\nEncontrados {len(shp_files)} shapefile(s):")
    for shp in shp_files:
        print(f"  - {shp}")

    for shp in shp_files:
        load_shapefile_to_postgis(shp, args.escala, engine)

    print(f"\nCarregamento de '{args.escala}' concluído!")


if __name__ == "__main__":
    main()
