from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/geopanda"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/geopanda"
    IBGE_DATA_DIR: str = "./data/raw"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
