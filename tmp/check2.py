import json, urllib.request

def call(method, path, body=None, token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    d = json.dumps(body).encode() if body else None
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000"+path, data=d, headers=h, method=method)).read())

t = call("POST", "/api/v1/auth/login", {"username":"admin","password":"admin123"})["access_token"]

docs = call("GET", "/api/v1/knowledge/documents?skip=0&limit=50", token=t)
print("Total docs:", len(docs))

# Check search results now
import subprocess
db_test = (
    "import os, asyncio, asyncpg\n"
    "async def check():\n"
    "  conn = await asyncpg.connect(host=os.environ.get('DB_HOST','127.0.0.1'), port=int(os.environ.get('DB_PORT','5432')), user=os.environ.get('DB_USER','accos'), password=os.environ.get('DB_PASSWORD','accos'), database=os.environ.get('DB_NAME','accos'))\n"
    "  # Count chunks\n"
    "  cnt = await conn.fetchval('SELECT COUNT(*) FROM knowledge_chunks')\n"
    "  docs_cnt = await conn.fetchval('SELECT COUNT(*) FROM knowledge_documents WHERE deleted_at IS NULL AND is_active = TRUE')\n"
    "  print(f'Chunks: {cnt}, Active docs: {docs_cnt}')\n"
    "  # Get embedding dim\n"
    "  dim = await conn.fetchval('SELECT vector_dims(embedding) FROM knowledge_chunks LIMIT 1')\n"
    "  print(f'Vector dim: {dim}')\n"
    "  # Check a doc with опозд content\n"
    "  rows = await conn.fetch(\"SELECT count(*) FROM knowledge_chunks c JOIN knowledge_documents d ON d.id=c.document_id WHERE d.title ILIKE '%пунктуальн%' AND d.deleted_at IS NULL\")\n"
    "  print(f'Punctual doc chunks: {rows[0][0]}')\n"
    "  await conn.close()\n"
    "asyncio.run(check())\n"
)
r = subprocess.run(
    ["/opt/accos/.venv/bin/python3", "-c", db_test],
    capture_output=True, text=True, timeout=15,
    env={**__import__('os').environ, "DB_HOST":"127.0.0.1", "DB_USER":"accos", "DB_PASSWORD":"accos", "DB_NAME":"accos"}
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:300])
