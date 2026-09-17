from __future__ import annotations

import json
import time
from urllib.parse import urlparse

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

    @property
    def database_url_scheme(self) -> str:
        return urlparse(self.database_url).scheme


settings = Settings()

# #region agent log
try:
    _payload = {
        "sessionId": "6a98e1",
        "hypothesisId": "A",
        "location": "config.py:settings",
        "message": "database_url scheme after normalize",
        "data": {"scheme": settings.database_url_scheme},
        "timestamp": int(time.time() * 1000),
    }
    print(f"[chainlens-debug] {_payload}", flush=True)
    with open(
        "/home/lana/Documents/cari_kerja/small_projects/1.chainlens/.cursor/debug-6a98e1.log",
        "a",
        encoding="utf-8",
    ) as _f:
        _f.write(json.dumps(_payload) + "\n")
except Exception:
    pass
# #endregion
