import logging
import threading

import httpx

from app.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

_model_cache = {}
_model_cache_lock = threading.Lock()


def _get_local_model(model_name: str):
    if model_name in _model_cache:
        return _model_cache[model_name]
    with _model_cache_lock:
        if model_name not in _model_cache:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading local embedding model: {model_name}")
            _model_cache[model_name] = SentenceTransformer(model_name)
        return _model_cache[model_name]


class RAGAdapter(BaseAdapter):
    def __init__(self, base_url: str, model: str = "default", api_key: str = ""):
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.model = model
        self.api_key = api_key

    async def embed(self, texts: list[str]) -> list[list[float]] | None:
        if not texts:
            return None

        if not self.base_url or self.base_url == "local":
            return await self._embed_local(texts)

        return await self._embed_api(texts)

    async def _embed_api(self, texts: list[str]) -> list[list[float]] | None:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "input": texts,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                embeddings = []
                for item in data.get("data", []):
                    embeddings.append(item["embedding"])
                return embeddings
        except Exception as e:
            logger.error(f"RAGAdapter embed API failed: {e}")
            return None

    async def _embed_local(self, texts: list[str]) -> list[list[float]] | None:
        try:
            import asyncio
            model_obj = await asyncio.to_thread(_get_local_model, self.model)
            embeddings = await asyncio.to_thread(model_obj.encode, texts, normalize_embeddings=True)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"RAGAdapter embed local failed: {e}")
            return None

    async def execute(self, **kwargs) -> dict:
        texts = kwargs.get("texts", [])
        result = await self.embed(texts)
        if result is None:
            return {"success": False, "error": "Embedding failed"}
        return {"success": True, "embeddings": result}
