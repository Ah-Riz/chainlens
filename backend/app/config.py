from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_async_mysql_url(url: str) -> str:
    """Force asyncmy driver — TiDB/SQLAlchemy consoles often emit mysql:// or mysql+pymysql://."""
    for prefix in ("mysql+pymysql://", "mysql+mysqldb://", "mysql://"):
        if url.startswith(prefix):
            return "mysql+asyncmy://" + url.removeprefix(prefix)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    tx_fetch_limit: int = 40
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    database_url: str = "mysql+asyncmy://root@127.0.0.1:4000/chainlens"
    cors_origins: str = "http://localhost:3000"
    mock_analyze: bool = True

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_asyncmy(cls, v: object) -> object:
        if isinstance(v, str) and v.strip():
            return _normalize_async_mysql_url(v.strip())
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
