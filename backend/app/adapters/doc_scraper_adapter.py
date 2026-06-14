import asyncio
import logging
import re
import time
from urllib.parse import urlparse, urljoin, urldefrag
from dataclasses import dataclass

import httpx
from trafilatura import extract
from trafilatura.settings import use_config

from app.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

traf_config = use_config()
traf_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")

EXCLUDE_PATTERNS = [
    r"\.(png|jpg|jpeg|gif|svg|css|js|woff|woff2|ico|pdf|zip|tar|gz|exe|dmg|mp4|mp3|avi|mov)$",
    r"/api/",
    r"/search",
    r"/login",
    r"/signup",
    r"/signin",
    r"\?.*page=",
    r"/cdn-cgi/",
]


@dataclass
class ScrapedPage:
    url: str
    title: str
    content: str
    word_count: int
    fetched_at: str


@dataclass
class CrawlResult:
    pages: list[ScrapedPage]
    pages_found: int
    errors: list[str]


class DocScraperAdapter(BaseAdapter):
    def __init__(
        self,
        max_pages: int = 500,
        max_depth: int = 10,
        delay: float = 0.5,
        timeout: int = 30,
        concurrent: int = 3,
        user_agent: str = "",
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.timeout = timeout
        self.concurrent = concurrent
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; ACCOS-DocBot/1.0)"

    async def execute(self, **kwargs) -> CrawlResult:
        return await self.crawl(
            site_url=kwargs.get("site_url", ""),
            max_pages=kwargs.get("max_pages", self.max_pages),
            max_depth=kwargs.get("max_depth", self.max_depth),
        )

    async def crawl(
        self,
        site_url: str,
        max_pages: int = 0,
        max_depth: int = 0,
    ) -> CrawlResult:
        if max_pages <= 0:
            max_pages = self.max_pages
        if max_depth <= 0:
            max_depth = self.max_depth

        base_url = site_url.rstrip("/")
        parsed = urlparse(base_url)
        base_domain = parsed.netloc
        base_path = parsed.path or "/"

        visited: set[str] = set()
        pages: list[ScrapedPage] = []
        errors: list[str] = []

        headers = {"User-Agent": self.user_agent}

        def should_exclude(url: str) -> bool:
            for pat in EXCLUDE_PATTERNS:
                if re.search(pat, url, re.IGNORECASE):
                    return True
            return False

        async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
            queue: list[tuple[str, int]] = [(base_url, 0)]

            while queue and len(pages) < max_pages:
                url, depth = queue.pop(0)
                url, _ = urldefrag(url)
                url = url.rstrip("/")

                if url in visited or depth > max_depth:
                    continue
                if should_exclude(url):
                    continue

                parsed_url = urlparse(url)
                if parsed_url.netloc and parsed_url.netloc != base_domain:
                    continue
                if not parsed_url.path.startswith(base_path) and parsed_url.path != "":
                    continue

                visited.add(url)

                try:
                    await asyncio.sleep(self.delay)
                    resp = await client.get(url, follow_redirects=True)

                    if resp.status_code != 200:
                        errors.append(f"{url}: HTTP {resp.status_code}")
                        continue

                    content_type = resp.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        continue

                    html = resp.text
                    text_content = extract(
                        html,
                        include_comments=False,
                        include_tables=True,
                        include_links=False,
                        include_formatting=True,
                        favor_recall=True,
                        config=traf_config,
                    )

                    if not text_content or len(text_content.strip()) < 50:
                        links = self._extract_links(html, url, base_domain, base_path)
                        for link in links:
                            if link not in visited:
                                queue.append((link, depth + 1))
                        continue

                    title = self._extract_title(html)

                    page = ScrapedPage(
                        url=url,
                        title=title,
                        content=text_content,
                        word_count=len(text_content.split()),
                        fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                    pages.append(page)

                    links = self._extract_links(html, url, base_domain, base_path)
                    for link in links:
                        if link not in visited:
                            queue.append((link, depth + 1))

                except httpx.TimeoutException:
                    errors.append(f"{url}: timeout")
                except httpx.RequestError as e:
                    errors.append(f"{url}: {e}")
                except Exception as e:
                    errors.append(f"{url}: {e}")
                    logger.warning(f"Error crawling {url}: {e}")

        return CrawlResult(pages=pages, pages_found=len(visited), errors=errors)

    def _extract_title(self, html: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)
        return ""

    def _extract_links(self, html: str, page_url: str, base_domain: str, base_path: str) -> list[str]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute = urljoin(page_url, href)
            absolute, _ = urldefrag(absolute)
            absolute = absolute.rstrip("/")
            parsed = urlparse(absolute)
            if parsed.netloc and parsed.netloc != base_domain:
                continue
            if not parsed.path.startswith(base_path):
                continue
            links.append(absolute)
        return list(set(links))
