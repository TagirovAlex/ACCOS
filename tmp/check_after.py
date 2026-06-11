import json, urllib.request

def api(method, path, body=None, tok=None):
    h = {"Content-Type": "application/json"}
    if tok: h["Authorization"] = "Bearer " + tok
    d = json.dumps(body).encode() if body else None
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000"+path, data=d, headers=h, method=method), timeout=60).read())

t = api("POST", "/api/v1/auth/login", {"username":"admin","password":"admin123"})["access_token"]

# Check doc statuses
docs = api("GET", "/api/v1/knowledge/documents?skip=0&limit=50", tok=t)
pending = [d for d in docs if d.get("status") == "pending"]
indexing = [d for d in docs if d.get("status") == "indexing"]
ready = [d for d in docs if d.get("status") == "ready"]
failed = [d for d in docs if d.get("status") == "failed"]
print(f"Total: {len(docs)}, ready={len(ready)}, pending={len(pending)}, indexing={len(indexing)}, failed={len(failed)}")

if ready:
    print("\nSearch 'опоздания':")
    r = api("POST", "/api/v1/knowledge/search", {"query":"опоздания"}, tok=t)
    for doc in r.get("results",[]):
        sim = doc.get("chunks",[{}])[0].get("similarity",0)
        print(f"  {doc.get('document_title','?')[:60]} (sim: {sim:.4f})")

    print("\nSearch 'пунктуальный':")
    r = api("POST", "/api/v1/knowledge/search", {"query":"пунктуальный"}, tok=t)
    for doc in r.get("results",[]):
        sim = doc.get("chunks",[{}])[0].get("similarity",0)
        print(f"  {doc.get('document_title','?')[:60]} (sim: {sim:.4f})")
