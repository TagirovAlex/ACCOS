from uuid import UUID

import pytest
import sqlalchemy as sa
from unittest.mock import patch, AsyncMock

from app.db.models.chat_queue import ChatQueue
from app.db.session import async_session_factory
from app.services.chat_worker import _process_chat_job


@pytest.mark.asyncio
async def test_create_chat(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    res = await client.post("/api/v1/chat/create", json={
        "title": "Test Chat"
    }, headers=headers)
    data = res.json()
    assert data["id"] is not None
    assert data["title"] == "Test Chat"


@pytest.mark.asyncio
async def test_list_chats(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    res = await client.get("/api/v1/chat/list", headers=headers)
    data = res.json()
    assert "chats" in data


@pytest.mark.asyncio
async def test_send_message(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    create = await client.post("/api/v1/chat/create", json={
        "title": "Chat for message"
    }, headers=headers)
    chat_id = create.json()["id"]

    res = await client.post(f"/api/v1/chat/{chat_id}/send", json={
        "message": "Hello"
    }, headers=headers)
    data = res.json()
    assert data["success"] is True

    history = await client.get(f"/api/v1/chat/{chat_id}", headers=headers)
    hdata = history.json()
    assert hdata["success"] is True
    assert len(hdata["messages"]) == 1
    assert hdata["messages"][0]["role"] == "user"
    assert hdata["messages"][0]["content"] == "Hello"
    assert hdata["has_pending"] is True


@pytest.mark.asyncio
async def test_send_message_queue_processed(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    create = await client.post("/api/v1/chat/create", json={
        "title": "Worker test"
    }, headers=headers)
    chat_id = create.json()["id"]
    sid = UUID(chat_id)

    await client.post(f"/api/v1/chat/{chat_id}/send", json={
        "message": "Test"
    }, headers=headers)

    async with async_session_factory() as db:
        q = (await db.execute(
            sa.select(ChatQueue).where(
                ChatQueue.session_id == sid,
                ChatQueue.status == "queued",
            )
        )).scalar_one_or_none()
        assert q is not None, "Queue job should exist"
        assert q.status == "queued"

        with patch("app.adapters.lmstudio_adapter.LMStudioAdapter.chat_completion",
                   new_callable=AsyncMock) as mock_lm:
            mock_lm.return_value = {
                "success": True,
                "content": "Worker reply!",
                "tokens_input": 10,
                "tokens_output": 5,
            }
            await _process_chat_job(q)

    history = await client.get(f"/api/v1/chat/{chat_id}", headers=headers)
    hdata = history.json()
    assert len(hdata["messages"]) == 2
    assert hdata["messages"][1]["role"] == "assistant"
    assert hdata["messages"][1]["content"] == "Worker reply!"
    assert hdata["has_pending"] is False

    async with async_session_factory() as db:
        q2 = (await db.execute(
            sa.select(ChatQueue).where(ChatQueue.session_id == sid)
        )).scalar_one()
        assert q2.status == "completed"


@pytest.mark.asyncio
async def test_get_chat_history(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    create = await client.post("/api/v1/chat/create", json={
        "title": "History chat"
    }, headers=headers)
    chat_id = create.json()["id"]

    res = await client.get(f"/api/v1/chat/{chat_id}", headers=headers)
    data = res.json()
    assert data["success"] is True
    assert "messages" in data
