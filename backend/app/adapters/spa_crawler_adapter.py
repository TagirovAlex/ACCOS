import asyncio
import logging
import time
from urllib.parse import urlparse

from trafilatura import extract
from trafilatura.settings import use_config

from app.adapters.base import BaseAdapter
from app.adapters.doc_scraper_adapter import ScrapedPage, CrawlResult

logger = logging.getLogger(__name__)

traf_config = use_config()
traf_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")


class SpaCrawlerAdapter(BaseAdapter):
    def __init__(
        self,
        max_pages: int = 500,
        max_depth: int = 10,
        timeout: int = 30,
        chromium_path: str = "/usr/bin/chromium",
        concurrent: int = 3,
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.timeout = timeout
        self.chromium_path = chromium_path
        self.concurrent = concurrent

    async def execute(self, **kwargs) -> CrawlResult:
        return await self.crawl(
            site_url=kwargs.get("site_url", ""),
            max_pages=kwargs.get("max_pages", self.max_pages),
            max_depth=kwargs.get("max_depth", self.max_depth),
        )

    async def discover(self, site_url: str) -> tuple[str, str, list[str]]:
        base_url = site_url.rstrip("/")
        parsed = urlparse(base_url)
        base_domain = parsed.netloc

        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                executable_path=self.chromium_path,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            ctx = await browser.new_context()
            page = await ctx.new_page()
            project, slugs = await self._discover(page, base_url)
            await browser.close()

        if len(slugs) > self.max_pages:
            slugs = slugs[:self.max_pages]
        return project, base_domain, slugs

    async def crawl(self, site_url: str, max_pages: int = 0, max_depth: int = 0) -> CrawlResult:
        project, base_domain, slugs = await self.discover(site_url)
        return await self._crawl_batch(project, base_domain, slugs, max_pages=max_pages)

    async def _crawl_batch(
        self,
        project: str,
        base_domain: str,
        batch: list[str],
        max_pages: int = 0,
    ) -> CrawlResult:
        if max_pages <= 0:
            max_pages = self.max_pages

        pages: list[ScrapedPage] = []
        errors: list[str] = []

        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                executable_path=self.chromium_path,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            ctx = await browser.new_context()
            page = await ctx.new_page()
            base_articles_url = f"https://{base_domain}/articles"
            await page.goto(base_articles_url, wait_until="load", timeout=30000)

            sem = asyncio.Semaphore(self.concurrent)

            async def fetch(slug: str) -> ScrapedPage | None:
                async with sem:
                    try:
                        data = await page.evaluate(
                            """async ({project, slug, baseUrl}) => {
                                const url = '/helper/articles/' + project + '/' + slug + '/';
                                const resp = await fetch(url, {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({
                                        curUrl: baseUrl + '/#!' + project + '/' + slug,
                                        articleChangedFromTabName: null,
                                        articleChangedRefEntityId: null,
                                    })
                                });
                                return await resp.json();
                            }""",
                            {"project": project, "slug": slug, "baseUrl": base_articles_url},
                        )
                    except Exception as e:
                        logger.warning(f"Fetch failed for {slug}: {e}")
                        return None
                    return self._process(data, slug)

            tasks = [fetch(s) for s in batch]
            results = await asyncio.gather(*tasks)

            for slug, r in zip(batch, results):
                if r:
                    pages.append(r)
                else:
                    errors.append(f"Failed to process {slug}")

            await browser.close()

        return CrawlResult(pages=pages, pages_found=len(batch), errors=errors)

    async def _discover(self, page, base_url: str) -> tuple[str, list[str]]:
        await page.goto(base_url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(5000)

        project = self._extract_project(base_url)

        for _ in range(50):
            nodes = await page.evaluate("""
                () => {
                    const containers = document.querySelectorAll('.CHTree_nodeContainer');
                    const result = [];
                    containers.forEach(c => {
                        const ul = c.querySelector(':scope > ul');
                        if (ul && ul.classList.contains('CHTree_nodeChildrenCollapsed')) {
                            const a = c.querySelector(':scope > a');
                            const nodeId = a ? a.getAttribute('data-node-id') : null;
                            if (nodeId) result.push(nodeId);
                        }
                    });
                    return result;
                }
            """)
            if not nodes:
                break
            for node_id in nodes:
                try:
                    await page.click(f"a[data-node-id='{node_id}'] .CHTree_btn", timeout=3000)
                    await page.wait_for_timeout(200)
                except Exception:
                    pass

        links = await page.eval_on_selector_all(
            f"a[href*='{project}']",
            "els => els.map(el => el.getAttribute('href'))",
        )

        slugs = []
        for link in links:
            if "#!" in link:
                parts = link.split("#!", 1)[1].split("/", 1)
                if len(parts) > 1 and parts[1]:
                    slugs.append(parts[1])
        seen = set()
        unique = []
        for s in slugs:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return project, unique

    def _extract_project(self, url: str) -> str:
        if "/#!" in url:
            return url.split("/#!")[1].split("/")[0]
        if "#!" in url:
            return url.split("#!")[1].split("/")[0]
        return ""

    def _process(self, data: dict, slug: str) -> ScrapedPage | None:
        vf_html = data.get("viewFrameHtml", "")
        if not vf_html:
            return None
        text_content = extract(
            vf_html,
            include_comments=False,
            include_tables=True,
            include_links=False,
            include_formatting=True,
            favor_recall=True,
            config=traf_config,
        )
        if not text_content or len(text_content.strip()) < 20:
            return None
        title = data.get("title", "") or data.get("pageTitle", "")
        return ScrapedPage(
            url=slug,
            title=title,
            content=text_content,
            word_count=len(text_content.split()),
            fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
