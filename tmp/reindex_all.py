import json, urllib.request, time

def api(method, path, body=None, tok=None):
    h = {"Content-Type": "application/json"}
    if tok: h["Authorization"] = "Bearer " + tok
    d = json.dumps(body).encode() if body else None
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000"+path, data=d, headers=h, method=method)).read())

t = api("POST", "/api/v1/auth/login", {"username":"admin","password":"admin123"})["access_token"]

# Start reindex
print("Starting reindex-all...")
try:
    r = api("POST", "/api/v1/knowledge/reindex-all", tok=t)
    print(f"Reindex result: {json.dumps(r, indent=2, ensure_ascii=False)[:300]}")
except Exception as e:
    print(f"Reindex error: {e}")
    # Check if chunk count is already 0
    import asyncpg, os
    async def check():
        import asyncio
        conn = await asyncpg.connect(
            host=os.environ.get("DB_HOST", "127.0.0.1"), port=int(os.environ.get("DB_PORT", 5432)),
            user=os.environ.get("DB_USER", "accos"), password=os.environ.get("DB_PASSWORD", "accos"),
            database=os.environ.get("DB_NAME", "accos")
        )
        cnt = await conn.fetchval("SELECT COUNT(*) FROM knowledge_chunks")
        dim = await conn.fetchval("SELECT vector_dims(embedding) FROM knowledge_chunks LIMIT 1") if cnt > 0 else "N/A"
        print(f"Chunks: {cnt}, dim: {dim}")
        await conn.close()
    import asyncio
    asyncio.run(check())
