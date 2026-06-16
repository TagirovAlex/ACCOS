import pytest


@pytest.mark.asyncio
async def test_admin_list_modules(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/admin/modules", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["modules"]) > 0


@pytest.mark.asyncio
async def test_admin_get_chat_settings(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/admin/modules/chat/settings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["settings"]) > 0
    keys = [s["key"] for s in data["settings"]]
    assert "chat_context_messages" in keys
    assert "lmstudio_base_url" in keys


@pytest.mark.asyncio
async def test_admin_update_setting_number_valid(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.put("/api/v1/admin/modules/chat/settings/chat_context_messages", json={"value": "50"}, headers=headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_admin_update_setting_number_invalid(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.put("/api/v1/admin/modules/chat/settings/chat_context_messages", json={"value": "not_a_number"}, headers=headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_admin_update_setting_unknown_module(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.put("/api/v1/admin/modules/nonexistent/settings/foo", json={"value": "bar"}, headers=headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_user_module_settings_empty(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    res = await client.get("/api/v1/user/module-settings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["settings"] == []


@pytest.mark.asyncio
async def test_admin_user_module_settings(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]
    res = await client.get(f"/api/v1/admin/users/{user_id}/module-settings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
