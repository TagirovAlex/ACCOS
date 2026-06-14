import asyncio
import logging
import os
import traceback
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limit import limiter

from app.core.config import settings, PROJECT_ROOT
from app.core.paths import UPLOADS_DIR, GENERATIONS_DIR, EDITS_DIR, VIDEOS_DIR, AVATARS_DIR
from app.api.v1.endpoints import auth, user, chat, generation, orchestration, admin, knowledge, help as help_endpoint, web_fetch_admin
from app.services.accrual_service import run_auto_accrual
from app.services.queue_worker import queue_worker_loop
from app.services.scheduler_service import start_scheduler, stop_scheduler, update_schedule

from app.services.settings_service import SettingsService
from app.db.session import async_session_factory

import uvicorn

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.DEBUG),
    format="[%(asctime)s] %(levelname)s %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

log_dir = PROJECT_ROOT / "logs"
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / "accos.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(module)s: %(message)s"))
logging.getLogger().addHandler(file_handler)

_accrual_task = None
_queue_worker_task = None
_mcp_server_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _accrual_task, _queue_worker_task, _mcp_server_task

    logger.info("Seeding default settings...")
    try:
        async with async_session_factory() as session:
            svc = SettingsService(session)
            await svc.seed_defaults()
            await session.commit()
    except Exception as e:
        logger.warning(f"Could not seed settings (DB not ready?): {e}")

    logger.info("Starting accrual scheduler...")

    async def accrual_loop():
        while True:
            try:
                interval = await run_auto_accrual()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Accrual loop crashed, restarting: {e}")
                await asyncio.sleep(60)

    _accrual_task = asyncio.create_task(accrual_loop())
    _queue_worker_task = asyncio.create_task(queue_worker_loop())
    logger.info("Queue worker started")
    try:
        await start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start reindex scheduler: {e}")

    logger.info("Starting MCP WebFetch server on port 8100...")
    try:
        from app.mcp.server_app import mcp_starlette
        mcp_config = uvicorn.Config(mcp_starlette, host="0.0.0.0", port=8100, log_level="info", reload=False, workers=1)
        mcp_server = uvicorn.Server(mcp_config)
        _mcp_server_task = asyncio.create_task(mcp_server.serve())
        logger.info("MCP WebFetch server started on http://0.0.0.0:8100/api/v1/mcp/sse")
    except Exception as e:
        logger.warning(f"Failed to start MCP server: {e}")

    yield
    try:
        await stop_scheduler()
    except Exception as e:
        logger.error(f"Failed to stop reindex scheduler: {e}")
    for task in (_accrual_task, _queue_worker_task, _mcp_server_task):
        if task and not task.done():
            task.cancel()
    logger.info("Background tasks stopped")


app = FastAPI(
    title="ACCOS - AI Content & Chat Orchestrator Service",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


static_dir = PROJECT_ROOT / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
GENERATIONS_DIR.mkdir(parents=True, exist_ok=True)
EDITS_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
AVATARS_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_DIR = PROJECT_ROOT / "static" / "knowledge"
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


def _error_detail(request: Request, exc: Exception, status: int, error_id: str) -> dict:
    body = {
        "success": False,
        "error_id": error_id,
        "status_code": status,
        "error": str(exc),
        "request": {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
        },
    }
    if settings.log_level.upper() == "DEBUG":
        body["traceback"] = traceback.format_exc()
    return body


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"[{error_id}] HTTP {exc.status_code} {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_detail(request, exc, exc.status_code, error_id),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"[{error_id}] 500 {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content=_error_detail(request, exc, 500, error_id),
    )

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(generation.router, prefix="/api/v1")
app.include_router(orchestration.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(knowledge.router)
app.include_router(help_endpoint.router)
app.include_router(web_fetch_admin.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
