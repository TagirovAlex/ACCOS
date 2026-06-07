from fastapi import FastAPI

from app.api.v1.endpoints import generation
from app.modules.base import BaseModule


class ComfyUIModule(BaseModule):
    name = "comfyui"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        app.include_router(generation.router, prefix="/api/v1")

    def get_name(self) -> str:
        return self.name
