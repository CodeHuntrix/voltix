#!/bin/sh
set -e
echo "Waiting for database..."
python - <<'PY'
import asyncio
import os
import time

import asyncpg

url = os.environ.get("DATABASE_URL", "postgresql://voltix:voltix@db:5432/voltix")
url = url.replace("postgresql+asyncpg://", "postgresql://")

async def wait():
    for _ in range(60):
        try:
            conn = await asyncpg.connect(url)
            await conn.close()
            print("db ready")
            return
        except Exception as e:
            print("db wait", e)
            await asyncio.sleep(2)
    raise SystemExit("db not ready")

asyncio.run(wait())
PY

python -m app.seed || true
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
