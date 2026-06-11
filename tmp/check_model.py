import json, urllib.request, os

def api(method, path, body=None, tok=None):
    h = {"Content-Type": "application/json"}
    if tok: h["Authorization"] = "Bearer " + tok
    d = json.dumps(body).encode() if body else None
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000"+path, data=d, headers=h, method=method)).read())

t = api("POST", "/api/v1/auth/login", {"username":"admin","password":"admin123"})["access_token"]

r = api("GET", "/api/v1/admin/settings", tok=t)
model = None
lm_url = "http://10.82.4.99:1234/v1"
for s in r.get("settings", []):
    if s["key"] == "rag_embedding_model":
        model = s["value"]
    if s["key"] == "lmstudio_base_url":
        lm_url = s["value"]
    print(s["key"], "=", s["value"])

def embed(texts):
    payload = {"model": model, "input": texts}
    req = urllib.request.Request(
        lm_url + "/embeddings",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return [d["embedding"] for d in resp["data"]]

def cos_sim(a, b):
    return sum(x*y for x,y in zip(a,b)) / (sum(x*x for x in a)**0.5 * sum(y*y for y in b)**0.5)

texts = [
    "опоздания на работу штраф депремирование",
    "рецепт салата оливье с колбасой и горошком",
    "положение о проведении игры самый пунктуальный сотрудник",
]

print("\n--- Без префиксов E5 ---")
embs = embed(texts)
print(f"Dim: {len(embs[0])}")
print(f"опоздания vs оливье: {cos_sim(embs[0], embs[1]):.6f}")
print(f"опоздания vs пунктуальный: {cos_sim(embs[0], embs[2]):.6f}")
print(f"оливье vs пунктуальный: {cos_sim(embs[1], embs[2]):.6f}")

print("\n--- С E5 префиксами ---")
prefixed = ["query: " + texts[0], "passage: " + texts[1], "passage: " + texts[2]]
embs_p = embed(prefixed)
print(f"опоздания vs оливье: {cos_sim(embs_p[0], embs_p[1]):.6f}")
print(f"опоздания vs пунктуальный: {cos_sim(embs_p[0], embs_p[2]):.6f}")
print(f"оливье vs пунктуальный: {cos_sim(embs_p[1], embs_p[2]):.6f}")
