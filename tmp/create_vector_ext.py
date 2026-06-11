import asyncio, asyncpg

async def main():
    conn = await asyncpg.connect(user='postgres', password='postgres', host='localhost', port=5432, database='accos')
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    print("vector extension created")
    await conn.close()

asyncio.run(main())
