import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from uuid import UUID

from app.adapters.lmstudio_adapter import LMStudioAdapter
from app.adapters.web_fetch_adapter import WebFetchAdapter
from app.db.models.chat import ChatMessage
from app.db.models.chat_queue import ChatQueue
from app.db.models.doc_template import GeneratedDocument
from app.db.models.user import User
from app.db.session import async_session_factory
from app.services.economy_service import EconomyService
from app.services.settings_service import SettingsService
from app.services import compute_service
from app.services import document_generator_service

logger = logging.getLogger(__name__)

WEB_FETCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_web_page",
            "description": "Fetch a web page URL and return its content as markdown. "
                            "Useful when you need to read articles, documentation, or any web content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "max_chars": {"type": "number", "description": "Maximum characters to return", "default": 10000},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_page",
            "description": "Search for a query within a fetched web page. "
                            "Useful when you need to find specific information on a page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL of the page to search"},
                    "query": {"type": "string", "description": "Text to search for"},
                    "max_chars": {"type": "number", "description": "Maximum context characters around match", "default": 5000},
                },
                "required": ["url", "query"],
            },
        },
    },
]

_chat_worker_running = False


async def _claim_next_chat_job():
    async with async_session_factory() as db:
        async with db.begin():
            result = await db.execute(
                __import__("sqlalchemy").text("""
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


async def _is_cancelled(queue_id):
    async with async_session_factory() as db:
        q = await db.get(ChatQueue, queue_id)
        return q and q.status == "cancelling"


async def _process_chat_job(record):
    queue_id = record.id
    sid = record.session_id
    uid = record.user_id
    prompt_messages = json.loads(record.prompt_messages)

    logger.info(f"Processing chat job {queue_id} for session {sid}")

    try:
        if await _is_cancelled(queue_id):
            await _update_job_status(queue_id, "cancelled")
            logger.info(f"Chat job {queue_id} cancelled before start")
            return

        async with async_session_factory() as db:
            settings_svc = SettingsService(db)
            api_key = await settings_svc.get("lmstudio_api_key")
            model = await settings_svc.get("lmstudio_model")
            base_url = await settings_svc.get("lmstudio_base_url")
            llm = LMStudioAdapter(api_key=api_key, model=model, base_url=base_url)

        messages = prompt_messages
        total_tokens_input = 0
        total_tokens_output = 0

        for round_num in range(6):
            async def llm_call(current_messages=messages):
                return await llm.chat_completion(current_messages, tools=WEB_FETCH_TOOLS)

            async def poll_cancel():
                while True:
                    await asyncio.sleep(2)
                    if await _is_cancelled(queue_id):
                        return True

            llm_task = asyncio.create_task(llm_call())
            poll_task = asyncio.create_task(poll_cancel())

            done, pending = await asyncio.wait(
                [llm_task, poll_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass

            if poll_task in done and not poll_task.exception() and poll_task.result():
                await _update_job_status(queue_id, "cancelled")
                logger.info(f"Chat job {queue_id} cancelled during generation")
                return

            llm_result = llm_task.result()

            if not llm_result["success"]:
                await _update_job_status(queue_id, "failed", llm_result.get("error", "LLM call failed"))
                logger.error(f"Chat job {queue_id} failed: {llm_result.get('error')}")
                return

            if await _is_cancelled(queue_id):
                await _update_job_status(queue_id, "cancelled")
                logger.info(f"Chat job {queue_id} cancelled after response")
                return

            total_tokens_input += llm_result.get("tokens_input", 0)
            total_tokens_output += llm_result.get("tokens_output", 0)

            tool_calls = llm_result.get("tool_calls")
            if not tool_calls:
                content = llm_result["content"]
                break

            logger.info(f"Chat job {queue_id} round {round_num + 1}: {len(tool_calls)} tool call(s)")
            for tc in tool_calls:
                fn = tc["function"]
                name = fn["name"]
                try:
                    args = json.loads(fn["arguments"])
                except json.JSONDecodeError:
                    args = {}

                if name == "fetch_web_page":
                    fetcher = WebFetchAdapter()
                    result = await fetcher.fetch(args.get("url", ""), max_chars=args.get("max_chars", 10000))
                    tool_content = result.get("content", result.get("error", "No content"))
                    if result.get("links"):
                        tool_content += "\n\nLinks on this page:\n" + "\n".join(
                            f"- {l['text']}: {l['url']}" for l in result["links"][:20]
                        )
                elif name == "search_in_page":
                    fetcher = WebFetchAdapter()
                    fetch_result = await fetcher.fetch(args.get("url", ""), max_chars=args.get("max_chars", 10000) * 2)
                    if not fetch_result["success"]:
                        tool_content = f"Error: {fetch_result['error']}"
                    else:
                        text = fetch_result["content"]
                        query = args.get("query", "")
                        idx = text.lower().find(query.lower())
                        if idx == -1:
                            tool_content = f"Query '{query}' not found on the page."
                        else:
                            half = args.get("max_chars", 5000) // 2
                            start = max(0, idx - half)
                            end = min(len(text), idx + len(query) + half)
                            tool_content = f"Found context around '{query}':\n\n{text[start:end]}"
                else:
                    tool_content = f"Unknown tool: {name}"

                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": tool_content[:50000]})
        else:
            await _update_job_status(queue_id, "failed", "Max tool call rounds exceeded")
            logger.warning(f"Chat job {queue_id}: exceeded max tool rounds")
            return

        content = _process_compute_blocks(content, str(sid))
        content = await _process_generate_block(content, uid, sid, queue_id, total_tokens_input, total_tokens_output)

        async with async_session_factory() as db:
            economy = EconomyService(db)
            cost = await economy.calculate_cost("llm", tokens_input=total_tokens_input, tokens_output=total_tokens_output)

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
                tokens_input=total_tokens_input, tokens_output=total_tokens_output, cost=cost,
            ))
            q = await db.get(ChatQueue, queue_id)
            if q:
                q.status = "completed"
                q.tokens_input = total_tokens_input
                q.tokens_output = total_tokens_output
                q.cost = cost
                q.updated_at = datetime.now(timezone.utc)
            await db.commit()

        logger.info(f"Chat job {queue_id} completed ({total_tokens_input}↑ {total_tokens_output}↓ {cost} MS)")

    except asyncio.CancelledError:
        await _update_job_status(queue_id, "cancelled")
        logger.info(f"Chat job {queue_id} cancelled via task cancellation")
    except Exception as e:
        logger.error(f"Chat job {queue_id} crashed: {e}")
        await _update_job_status(queue_id, "failed", str(e))


async def _drain_queue():
    while True:
        record = await _claim_next_chat_job()
        if not record:
            break
        await _process_chat_job(record)


async def ensure_chat_worker():
    global _chat_worker_running
    if _chat_worker_running:
        return
    _chat_worker_running = True
    logger.info("Chat worker started (on-demand)")
    try:
        await _drain_queue()
    finally:
        _chat_worker_running = False
        logger.info("Chat worker stopped (queue empty)")


def _process_compute_blocks(content: str, session_id: str) -> str:
    def _replace(m):
        code = m.group(1).strip().split("\n")
        result = compute_service.execute(session_id, code)
        if not result["success"]:
            return f"[COMPUTE]\nError: {result.get('error', 'unknown')}\n[/COMPUTE]"
        lines = []
        for r in result["results"]:
            lines.append(r)
        output = "\n".join(lines)
        if result["variables"]:
            vars_str = ", ".join(f"{k}={v}" for k, v in result["variables"].items())
            output += f"\n\n_Variables: {vars_str}_"
        return f"**_Computed result_:**\n```\n{output}\n```"

    return re.sub(r"\[COMPUTE\](.*?)\[/COMPUTE\]", _replace, content, flags=re.DOTALL)


async def _process_generate_block(content: str, user_id: str, session_id, queue_id, tokens_input: int, tokens_output: int) -> str:
    try:
        payload = json.loads(content)
        if not isinstance(payload, dict) or "_generate" not in payload:
            return content
        gen = payload["_generate"]
        template_name = gen.get("template")
        variables = gen.get("variables", {})
        output_format = gen.get("format", "pdf")
    except (json.JSONDecodeError, TypeError):
        return content

    async with async_session_factory() as db:
        from app.repositories.template_repository import DocTemplateRepository
        repo = DocTemplateRepository(db)
        templates = await repo.get_all()
        template = next((t for t in templates if t.name.lower() == template_name.lower()), None)
        if not template:
            return content + f"\n\nError: template '{template_name}' not found"

        from app.services.document_generator_service import DocumentGeneratorService
        gen_svc = DocumentGeneratorService()
        output_path = gen_svc.generate(output_format, template_path=template.file_path, fields=variables)

        from pathlib import Path
        p = Path(output_path)
        filename = f"{template_name}_{p.name}"
        doc = GeneratedDocument(
            user_id=UUID(user_id) if user_id else None,
            session_id=session_id,
            template_id=template.id,
            source_file=filename,
            file_path=output_path,
            format=output_format,
            prompt=json.dumps(variables),
        )
        db.add(doc)
        await db.commit()

    return content + f"\n\n📄 **Document generated:** [{filename}](/api/v1/generated-documents/{doc.id}/download)"
