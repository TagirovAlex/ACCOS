from fastapi import FastAPI

from app.api.v1.endpoints import knowledge
from app.modules.base import BaseModule, ModuleSettingDef


class RAGModule(BaseModule):
    name = "rag"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        app.include_router(knowledge.router)

    def get_settings_schema(self) -> list[ModuleSettingDef]:
        return [
            ModuleSettingDef(key="rag_chunk_size", label="Размер чанка", type="number", category="indexing", default=768, is_admin_setting=True, description="Максимум токенов на один чанк"),
            ModuleSettingDef(key="rag_chunk_overlap", label="Перекрытие чанков", type="number", category="indexing", default=150, is_admin_setting=True, description="Перекрытие токенов между соседними чанками"),
            ModuleSettingDef(key="rag_embedding_model", label="Модель эмбеддингов", type="string", category="embedding", default="text-embedding-multilingual-e5-large", is_admin_setting=True, description="Название модели для создания эмбеддингов"),
            ModuleSettingDef(key="rag_top_k", label="Количество результатов", type="number", category="retrieval", default=5, is_admin_setting=True, description="Сколько чанков возвращать при поиске"),
            ModuleSettingDef(key="rag_min_score", label="Минимальная оценка", type="number", category="retrieval", default=0.5, is_admin_setting=True, description="Минимальный порог схожести для результатов поиска"),
            ModuleSettingDef(key="rag_enabled", label="Включено", type="boolean", category="general", default=True, is_admin_setting=True, description="Включить базу знаний"),
            ModuleSettingDef(key="reindex_cron", label="Расписание переиндексации", type="string", category="scheduling", default="0 3 * * *", is_admin_setting=True, description="Cron-выражение для автоматической переиндексации"),
            ModuleSettingDef(key="reindex_mode", label="Режим переиндексации", type="select", category="scheduling", default="all", is_admin_setting=True, description="Режим переиндексации", validation={"options": ["all", "incremental"]}),
            ModuleSettingDef(key="reindex_schedule_enabled", label="Включить расписание", type="boolean", category="scheduling", default=False, is_admin_setting=True, description="Включить автоматическую переиндексацию по расписанию"),
            ModuleSettingDef(key="hidden_doc_folders", label="Скрытые папки", type="string", category="display", default="", is_admin_setting=True, description="Список названий папок через запятую, которые нужно скрыть из списка"),
        ]
