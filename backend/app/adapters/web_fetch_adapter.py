import logging

import httpx

from app.adapters.base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

BLOCKED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar", ".tar", ".gz", ".exe", ".dmg", ".iso", ".bin", ".mp3", ".mp4", ".avi", ".mov", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

BLOCKED_MEDIA_TYPES = {"application/", "image/", "audio/", "video/", "font/"}


class WebFetchAdapter(BaseAdapter):
    def __init__(self, timeout: int = 15, max_chars: int = 10000, user_agent: str = ""):
        self.timeout = timeout
        self.max_chars = max_chars
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; ACCOS-Bot/1.0)"

    async def execute(self, **kwargs) -> dict:
        url = kwargs.get("url", "")
        max_chars = kwargs.get("max_chars", self.max_chars)
        timeout = kwargs.get("timeout", self.timeout)
        return await self.fetch(url, max_chars=max_chars, timeout=timeout)

    async def fetch(self, url: str, max_chars: int = 0, timeout: int = 0) -> dict:
        if max_chars <= 0:
            max_chars = self.max_chars
        if timeout <= 0:
            timeout = self.timeout

        ext = self._get_extension(url)
        if ext in BLOCKED_EXTENSIONS:
            return {"success": False, "error": f"Blocked file extension: {ext}"}

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                )
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if any(content_type.startswith(prefix) for prefix in BLOCKED_MEDIA_TYPES):
                    return {"success": False, "error": f"Blocked content type: {content_type}"}

                if "text/html" in content_type or "text/plain" in content_type or content_type == "":
                    text = response.text
                else:
                    return {"success": False, "error": f"Unsupported content type: {content_type}"}

                try:
                    import trafilatura
                    result = trafilatura.extract(text, output_format="markdown", include_comments=False, no_fallback=False)
                    if result:
                        text = result
                except ImportError:
                    logger.warning("trafilatura not available, falling back to raw text")
                except Exception as e:
                    logger.warning(f"trafilatura extraction failed: {e}")

                if len(text) > max_chars:
                    text = text[:max_chars] + f"\n\n[Truncated at {max_chars} characters]"

                return {
                    "success": True,
                    "content": text,
                    "content_type": content_type,
                    "url": url,
                    "char_count": len(text),
                }

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            return {"success": False, "error": f"Request timed out after {timeout}s"}
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.warning(f"Request error for {url}: {e}")
            return {"success": False, "error": f"Connection error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return {"success": False, "error": str(e)}

    def _get_extension(self, url: str) -> str:
        from urllib.parse import urlparse, unquote
        path = unquote(urlparse(url).path)
        pos = path.rfind(".")
        if pos == -1:
            return ""
        return path[pos:].lower().split("?")[0].split("#")[0]
