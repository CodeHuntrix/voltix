from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from sqlalchemy import text
from starlette.responses import Response

from app.api.routes import router
from app.core.config import get_settings
from app.core.db import Base, SessionLocal, engine
from app.core.logging import setup_logging
from app.core.security import decode_token
from app.models import User  # noqa: F401 — register models
from app import models  # noqa: F401
from app.services.ws import ws_manager

settings = get_settings()
REQUESTS = Counter("voltix_api_requests_total", "API requests", ["route"])


async def _ensure_timescale() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Timescale hypertable (ignore if extension unavailable)
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
            await conn.execute(
                text(
                    """
                    SELECT create_hypertable('telemetry', 'time',
                        if_not_exists => TRUE,
                        migrate_data => TRUE)
                    """
                )
            )
        except Exception:
            pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    await _ensure_timescale()
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict:
    db_ok = False
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok, "service": "voltix-api"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.websocket("/ws/sites/{site_id}")
async def site_ws(websocket: WebSocket, site_id: str) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4401)
            return
    except Exception:
        await websocket.close(code=4401)
        return

    from uuid import UUID

    sid = UUID(site_id)
    await ws_manager.connect(sid, websocket)
    try:
        await websocket.send_json({"type": "connected", "site_id": site_id})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(sid, websocket)
    except Exception:
        await ws_manager.disconnect(sid, websocket)
