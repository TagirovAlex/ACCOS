import json, urllib.request, time

def api(method, path, body=None, tok=None):
    h = {"Content-Type": "application/json"}
    if tok: h["Authorization"] = "Bearer " + tok
    d = json.dumps(body).encode() if body else None
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000"+path, data=d, headers=h, method=method), timeout=600).read())

t = api("POST", "/api/v1/auth/login", {"username":"admin","password":"admin123"})["access_token"]

print("Starting reindex-all...")
t0 = time.time()
r = api("POST", "/api/v1/knowledge/reindex-all", tok=t)
elapsed = time.time() - t0
print(f"Done in {elapsed:.0f}s")
print(json.dumps(r, indent=2, ensure_ascii=False))
