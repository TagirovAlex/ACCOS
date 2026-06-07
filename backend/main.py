import asyncio
import logging
import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.endpoints import auth, user, chat, generation, orchestration, admin
from app.services.accrual_service import run_auto_accrual

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.DEBUG),
    format="[%(asctime)s] %(levelname)s %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / "accos.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(module)s: %(message)s"))
logging.getLogger().addHandler(file_handler)

_accrual_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _accrual_task
    logger.info("Starting accrual scheduler...")

    async def accrual_loop():
        while True:
            await run_auto_accrual()
            await asyncio.sleep(3600)

    _accrual_task = asyncio.create_task(accrual_loop())
    yield
    if _accrual_task:
        _accrual_task.cancel()
        logger.info("Accrual scheduler stopped")


app = FastAPI(
    title="ACCOS - AI Content & Chat Orchestrator Service",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="../static"), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)},
    )

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(generation.router, prefix="/api/v1")
app.include_router(orchestration.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
