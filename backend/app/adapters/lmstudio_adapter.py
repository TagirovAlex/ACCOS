import logging

import httpx

from app.adapters.base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class LMStudioAdapter(BaseAdapter):
    def __init__(self):
        self.base_url = settings.lmstudio_base_url.rstrip("/")
        self.model = settings.lmstudio_model or "default"

    async def execute(self, **kwargs) -> dict:
        messages = kwargs.get("messages", [])
        return await self.chat_completion(messages)

    async def chat_completion(self, messages: list[dict]) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]
                return {
                    "success": True,
                    "content": choice["message"]["content"],
                    "tokens_input": data.get("usage", {}).get("prompt_tokens", 0),
                    "tokens_output": data.get("usage", {}).get("completion_tokens", 0),
                    "model": data.get("model", "unknown"),
                }
        except httpx.TimeoutException:
            logger.error("LMStudio request timed out")
            return {"success": False, "error": "Request timed out"}
        except httpx.HTTPStatusError as e:
            logger.error(f"LMStudio HTTP error: {e.response.status_code}")
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"LMStudio error: {e}")
            return {"success": False, "error": str(e)}
