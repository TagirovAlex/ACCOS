import json
import urllib.request
import math

base_url = "http://10.82.4.99:1234/v1"
api_key = "sk-lm-8nN2J73V:ojuUzseEZSCNEUdku2Gm"
headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}

# List models and test each one that looks like e5
req = urllib.request.Request(base_url + "/models")
resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
models = [m.get("id","") for m in resp.get("data",[])]
print("All models:", models)

e5_models = [m for m in models if "e5" in m.lower()]
print("\nE5 models:", e5_models)

for model in e5_models:
    print(f"\nTesting {model}...")
    try:
        payload = json.dumps({"model": model, "input": ["тест"]}).encode()
        req = urllib.request.Request(base_url + "/embeddings", data=payload, headers=headers, method="POST")
        resp_body = json.loads(urllib.request.urlopen(req, timeout=30).read())
        emb = resp_body["data"][0]["embedding"]
        print(f"  OK: dim={len(emb)}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"  HTTP {e.code}: {err_body[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
