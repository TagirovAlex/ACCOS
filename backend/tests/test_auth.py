import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_login_admin_success(client):
    with patch("app.services.auth_service.AuthService._authenticate_ldap") as mock_auth:
        mock_auth.return_value = {
            "authenticated": True, "email": "admin@local",
            "full_name": "Admin", "groups": [],
        }
        res = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "admin123"
        })
        data = res.json()
        assert data["success"] is True
        assert data["access_token"] != ""


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    with patch("app.services.auth_service.AuthService._authenticate_ldap") as mock_auth:
        mock_auth.return_value = {
            "authenticated": False, "error": "Invalid credentials",
        }
        res = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "wrong"
        })
        data = res.json()
        assert data["success"] is False


@pytest.mark.asyncio
async def test_login_new_user_auto_create(client):
    with patch("app.services.auth_service.AuthService._authenticate_ldap") as mock_auth:
        mock_auth.return_value = {
            "authenticated": True, "email": "new@local",
            "full_name": "New User", "groups": [],
        }
        res = await client.post("/api/v1/auth/login", json={
            "username": "newuser", "password": "pass"
        })
        data = res.json()
        assert data["success"] is True
        assert data["access_token"] != ""


@pytest.mark.asyncio
async def test_get_me(client, admin_token):
    res = await client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    data = res.json()
    assert data["success"] is True
    assert data["username"] == "admin"
    assert data["is_admin"] is True
    assert "balance" in data


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_health_check(client):
    res = await client.get("/api/v1/health")
    data = res.json()
    assert data["status"] == "ok"
