import pytest
from unittest.mock import patch


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

    with patch("app.adapters.lmstudio_adapter.LMStudioAdapter.chat_completion") as mock_lm:
        mock_lm.return_value = {
            "success": True,
            "content": "Hello from AI!",
            "tokens_input": 10,
            "tokens_output": 5,
        }
        res = await client.post(f"/api/v1/chat/{chat_id}/send", json={
            "message": "Hello"
        }, headers=headers)
    data = res.json()
    assert data["success"] is True
    assert data["message"] == "Hello from AI!"


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
