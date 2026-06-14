import logging

import httpx

from typing import Any

import httpx

from app.adapters.base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class LMStudioAdapter(BaseAdapter):
    def __init__(self, api_key: str = "", model: str = "", base_url: str = ""):
        self.base_url = (base_url or settings.lmstudio_base_url).rstrip("/")
        self.model = model or settings.lmstudio_model or "default"
        self.api_key = api_key or settings.lmstudio_api_key

    async def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def execute(self, **kwargs) -> dict:
        messages = kwargs.get("messages", [])
        tools = kwargs.get("tools")
        return await self.chat_completion(messages, tools=tools)

    async def chat_completion(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=await self._headers(),
                )
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]
                msg = choice["message"]
                result: dict = {
                    "success": True,
                    "content": msg.get("content", ""),
                    "tokens_input": data.get("usage", {}).get("prompt_tokens", 0),
                    "tokens_output": data.get("usage", {}).get("completion_tokens", 0),
                    "model": data.get("model", "unknown"),
                }
                if msg.get("tool_calls"):
                    result["tool_calls"] = msg["tool_calls"]
                    result["finish_reason"] = choice.get("finish_reason", "tool_calls")
                return result
        except httpx.TimeoutException:
            logger.error("LMStudio request timed out")
            return {"success": False, "error": "Request timed out"}
        except httpx.HTTPStatusError as e:
            logger.error(f"LMStudio HTTP error: {e.response.status_code}")
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"LMStudio error: {e}")
            return {"success": False, "error": str(e)}
