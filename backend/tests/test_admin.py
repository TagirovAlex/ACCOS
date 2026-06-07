import pytest


@pytest.mark.asyncio
async def test_admin_list_users(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/admin/users", headers=headers)
    data = res.json()
    assert data["success"] is True
    assert "users" in data


@pytest.mark.asyncio
async def test_admin_list_groups(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/admin/groups", headers=headers)
    data = res.json()
    assert data["success"] is True
    assert "groups" in data


@pytest.mark.asyncio
async def test_admin_create_group(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.post("/api/v1/admin/groups", json={
        "name": "Test Group",
        "ad_group_dn": "CN=TestGroup,DC=domain,DC=local",
        "permissions": "full_access",
        "start_balance": 500.0,
    }, headers=headers)
    data = res.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_admin_list_settings(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/admin/settings", headers=headers)
    data = res.json()
    assert data["success"] is True
    assert "settings" in data


@pytest.mark.asyncio
async def test_admin_list_chats(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/admin/chats", headers=headers)
    data = res.json()
    assert data["success"] is True
    assert "chats" in data


@pytest.mark.asyncio
async def test_admin_list_generations(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/admin/generations", headers=headers)
    data = res.json()
    assert data["success"] is True
    assert "generations" in data


@pytest.mark.asyncio
async def test_admin_list_assets(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/admin/assets", headers=headers)
    data = res.json()
    assert data["success"] is True
    assert "assets" in data


@pytest.mark.asyncio
async def test_admin_unauthorized(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    res = await client.get("/api/v1/admin/users", headers=headers)
    assert res.status_code == 403
