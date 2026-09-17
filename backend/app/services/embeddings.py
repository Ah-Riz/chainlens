from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings

EMBED_DIM = 1536


async def embed_text(text: str) -> list[float] | None:
    if not settings.openai_api_key or settings.mock_analyze:
        return None
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        res = await client.embeddings.create(model=settings.embedding_model, input=text[:8000])
        return list(res.data[0].embedding)
    except Exception:
        return None
