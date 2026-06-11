import asyncio
import asyncpg
import httpx
import bcrypt
import uuid

DB_URL = "postgresql://postgres:postgres@localhost:5432/accos"  # sync URL for asyncpg

async def test_admin_login():
    pool = await asyncpg.create_pool(
        user="postgres", password="postgres",
        host="localhost", port=5432, database="accos"
    )

    test_username = f"testadmin_{uuid.uuid4().hex[:8]}"
    test_password = "TestPass123!"

    async with pool.acquire() as conn:
        hashed = bcrypt.hashpw(test_password.encode(), bcrypt.gensalt()).decode()
        user_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO users (id, username, hashed_password, admin_role, auth_source, balance, is_active, is_admin, permissions, created_at, updated_at)
               VALUES ($1, $2, $3, 'admin', 'local', 100, TRUE, FALSE, 'chat', NOW(), NOW())""",
            user_id, test_username, hashed
        )
        print(f"Created test user: {test_username} with admin_role=admin")

    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        # Test login
        r = await client.post("/auth/login", json={
            "username": test_username,
            "password": test_password
        })
        data = r.json()
        print(f"Login response: status={r.status_code}, success={data.get('success')}, is_admin={data.get('is_admin')}, admin_role={data.get('admin_role')}")

        if r.status_code != 200 or not data.get("success"):
            print(f"LOGIN FAILED: {data.get('error')}")
            return False

        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test admin endpoint (e.g. dashboard)
        r2 = await client.get("/admin/dashboard", headers=headers)
        print(f"Dashboard access: status={r2.status_code}")
        if r2.status_code == 200:
            print("SUCCESS: admin_role='admin' can access admin dashboard!")
        else:
            detail = r2.json().get("detail", "unknown")
            print(f"FAILED: Dashboard returned {r2.status_code}: {detail}")

        # Test daily stats
        r3 = await client.get("/admin/daily-stats", headers=headers)
        print(f"Daily stats access: status={r3.status_code}")

    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE username = $1", test_username)
        print(f"Cleaned up test user: {test_username}")

    await pool.close()
    return True

if __name__ == "__main__":
    asyncio.run(test_admin_login())
