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
            ModuleSettingDef(key="rag_chunk_size", label="Chunk size", type="number", category="indexing", default=768, is_admin_setting=True, description="Max tokens per chunk"),
            ModuleSettingDef(key="rag_chunk_overlap", label="Chunk overlap", type="number", category="indexing", default=150, is_admin_setting=True, description="Token overlap between chunks"),
            ModuleSettingDef(key="rag_embedding_model", label="Embedding model", type="string", category="embedding", default="text-embedding-multilingual-e5-large", is_admin_setting=True, description="Model name for embeddings"),
            ModuleSettingDef(key="rag_top_k", label="Top K", type="number", category="retrieval", default=5, is_admin_setting=True, description="Number of chunks to retrieve"),
            ModuleSettingDef(key="rag_min_score", label="Min score", type="number", category="retrieval", default=0.5, is_admin_setting=True, description="Minimum similarity score"),
            ModuleSettingDef(key="rag_enabled", label="Enabled", type="boolean", category="general", default=True, is_admin_setting=True, description="Enable RAG"),
            ModuleSettingDef(key="reindex_cron", label="Reindex cron", type="string", category="scheduling", default="0 3 * * *", is_admin_setting=True, description="Cron expression for reindex"),
            ModuleSettingDef(key="reindex_mode", label="Reindex mode", type="select", category="scheduling", default="all", is_admin_setting=True, description="Reindex mode", validation={"options": ["all", "incremental"]}),
            ModuleSettingDef(key="reindex_schedule_enabled", label="Schedule enabled", type="boolean", category="scheduling", default=False, is_admin_setting=True, description="Enable scheduled reindex"),
            ModuleSettingDef(key="hidden_doc_folders", label="Hidden folders", type="string", category="display", default="", is_admin_setting=True, description="Comma-separated folder names to hide"),
        ]
