from fastapi import FastAPI

from app.api.v1.endpoints import knowledge
from app.modules.base import BaseModule


class RAGModule(BaseModule):
    name = "rag"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        app.include_router(knowledge.router)

    def get_name(self) -> str:
        return self.name
