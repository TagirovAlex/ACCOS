import subprocess
import os

# Check alembic current
r = subprocess.run(
    ["/opt/accos/.venv/bin/alembic", "-c", "/opt/accos/config/alembic.ini", "current"],
    capture_output=True, text=True, timeout=15
)
print("Alembic current:", r.stdout.strip())

# Check column via DB env vars
import asyncio, asyncpg
async def check():
    conn = await asyncpg.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ.get("DB_USER", "accos"),
        password=os.environ.get("DB_PASSWORD", "accos"),
        database=os.environ.get("DB_NAME", "accos"),
    )
    row = await conn.fetchrow(
        "SELECT column_name, udt_name FROM information_schema.columns "
        "WHERE table_name='knowledge_chunks' AND column_name='embedding'"
    )
    print(f"Column: {row[0]}, type: {row[1]}" if row else "No embedding column!")
    
    # Check if vector dim works
    try:
        dim = await conn.fetchval("SELECT vector_dims(embedding) FROM knowledge_chunks LIMIT 1")
        print(f"Vector dim: {dim}")
    except:
        # No chunks or column issue
        cnt = await conn.fetchval("SELECT COUNT(*) FROM knowledge_chunks")
        print(f"Chunks count: {cnt} (maybe empty)")
    
    await conn.close()
asyncio.run(check())
