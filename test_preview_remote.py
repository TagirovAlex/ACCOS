import asyncio, httpx

async def test():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as c:
        r = await c.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        print("login:", r.status_code)
        token = r.json().get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"}

        # Upload a test document
        files = {"file": ("test.txt", b"Hello World Preview Test", "text/plain")}
        r2 = await c.post("/api/v1/knowledge/upload", data={"title": "Test Doc"}, files=files, headers=headers)
        print("upload:", r2.status_code, r2.json())
        doc_id = r2.json().get("document_id", "")

        # Check preview
        r3 = await c.get(f"/api/v1/knowledge/{doc_id}/preview", headers=headers)
        print("preview status:", r3.status_code)
        print("preview headers:", dict(r3.headers))
        print("preview body preview:", r3.text[:500])

asyncio.run(test())
