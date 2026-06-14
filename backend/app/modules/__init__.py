from app.modules.base import BaseModule, ModuleSettingDef, MenuItemDef
from app.modules.registry import ModuleRegistry
from app.modules.chat_module import ChatModule
from app.modules.comfyui_module import ComfyUIModule
from app.modules.rag_module import RAGModule
from app.modules.web_fetch_module import WebFetchModule
from app.modules.doc_scraper_module import DocScraperModule
from app.modules.file_module import FileModule

__all__ = [
    "BaseModule", "ModuleSettingDef", "MenuItemDef",
    "ModuleRegistry",
    "ChatModule", "ComfyUIModule", "RAGModule",
    "WebFetchModule", "DocScraperModule", "FileModule",
]
