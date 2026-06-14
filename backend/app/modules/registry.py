import logging
from typing import Any

from fastapi import FastAPI

from app.modules.base import BaseModule

logger = logging.getLogger(__name__)


class ModuleRegistry:
    _instance: "ModuleRegistry | None" = None

    def __new__(cls) -> "ModuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules: dict[str, BaseModule] = {}
        return cls._instance

    def register(self, module: BaseModule) -> None:
        name = module.get_name()
        if name in self._modules:
            logger.warning(f"Module '{name}' already registered, overwriting")
        self._modules[name] = module
        logger.info(f"Registered module: {name}")

    def get_module(self, name: str) -> BaseModule | None:
        return self._modules.get(name)

    def get_all_modules(self) -> list[BaseModule]:
        return list(self._modules.values())

    def register_all(self, app: FastAPI) -> None:
        sorted_modules = self._topological_sort()
        for module in sorted_modules:
            module.register_routes(app)
            logger.info(f"Mounted routes for module: {module.get_name()}")

    def startup_all(self) -> None:
        for module in self._modules.values():
            module.on_startup()

    def shutdown_all(self) -> None:
        for module in self._modules.values():
            module.on_shutdown()

    def _topological_sort(self) -> list[BaseModule]:
        modules = list(self._modules.values())
        sorted_list: list[BaseModule] = []
        visited: set[str] = set()

        def dfs(m: BaseModule, path: set[str]) -> None:
            name = m.get_name()
            if name in visited:
                return
            if name in path:
                logger.warning(f"Circular dependency detected for module '{name}', skipping dependency sort")
                return
            path.add(name)
            for dep_name in m.depends_on:
                dep = self._modules.get(dep_name)
                if dep:
                    dfs(dep, path)
            path.remove(name)
            visited.add(name)
            sorted_list.append(m)

        for m in modules:
            if m.get_name() not in visited:
                dfs(m, set())

        remaining = [m for m in modules if m.get_name() not in visited]
        sorted_list.extend(remaining)
        return sorted_list
