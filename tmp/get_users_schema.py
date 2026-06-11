import asyncio, asyncpg

async def get_schema():
    conn = await asyncpg.connect(user='postgres', password='postgres', host='localhost', port=5432, database='accos')
    cols = await conn.fetch(
        "SELECT column_name, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position"
    )
    for c in cols:
        default = c['column_default'] or '-'
        print(f"{c['column_name']:30s} nullable={c['is_nullable']:5s} default={default}")
    await conn.close()

asyncio.run(get_schema())
