import json, urllib.request

def api(method, path, body=None, tok=None):
    h = {"Content-Type": "application/json"}
    if tok: h["Authorization"] = "Bearer " + tok
    d = json.dumps(body).encode() if body else None
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000"+path, data=d, headers=h, method=method)).read())

t = api("POST", "/api/v1/auth/login", {"username":"admin","password":"admin123"})["access_token"]

# Check indexing status
docs = api("GET", "/api/v1/knowledge/documents?skip=0&limit=50", tok=t)

pending = [d for d in docs if d.get("status") == "pending"]
indexing = [d for d in docs if d.get("status") == "indexing"]
ready = [d for d in docs if d.get("status") == "ready"]
failed = [d for d in docs if d.get("status") == "failed"]
print(f"Docs: {len(docs)} total, {len(ready)} ready, {len(pending)} pending, {len(indexing)} indexing, {len(failed)} failed")

# Find "самый пунктуальный" doc specifically
punct = [d for d in docs if "пунктуальн" in d.get("title","").lower()]
for p in punct:
    print(f"  Found: {p['title'][:60]} — status: {p['status']}")

# If all ready, test search
if ready == len(docs) or True:
    print("\nSearch 'опоздания':")
    r = api("POST", "/api/v1/knowledge/search", {"query":"опоздания"}, tok=t)
    for doc in r.get("results",[]):
        print(f"  {doc.get('document_title','?')[:60]} (score: {doc.get('chunks',[{}])[0].get('similarity',0):.4f})")

    print("\nSearch 'штраф':")
    r = api("POST", "/api/v1/knowledge/search", {"query":"штраф"}, tok=t)
    for doc in r.get("results",[]):
        print(f"  {doc.get('document_title','?')[:60]} (score: {doc.get('chunks',[{}])[0].get('similarity',0):.4f})")
