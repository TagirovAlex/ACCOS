from fastapi import FastAPI
from app.modules.base import BaseModule


class FileModule(BaseModule):
    name = "files"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        pass
