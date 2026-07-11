"""
Downloader automático de malhas territoriais do IBGE.

Baixa shapefiles da malha territorial para todas as unidades federativas.
Fonte: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais.html

Uso:
    python scripts/download_ibge.py
    python scripts/download_ibge.py --ano 2022 --escala municipal
    python scripts/download_ibge.py --escala setores_censitarios --uf 33
"""

import argparse
import zipfile
import shutil
from pathlib import Path

import requests

IBGE_URL = "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"

LAYER_MAP = {
    "regioes": {"qualificador": "regioes", "nivel": "regiao", "camadas": ["regiao"]},
    "estados": {"qualificador": "estados", "nivel": "estado", "camadas": ["estado"]},
    "mesorregioes": {"qualificador": "mesorregioes", "nivel": "mesorregiao", "camadas": ["mesorregiao"]},
    "microrregioes": {"qualificador": "microrregioes", "nivel": "microrregiao", "camadas": ["microrregiao"]},
    "municipios": {"qualificador": "municipios", "nivel": "municipio", "camadas": ["municipio"]},
    "setores_censitarios": {"qualificador": "setores-censitarios", "nivel": "setorCensitario", "camadas": ["setorCensitario"]},
}


def get_ibge_layer_urls(ano: int, escala: str) -> list[str]:
    """
    Constrói URLs para download de cada camada da malha territorial.

    Retorna lista de URLs para cada unidade federativa na escala desejada.
    """
    config = LAYER_MAP.get(escala)
    if not config:
        raise ValueError(f"Escala '{escala}' não suportada. Opções: {list(LAYER_MAP.keys())}")

    urls = []

    # Para regiões e estados, a URL é direta
    if escala in ("regioes", "estados"):
        url = (
            f"{IBGE_URL}"
            f"?formato=application/vnd.google-earth.kml+xml"
            f"&qualidade=absoluto"
            f"&intrarregiao={config['qualificador']}"
            f"&lingua=pt"
        )
        urls.append(url)

    # Para escalas subnacionais, precisa por UF
    elif escala in ("mesorregioes", "microrregioes", "municipios", "setores_censitarios"):
        uf_codes = get_uf_codes()
        for cod_uf in uf_codes:
            url = (
                f"{IBGE_URL}/estados/{cod_uf}"
                f"?formato=application/vnd.google-earth.kml+xml"
                f"&qualidade=absoluto"
                f"&intrarregiao={config['qualificador']}"
                f"&lingua=pt"
            )
            urls.append(url)

    return urls


def get_uf_codes() -> list[str]:
    """Retorna códigos IBGE de todas as UFs do Brasil."""
    return [
        "11", "12", "13", "14", "15", "16", "17",
        "21", "22", "23", "24", "25", "26", "27", "28", "29",
        "31", "32", "33", "35",
        "41", "42", "43",
        "50", "51", "52", "53",
    ]


def download_shapefile(url: str, output_dir: Path) -> Path:
    """Baixa um shapefile de uma URL do IBGE e extrai."""
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / "download.zip"

    print(f"  Baixando: {url[:100]}...")

    resp = requests.get(url, timeout=120)
    resp.raise_for_status()

    zip_path.write_bytes(resp.content)
    print(f"  Extraindo para: {output_dir}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(output_dir)

    zip_path.unlink()
    return output_dir


def download_ibge_complete(ano: int, escala: str, output_base: Path, uf: str | None = None):
    """Pipeline completo de download da malha territorial."""
    print(f"\n=== Download IBGE: {escala} (ano {ano}) ===\n")

    config = LAYER_MAP.get(escala)
    if not config:
        raise ValueError(f"Escala '{escala}' não suportada.")

    output_dir = output_base / escala
    output_dir.mkdir(parents=True, exist_ok=True)

    if escala in ("regioes", "estados"):
        url = (
            f"{IBGE_URL}"
            f"?formato=application/vnd.google-earth.kml+xml"
            f"&qualidade=absoluto"
            f"&intrarregiao={config['qualificador']}"
            f"&lingua=pt"
        )
        print(f"[1/1] Baixando {escala}...")
        download_shapefile(url, output_dir)

    else:
        ufs = [uf] if uf else get_uf_codes()
        total = len(ufs)
        for i, cod_uf in enumerate(ufs, 1):
            url = (
                f"{IBGE_URL}/estados/{cod_uf}"
                f"?formato=application/vnd.google-earth.kml+xml"
                f"&qualidade=absoluto"
                f"&intrarregiao={config['qualificador']}"
                f"&lingua=pt"
            )
            print(f"[{i}/{total}] Baixando {escala} - UF {cod_uf}...")
            uf_dir = output_dir / cod_uf
            download_shapefile(url, uf_dir)

    print(f"\nDownload completo! Arquivos em: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Downloader de malhas IBGE")
    parser.add_argument("--ano", type=int, default=2022, help="Ano da malha (padrão: 2022)")
    parser.add_argument("--escala", type=str, default="municipios",
                        choices=list(LAYER_MAP.keys()),
                        help="Escala da malha (padrão: municipios)")
    parser.add_argument("--output", type=str, default="./data/raw",
                        help="Diretório de saída (padrão: ./data/raw)")
    parser.add_argument("--uf", type=str, default=None,
                        help="Código da UF para filtrar (ex: 33 para RJ)")
    args = parser.parse_args()

    output = Path(args.output)
    download_ibge_complete(args.ano, args.escala, output, args.uf)


if __name__ == "__main__":
    main()
