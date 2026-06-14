from pydantic import BaseModel


class StartScrapeRequest(BaseModel):
    site_url: str
    site_name: str
    max_pages: int = 500
    max_depth: int = 10


class ScrapeJobResponse(BaseModel):
    id: str
    site_url: str
    site_name: str
    status: str
    pages_found: int
    pages_scraped: int
    chunks_created: int
    chunks_ingested: int
    errors: list[str]
    max_pages: int
    max_depth: int
    is_active: bool
    created_by: str | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None


class ScrapeListResponse(BaseModel):
    success: bool
    jobs: list[ScrapeJobResponse]
