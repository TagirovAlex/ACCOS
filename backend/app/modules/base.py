from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI


@dataclass
class ModuleSettingDef:
    key: str
    label: str
    type: str = "string"
    category: str = "general"
    default: Any = ""
    is_user_setting: bool = False
    is_admin_setting: bool = True
    validation: dict | None = None
    description: str = ""


@dataclass
class MenuItemDef:
    label: str
    path: str
    icon: str = "Settings"
    permission: str | None = None
    order: int = 100


class BaseModule(ABC):
    name: str
    depends_on: list[str] = ["core"]

    @abstractmethod
    def register_routes(self, app: FastAPI) -> None:
        pass

    def get_name(self) -> str:
        return self.name

    def get_settings_schema(self) -> list[ModuleSettingDef]:
        return []

    def get_admin_menu(self) -> list[MenuItemDef]:
        return []

    def get_user_menu(self) -> list[MenuItemDef]:
        return []

    def on_startup(self) -> None:
        pass

    def on_shutdown(self) -> None:
        pass
