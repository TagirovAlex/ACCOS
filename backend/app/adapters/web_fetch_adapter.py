import logging
from urllib.parse import urljoin, urlparse, unquote
from html.parser import HTMLParser

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
                response = await client.get(url, headers={"User-Agent": self.user_agent})
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if any(content_type.startswith(p) for p in BLOCKED_MEDIA_TYPES):
                    return {"success": False, "error": f"Blocked content type: {content_type}"}

                links = []
                if "text/html" in content_type or content_type == "":
                    links = self._extract_links(response.text, url)

                text = response.text
                if "text/html" in content_type or "text/plain" in content_type or content_type == "":
                    try:
                        import trafilatura
                        result = trafilatura.extract(text, output_format="markdown", include_comments=False, no_fallback=False)
                        if result:
                            text = result
                    except ImportError:
                        logger.warning("trafilatura not available, falling back to raw text")
                    except Exception as e:
                        logger.warning(f"trafilatura extraction failed: {e}")
                else:
                    return {"success": False, "error": f"Unsupported content type: {content_type}"}

                if len(text) > max_chars:
                    text = text[:max_chars] + f"\n\n[Truncated at {max_chars} characters]"

                return {"success": True, "content": text, "content_type": content_type, "url": url, "char_count": len(text), "links": links}

        except httpx.TimeoutException:
            return {"success": False, "error": f"Request timed out after {timeout}s"}
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Connection error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return {"success": False, "error": str(e)}

    def _extract_links(self, html: str, base_url: str) -> list[dict]:
        class LinkParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
                self._in_a = False
                self._href = ""
                self._text = ""

            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    self._href = dict(attrs).get("href", "")
                    self._in_a = True
                    self._text = ""

            def handle_endtag(self, tag):
                if tag == "a" and self._in_a:
                    href = self._href.strip()
                    text = self._text.strip()
                    if href and text and not href.startswith("#") and not href.startswith("javascript:"):
                        self.links.append({"url": urljoin(base_url, href), "text": text[:200]})
                    self._in_a = False

            def handle_data(self, data):
                if self._in_a:
                    self._text += data

        parser = LinkParser()
        parser.feed(html)
        seen = set()
        unique = []
        for l in parser.links:
            if l["url"] not in seen:
                seen.add(l["url"])
                unique.append(l)
        return unique[:100]

    def _get_extension(self, url: str) -> str:
        path = unquote(urlparse(url).path)
        pos = path.rfind(".")
        if pos == -1:
            return ""
        return path[pos:].lower().split("?")[0].split("#")[0]
