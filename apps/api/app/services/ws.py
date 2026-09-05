"""In-memory WebSocket fanout for site live updates."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, site_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms[str(site_id)].add(websocket)

    async def disconnect(self, site_id: UUID, websocket: WebSocket) -> None:
        async with self._lock:
            self._rooms[str(site_id)].discard(websocket)

    async def broadcast(self, site_id: UUID, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, default=str)
        async with self._lock:
            sockets = list(self._rooms.get(str(site_id), set()))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(site_id, ws)


ws_manager = ConnectionManager()
