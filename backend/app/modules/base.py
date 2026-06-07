from abc import ABC, abstractmethod

from fastapi import FastAPI


class BaseModule(ABC):
    name: str
    depends_on: list[str] = ["core"]

    @abstractmethod
    def register_routes(self, app: FastAPI) -> None:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass
