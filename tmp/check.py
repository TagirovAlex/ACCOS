import json, urllib.request

def call(method, path, body=None, token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    d = json.dumps(body).encode() if body else None
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000"+path, data=d, headers=h, method=method)).read())

t = call("POST", "/api/v1/auth/login", {"username":"admin","password":"admin123"})["access_token"]

# Check chunks
docs = call("GET", "/api/v1/knowledge/documents?skip=0&limit=3", token=t)
for d in docs:
    rid = d["id"]
    try:
        r = call("GET", "/api/v1/knowledge/"+rid+"/chunks", token=t)
        cs = r.get("chunks",[])
        print(d["title"][:50], "chunks:", len(cs))
        if cs:
            print("  first:", cs[0]["content"][:100].replace("\n","|"))
    except Exception as e:
        print(d["title"][:50], "ERROR:", str(e)[:60])

# Docs count
print("Docs total:", len(docs))

# Search
print("\nSearch 'опоздания':")
r = call("POST", "/api/v1/knowledge/search", {"query":"опоздания"}, token=t)
for doc in r.get("results",[]):
    print(" ", doc.get("document_title","?")[:50])
