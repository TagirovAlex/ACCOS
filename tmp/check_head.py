import os, re
for f in sorted(os.listdir('C:\\Github\\ACCOS\\backend\\alembic\\versions')):
    if not f.endswith('.py') or f.startswith('__init__'):
        continue
    content = open(f'C:\\Github\\ACCOS\\backend\\alembic\\versions\\{f}').read()
    rev = re.search(r"^revision: str = '([^']+)'", content, re.M)
    down = re.search(r"^down_revision:.*?= '([^']+)'", content, re.M)
    down = down.group(1) if down else 'None'
    # Check if this revision is referenced by any other as down_revision
    referenced = any(down == rev.group(1) for other_f in os.listdir('C:\\Github\\ACCOS\\backend\\alembic\\versions') if other_f != f and other_f.endswith('.py') and not other_f.startswith('__init__') for rev2 in [re.search(r"^revision: str = '([^']+)'", open(f'C:\\Github\\ACCOS\\backend\\alembic\\versions\\{other_f}').read(), re.M)] if rev2)
