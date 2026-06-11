import json
import urllib.request
import urllib.error
import math

resp = json.loads(urllib.request.urlopen(
    urllib.request.Request("http://127.0.0.1:8000/api/v1/auth/login",
        json.dumps({"username": "admin", "password": "admin123"}).encode(),
        {"Content-Type": "application/json"})
).read())
token = resp["access_token"]

# Get settings from API
resp = json.loads(urllib.request.urlopen(
    urllib.request.Request("http://127.0.0.1:8000/api/v1/admin/settings",
        headers={"Authorization": "Bearer " + token})
).read())
settings = resp.get("settings", [])
for s in settings:
    k = s.get("key", "")
    if k in ["lmstudio_base_url", "rag_embedding_model", "lmstudio_api_key"]:
        print(f"  {k} = {s.get('value','')}")

base_url = [s["value"] for s in settings if s["key"] == "lmstudio_base_url"][0].rstrip("/")
model = [s["value"] for s in settings if s["key"] == "rag_embedding_model"][0]
api_key = [s["value"] for s in settings if s["key"] == "lmstudio_api_key"][0]

headers = {"Content-Type": "application/json"}
if api_key:
    headers["Authorization"] = "Bearer " + api_key

# Test: embed 2 very different texts
print("\n=== Testing embedding discrimination ===")
texts = [
    "опоздания на работу штраф депремирование",
    "рецепт салата оливье с колбасой и горошком"
]
payload = json.dumps({"model": model, "input": texts}).encode()
req = urllib.request.Request(base_url + "/embeddings", data=payload, headers=headers, method="POST")
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
emb1 = resp["data"][0]["embedding"]
emb2 = resp["data"][1]["embedding"]

dot = sum(a*b for a,b in zip(emb1, emb2))
n1 = math.sqrt(sum(a*a for a in emb1))
n2 = math.sqrt(sum(a*a for a in emb2))
cosine = dot / (n1 * n2)
print(f"Cosine sim: {cosine:.6f}")

# Test: same text should have high sim
payload = json.dumps({"model": model, "input": ["опоздания на работу", "опоздания на работу"]}).encode()
req = urllib.request.Request(base_url + "/embeddings", data=payload, headers=headers, method="POST")
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
e1 = resp["data"][0]["embedding"]
e2 = resp["data"][1]["embedding"]
dot = sum(a*b for a,b in zip(e1, e2))
n1 = math.sqrt(sum(a*a for a in e1))
n2 = math.sqrt(sum(a*a for a in e2))
cosine_self = dot / (n1 * n2)
print(f"Same text sim: {cosine_self:.6f}")

# Compare existing chunk embeddings from "Самый пунктуальный" with our query embedding
print("\n=== Comparing query embedding vs DB chunks ===")
import subprocess
db_code = (
    "import os, asyncio, asyncpg, json, math\n"
    "async def check():\n"
    "  conn = await asyncpg.connect(\n"
    "    host=os.environ.get('DB_HOST','127.0.0.1'),\n"
    "    port=int(os.environ.get('DB_PORT','5432')),\n"
    "    user=os.environ.get('DB_USER','accos'),\n"
    "    password=os.environ.get('DB_PASSWORD','accos'),\n"
    "    database=os.environ.get('DB_NAME','accos'),\n"
    "  )\n"
    "  query_emb = " + json.dumps(emb1) + "\n"
    "  rows = await conn.fetch(\"\"\"\n"
    "    SELECT d.title, c.chunk_index, left(c.content, 120), 1 - (c.embedding <=> $1::vector) AS sim\n"
    "    FROM knowledge_chunks c\n"
    "    JOIN knowledge_documents d ON d.id = c.document_id\n"
    "    WHERE d.deleted_at IS NULL AND d.is_active = TRUE\n"
    "    ORDER BY sim DESC LIMIT 10\n"
    "  \"\"\", query_emb)\n"
    "  for r in rows:\n"
    "    print(f'{float(r[3]):.6f} | {str(r[0])[:45]} | {r[1]:2d} | {str(r[2])[:80]}')\n"
    "  await conn.close()\n"
    "asyncio.run(check())\n"
)
result = subprocess.run(
    ["/opt/accos/.venv/bin/python3", "-c", db_code],
    capture_output=True, text=True, timeout=15
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:300])
