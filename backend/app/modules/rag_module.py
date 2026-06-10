import logging

from app.modules.base import BaseModule

logger = logging.getLogger(__name__)


class RAGModule(BaseModule):
    name = "rag"
    description = "Knowledge base with RAG (Retrieval-Augmented Generation)"

    async def initialize(self):
        logger.info("RAG module initialized")
        return True

    async def shutdown(self):
        logger.info("RAG module shutdown")
        return True
