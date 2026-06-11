import re, os

path = "backend/alembic/versions"
for f in sorted(os.listdir(path)):
    if not f.endswith(".py") or f.startswith("__"):
        continue
    content = open(os.path.join(path, f)).read()
    rev_id = re.search(r"Revision ID: (\w+)", content).group(1)
    revises = re.search(r"Revises: (\w+)", content)
    revises = revises.group(1) if revises else "None"
    name = re.search(r'"""(.*?)"""', content, re.DOTALL)
    name = name.group(1).strip() if name else ""
    print(f"{rev_id:30s} revises {revises:30s} {name.split(chr(10))[0]}")
