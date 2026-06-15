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
        chromium_path: str = "/usr/bin/chromium",
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.timeout = timeout
        self.concurrent = concurrent
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; ACCOS-DocBot/1.0)"
        self.chromium_path = chromium_path

    async def execute(self, **kwargs) -> CrawlResult:
        return await self.crawl(
            site_url=kwargs.get("site_url", ""),
            max_pages=kwargs.get("max_pages", self.max_pages),
            max_depth=kwargs.get("max_depth", self.max_depth),
        )

    async def discover(self, site_url: str) -> list[str]:
        """Discover all page URLs on a site (quick BFS without content extraction)."""
        base_url = site_url.rstrip("/")
        parsed = urlparse(base_url)
        base_domain = parsed.netloc
        path_parts = parsed.path.strip("/").split("/") if parsed.path and parsed.path != "/" else []
        base_path = "/" + "/".join(path_parts[:2]) + "/" if path_parts else "/"

        visited: set[str] = set()
        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
            queue: list[tuple[str, int]] = [(base_url, 0)]

            api_pages = await self._discover_via_confluence_api(client, base_url)
            if api_pages:
                queue = [(p, 0) for p in api_pages if p not in visited]
            else:
                pw_pages = await self._discover_via_playwright(base_url, base_domain)
                if pw_pages:
                    queue = [(p, 0) for p in pw_pages if p not in visited]

            while queue and len(visited) < self.max_pages:
                url, depth = queue.pop(0)
                url, _ = urldefrag(url)
                url = url.rstrip("/")
                if url in visited or depth > self.max_depth:
                    continue
                parsed_url = urlparse(url)
                if parsed_url.netloc and parsed_url.netloc != base_domain:
                    continue
                if not parsed_url.path.startswith(base_path) and parsed_url.path != "":
                    continue
                if any(re.search(p, url, re.IGNORECASE) for p in EXCLUDE_PATTERNS):
                    continue
                visited.add(url)
                try:
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code != 200:
                        continue
                    if "text/html" not in resp.headers.get("content-type", ""):
                        continue
                    links = self._extract_links(resp.text, url, base_domain, base_path)
                    for link in links:
                        if link not in visited:
                            queue.append((link, depth + 1))
                except Exception:
                    continue

        return list(visited)

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
        path_parts = parsed.path.strip("/").split("/") if parsed.path and parsed.path != "/" else []
        base_path = "/" + "/".join(path_parts[:2]) + "/" if path_parts else "/"

        visited: set[str] = set()
        pages: list[ScrapedPage] = []
        errors: list[str] = []
        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
            queue: list[tuple[str, int]] = [(base_url, 0)]

            api_pages = await self._discover_via_confluence_api(client, base_url)
            if api_pages:
                queue = [(p, 0) for p in api_pages if p not in visited]
            else:
                pw_pages = await self._discover_via_playwright(base_url, base_domain)
                if pw_pages:
                    queue = [(p, 0) for p in pw_pages if p not in visited]

            while queue and len(pages) < max_pages:
                url, depth = queue.pop(0)
                url, _ = urldefrag(url)
                url = url.rstrip("/")

                if url in visited or depth > max_depth:
                    continue
                if any(re.search(p, url, re.IGNORECASE) for p in EXCLUDE_PATTERNS):
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
                    if "text/html" not in resp.headers.get("content-type", ""):
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

    async def _discover_via_confluence_api(self, client: httpx.AsyncClient, base_url: str) -> list[str]:
        parsed = urlparse(base_url)
        parts = parsed.path.strip("/").split("/")
        space_key = None
        for i, p in enumerate(parts):
            if p == "spaces" and i + 1 < len(parts):
                space_key = parts[i + 1]
                break
        if not space_key:
            return []

        scheme = parsed.scheme or "https"
        root = f"{scheme}://{parsed.netloc}"
        api_url = f"{root}/rest/api/content?spaceKey={space_key}&limit=100"

        try:
            resp = await client.get(api_url, follow_redirects=True, timeout=15)
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return []
            pages: list[str] = []
            for r in results:
                webui = r.get("_links", {}).get("webui", "")
                if webui:
                    pages.append(urljoin(root, webui).rstrip("/"))
            while data.get("_links", {}).get("next"):
                next_url = root + data["_links"]["next"]
                resp = await client.get(next_url, follow_redirects=True, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                for r in data.get("results", []):
                    webui = r.get("_links", {}).get("webui", "")
                    if webui:
                        pages.append(urljoin(root, webui).rstrip("/"))
            return pages
        except Exception as e:
            logger.debug(f"Confluence API discovery failed for {api_url}: {e}")
            return []

    async def _discover_via_playwright(self, base_url: str, base_domain: str) -> list[str]:
        from playwright.async_api import async_playwright
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    executable_path=self.chromium_path,
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )
                ctx = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1920, "height": 1080},
                )
                page = await ctx.new_page()
                await page.goto(base_url, wait_until="load", timeout=self.timeout * 1000)
                await page.wait_for_timeout(3000)

                links = await page.evaluate("""
                    () => {
                        const urls = new Set();
                        document.querySelectorAll('a[href]').forEach(a => {
                            try {
                                const href = a.href.split('#')[0].replace(/\/$/, '');
                                if (href) urls.add(href);
                            } catch(e) {}
                        });
                        return Array.from(urls);
                    }
                """)
                await browser.close()

                discovered = []
                for url in links:
                    parsed = urlparse(url)
                    if parsed.netloc == base_domain:
                        discovered.append(url.rstrip("/"))
                return list(set(discovered))
        except Exception as e:
            logger.warning(f"Playwright discovery failed: {e}")
            return []
