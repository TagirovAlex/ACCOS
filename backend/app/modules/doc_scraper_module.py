from fastapi import FastAPI

from app.api.v1.endpoints import doc_scraper_admin
from app.modules.base import BaseModule, ModuleSettingDef


class DocScraperModule(BaseModule):
    name = "doc_scraper"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        app.include_router(doc_scraper_admin.router, prefix="/api/v1")
