import logging

import httpx

from app.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class RAGAdapter(BaseAdapter):
    def __init__(self, base_url: str, model: str = "default", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    async def embed(self, texts: list[str]) -> list[list[float]] | None:
        if not texts:
            return None
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
            logger.error(f"RAGAdapter embed failed: {e}")
            return None

    async def execute(self, **kwargs) -> dict:
        texts = kwargs.get("texts", [])
        result = await self.embed(texts)
        if result is None:
            return {"success": False, "error": "Embedding failed"}
        return {"success": True, "embeddings": result}
