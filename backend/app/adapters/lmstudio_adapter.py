import logging
import time
from typing import Any

import httpx

from app.adapters.base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

_vision_cache: dict[str, tuple[bool, float]] = {}
_VISION_CACHE_TTL = 300
_VISION_KEYWORDS = {"llava", "qwen-vl", "pixtral", "vision", "llama-vision", "llama-3.2-vision", "llama3.2-vision"}


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

    async def check_vision_capability(self) -> bool:
        now = time.time()
        cache_key = f"{self.base_url}:{self.model}"
        if cache_key in _vision_cache:
            cached, ts = _vision_cache[cache_key]
            if now - ts < _VISION_CACHE_TTL:
                return cached
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                if resp.status_code == 200:
                    models = resp.json().get("data", [])
                    for m in models:
                        mid = (m.get("id") or "").lower()
                        mlower = self.model.lower()
                        if mlower in mid:
                            supports = m.get("supports_vision", False)
                            if supports:
                                _vision_cache[cache_key] = (True, now)
                                return True
                            for kw in _VISION_KEYWORDS:
                                if kw in mid:
                                    _vision_cache[cache_key] = (True, now)
                                    return True
                            _vision_cache[cache_key] = (False, now)
                            return False
        except Exception as e:
            logger.warning(f"Vision check failed: {e}")
        mlower = self.model.lower()
        for kw in _VISION_KEYWORDS:
            if kw in mlower:
                _vision_cache[cache_key] = (True, now)
                return True
        _vision_cache[cache_key] = (False, now)
        return False
