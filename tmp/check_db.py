import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect(
        host="127.0.0.1", port=5432,
        user="accos", password="accos", database="accos"
    )
    cnt = await conn.fetchval("SELECT COUNT(*) FROM knowledge_chunks")
    print(f"Chunks: {cnt}")
    if cnt > 0:
        dim = await conn.fetchval("SELECT vector_dims(embedding) FROM knowledge_chunks LIMIT 1")
        print(f"Vector dim: {dim}")
    row = await conn.fetchrow(
        "SELECT column_name, udt_name, character_maximum_length "
        "FROM information_schema.columns "
        "WHERE table_name='knowledge_chunks' AND column_name='embedding'"
    )
    if row:
        print(f"Column def: {row['column_name']} {row['udt_name']} max={row['character_maximum_length']}")
    await conn.close()

asyncio.run(check())
