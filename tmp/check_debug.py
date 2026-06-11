import json, urllib.request, sys

def api(method, path, body=None, tok=None):
    h = {"Content-Type": "application/json"}
    if tok: h["Authorization"] = "Bearer " + tok
    d = json.dumps(body).encode() if body else None
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000"+path, data=d, headers=h, method=method), timeout=60).read())

t = api("POST", "/api/v1/auth/login", {"username":"admin","password":"admin123"})["access_token"]

# Check DB directly
import asyncio, asyncpg
async def check_db():
    conn = await asyncpg.connect(host="127.0.0.1", port=5432, user="accos", password="accos", database="accos")
    cnt = await conn.fetchval("SELECT COUNT(*) FROM knowledge_chunks")
    dim = await conn.fetchval("SELECT vector_dims(embedding) FROM knowledge_chunks LIMIT 1")
    print(f"Chunks: {cnt}, dim: {dim}")
    
    # Check "пунктуальный" doc has chunks
    rows = await conn.fetch(
        "SELECT d.title, c.id, length(c.embedding::text) as emb_len "
        "FROM knowledge_chunks c JOIN knowledge_documents d ON d.id=c.document_id "
        "WHERE d.title ILIKE '%пунктуальн%' LIMIT 3"
    )
    for r in rows:
        print(f"  {r['title'][:40]:40s} chunk: {str(r['id'])[:8]} emb_len: {r['emb_len']}")

    # Check similarity search directly
    # First get embedding for query
    query = "опоздания"
    # Get doc embedding
    row = await conn.fetchrow("SELECT embedding FROM knowledge_chunks LIMIT 1")
    if row:
        print(f"\nSample embedding: first 5 dims = {row['embedding'][:5]}")
    
    await conn.close()

asyncio.run(check_db())

# Also check: is the search endpoint returning 500?
print("\n=== Search test ===")
try:
    r = api("POST", "/api/v1/knowledge/search", {"query":"опоздания", "top_k":5, "min_score":0.0}, tok=t)
    print(f"Search results: {r}")
except Exception as e:
    print(f"Search error: {e}")
    # Read response body
    import http.client
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=30)
    conn.request("POST", "/api/v1/knowledge/search", 
                 json.dumps({"query":"опоздания","top_k":5,"min_score":0.0}),
                 {"Content-Type":"application/json","Authorization":f"Bearer {t}"})
    resp = conn.getresponse()
    print(f"Status: {resp.status}")
    print(f"Body: {resp.read().decode()[:500]}")
    conn.close()
