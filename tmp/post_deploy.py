import json
import urllib.request

def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request("http://127.0.0.1:8000" + path, data=data, headers=headers, method=method)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

r = call("POST", "/api/v1/auth/login", {"username": "admin", "password": "admin123"})
token = r["access_token"]

print("=== Updating settings ===")
r = call("PUT", "/api/v1/admin/settings/rag_embedding_model", {"value": "text-embedding-multilingual-e5-small"}, token=token)
print("rag_embedding_model update:", r)

# Verify
resp = call("GET", "/api/v1/admin/settings", token=token)
for s in resp.get("settings", []):
    key = s.get("key", "")
    if key in ["rag_embedding_model", "lmstudio_base_url"]:
        print(f"  {key} = {s.get('value','')}")

print("\n=== Reindexing all documents ===")
result = call("POST", "/api/v1/knowledge/reindex-all", token=token)
print("Reindex:", json.dumps(result, indent=2, ensure_ascii=False))

print("\n=== Testing search: 'опоздания на работу штраф' ===")
result = call("POST", "/api/v1/knowledge/search", {"query": "опоздания на работу штраф"}, token=token)
print(f"Results: {len(result.get('results',[]))}")
for doc in result.get("results", []):
    title = doc.get("document_title", "?")
    for c in doc.get("chunks", [])[:1]:
        sim = c.get("similarity", 0)
        content = c.get("content", "")[:150].replace(chr(10), "|")
        print(f"  sim={sim:.4f} | {title[:50]}")
        print(f"    {content}")

print("\n=== Testing search: 'как в компании относятся к опозданиям' ===")
result = call("POST", "/api/v1/knowledge/search", {"query": "как в компании относятся к опозданиям"}, token=token)
print(f"Results: {len(result.get('results',[]))}")
for doc in result.get("results", []):
    title = doc.get("document_title", "?")
    for c in doc.get("chunks", [])[:1]:
        sim = c.get("similarity", 0)
        content = c.get("content", "")[:150].replace(chr(10), "|")
        print(f"  sim={sim:.4f} | {title[:50]}")
        print(f"    {content}")
