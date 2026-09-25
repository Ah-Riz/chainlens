from __future__ import annotations

from google import genai
from google.genai import types

from app.config import settings
from app.services.llm import is_plausible_gemini_key

EMBED_DIM = 1536
EMBEDDING_MODEL = "gemini-embedding-001"


async def embed_text(text: str) -> list[float] | None:
    if not is_plausible_gemini_key(settings.gemini_api_key) or settings.mock_analyze:
        return None
    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        res = await client.aio.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text[:8000],
            config=types.EmbedContentConfig(output_dimensionality=EMBED_DIM),
        )
        embeddings = getattr(res, "embeddings", None) or []
        if not embeddings:
            return None
        values = getattr(embeddings[0], "values", None)
        if not values:
            return None
        return list(values)
    except Exception:
        return None
