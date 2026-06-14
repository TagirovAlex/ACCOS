from fastapi import FastAPI
from app.modules.base import BaseModule


class DocumentModule(BaseModule):
    name = "documents"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        pass
