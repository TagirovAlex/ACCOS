import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.adapters.lmstudio_adapter import LMStudioAdapter
from app.db.models.chat import ChatMessage
from app.db.models.chat_queue import ChatQueue
from app.db.models.user import User
from app.db.session import async_session_factory
from app.services.economy_service import EconomyService
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


async def _claim_next_chat_job():
    async with async_session_factory() as db:
        async with db.begin():
            result = await db.execute(
                text("""
                    UPDATE chat_queue
                    SET status = 'processing', updated_at = NOW()
                    WHERE id = (
                        SELECT id FROM chat_queue
                        WHERE status = 'queued'
                        ORDER BY created_at
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING id
                """)
            )
            row = result.fetchone()
            if row:
                return await db.get(ChatQueue, row[0])
            return None


async def _update_job_status(queue_id, status, error_message=None, tokens_input=None, tokens_output=None, cost=None):
    async with async_session_factory() as db:
        async with db.begin():
            q = await db.get(ChatQueue, queue_id)
            if not q:
                return
            q.status = status
            q.updated_at = datetime.now(timezone.utc)
            if error_message:
                q.error_message = error_message
            if tokens_input is not None:
                q.tokens_input = tokens_input
            if tokens_output is not None:
                q.tokens_output = tokens_output
            if cost is not None:
                q.cost = cost


async def _process_chat_job(record):
    queue_id = record.id
    sid = record.session_id
    uid = record.user_id
    prompt_messages = json.loads(record.prompt_messages)

    logger.info(f"Processing chat job {queue_id} for session {sid}")

    try:
        async with async_session_factory() as db:
            settings_svc = SettingsService(db)
            api_key = await settings_svc.get("lmstudio_api_key")
            model = await settings_svc.get("lmstudio_model")
            base_url = await settings_svc.get("lmstudio_base_url")
            llm = LMStudioAdapter(api_key=api_key, model=model, base_url=base_url)

        llm_result = await llm.chat_completion(prompt_messages)
        if not llm_result["success"]:
            await _update_job_status(queue_id, "failed", llm_result.get("error", "LLM call failed"))
            logger.error(f"Chat job {queue_id} failed: {llm_result.get('error')}")
            return

        tokens_input = llm_result.get("tokens_input", 0)
        tokens_output = llm_result.get("tokens_output", 0)
        content = llm_result["content"]

        async with async_session_factory() as db:
            economy = EconomyService(db)
            cost = await economy.calculate_cost("llm", tokens_input=tokens_input, tokens_output=tokens_output)

            user = await db.get(User, uid)
            if not user:
                await _update_job_status(queue_id, "failed", "User not found")
                return
            if user.balance < cost:
                await _update_job_status(queue_id, "failed", f"Insufficient balance: {user.balance} < {cost}")
                logger.warning(f"Chat job {queue_id}: insufficient balance for user {uid}")
                return

            user.balance -= cost
            db.add(ChatMessage(
                session_id=sid, role="assistant", content=content,
                tokens_input=tokens_input, tokens_output=tokens_output, cost=cost,
            ))
            q = await db.get(ChatQueue, queue_id)
            if q:
                q.status = "completed"
                q.tokens_input = tokens_input
                q.tokens_output = tokens_output
                q.cost = cost
                q.updated_at = datetime.now(timezone.utc)
            await db.commit()

        logger.info(f"Chat job {queue_id} completed ({tokens_input}↑ {tokens_output}↓ {cost} MS)")

    except Exception as e:
        logger.error(f"Chat job {queue_id} crashed: {e}")
        await _update_job_status(queue_id, "failed", str(e))


async def chat_worker_loop():
    logger.info("Chat worker started")
    while True:
        try:
            record = await _claim_next_chat_job()
            if record:
                await _process_chat_job(record)
            else:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Chat worker error: {e}")
            await asyncio.sleep(5)
