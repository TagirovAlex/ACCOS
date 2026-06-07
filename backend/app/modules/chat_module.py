from fastapi import FastAPI

from app.api.v1.endpoints import chat
from app.modules.base import BaseModule


class ChatModule(BaseModule):
    name = "chat"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        app.include_router(chat.router, prefix="/api/v1")

    def get_name(self) -> str:
        return self.name
