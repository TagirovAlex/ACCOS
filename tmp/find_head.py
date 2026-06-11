import os, re
d = {}
for f in os.listdir('C:\\Github\\ACCOS\\backend\\alembic\\versions'):
    if not f.endswith('.py') or f.startswith('__init__'):
        continue
    content = open(f'C:\\Github\\ACCOS\\backend\\alembic\\versions\\{f}').read()
    rev = re.search(r"^revision: str = '([^']+)'", content, re.M)
    down = re.search(r"^down_revision:.*?= '([^']+)'", content, re.M)
    if rev:
        d[rev.group(1)] = down.group(1) if down else 'None'
for k, v in d.items():
    print(f'{k} <- {v}')
