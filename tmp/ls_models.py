import urllib.request
import json

req = urllib.request.Request("http://10.82.4.99:1234/v1/models")
resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
for m in resp.get("data", []):
    mid = m.get("id", "?")
    print(mid)
