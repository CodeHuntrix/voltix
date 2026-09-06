"""Voltix edge gateway — MQTT subscribe, SQLite buffer, HTTPS forward, AutoCut to MQTT."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("voltix.edge")

CLOUD_URL = os.getenv("CLOUD_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("EDGE_INGEST_API_KEY", "voltix-edge-dev-key")
SITE_ID = os.getenv("SITE_ID", "")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "voltix/telemetry/#")
BUFFER_PATH = Path(os.getenv("EDGE_BUFFER_PATH", "edge_buffer.sqlite"))
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "2.0"))
COMMAND_POLL = float(os.getenv("COMMAND_POLL", "3.0"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))


def init_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS buffer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT NOT NULL,
            created_at REAL NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    return conn


class EdgeGateway:
    def __init__(self) -> None:
        self.conn = init_db(BUFFER_PATH)
        self.client = None
        self._online = True

    def enqueue(self, point: dict) -> None:
        self.conn.execute(
            "INSERT INTO buffer (payload, created_at) VALUES (?, ?)",
            (json.dumps(point), time.time()),
        )
        self.conn.commit()

    def buffer_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM buffer").fetchone()
        return int(row[0])

    async def flush(self) -> int:
        rows = self.conn.execute(
            "SELECT id, payload, attempts FROM buffer ORDER BY id ASC LIMIT ?",
            (BATCH_SIZE,),
        ).fetchall()
        if not rows:
            return 0
        points = [json.loads(r[1]) for r in rows]
        ids = [r[0] for r in rows]
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                resp = await http.post(
                    f"{CLOUD_URL}/api/v1/ingest/telemetry",
                    headers={"X-API-Key": API_KEY},
                    json={"points": points},
                )
                resp.raise_for_status()
            self.conn.executemany("DELETE FROM buffer WHERE id = ?", [(i,) for i in ids])
            self.conn.commit()
            self._online = True
            log.info("flushed %s points (buffer left=%s)", len(ids), self.buffer_count())
            return len(ids)
        except Exception as exc:
            self._online = False
            self.conn.executemany(
                "UPDATE buffer SET attempts = attempts + 1 WHERE id = ?",
                [(i,) for i in ids],
            )
            self.conn.commit()
            log.warning("cloud down — buffering (%s). err=%s", self.buffer_count(), exc)
            return 0

    async def poll_commands(self) -> None:
        params = {"site_id": SITE_ID} if SITE_ID else {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                resp = await http.get(
                    f"{CLOUD_URL}/api/v1/edge/commands",
                    headers={"X-API-Key": API_KEY},
                    params=params,
                )
                resp.raise_for_status()
                commands = resp.json()
            for cmd in commands:
                await self.dispatch_cut(cmd)
        except Exception as exc:
            log.debug("command poll failed: %s", exc)

    async def dispatch_cut(self, cmd: dict) -> None:
        device_id = cmd.get("device_id")
        topic = f"voltix/commands/{device_id or 'broadcast'}"
        payload = json.dumps({"command_id": cmd["id"], "action": "cut", "machine_id": cmd["machine_id"]})
        log.info("AutoCut → MQTT %s %s", topic, payload)
        if self.client and mqtt:
            self.client.publish(topic, payload, qos=1)
        # Ack cloud
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                await http.post(
                    f"{CLOUD_URL}/api/v1/edge/commands/ack",
                    headers={"X-API-Key": API_KEY},
                    json={
                        "command_id": cmd["id"],
                        "success": True,
                        "detail": f"published to {topic}",
                    },
                )
        except Exception as exc:
            log.warning("ack failed: %s", exc)

    def on_mqtt_message(self, _client, _userdata, msg) -> None:
        try:
            data = json.loads(msg.payload.decode())
            # Normalize to ingest contract
            point = {
                "device_id": data["device_id"],
                "machine_id": data["machine_id"],
                "ts": data.get("ts") or datetime.now(timezone.utc).isoformat(),
                "i_rms_a": float(data["i_rms_a"]),
                "v_nominal": float(data.get("v_nominal", 230)),
                "pf_assumed": float(data.get("pf_assumed", 0.85)),
                "kw_est": float(data["kw_est"]),
                "temp_c": data.get("temp_c"),
            }
            self.enqueue(point)
        except Exception as exc:
            log.warning("bad mqtt payload: %s", exc)

    def start_mqtt(self) -> None:
        if mqtt is None:
            log.warning("paho-mqtt not installed — HTTP-only mode (simulator posts direct)")
            return
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="voltix-edge")
        client.on_message = self.on_mqtt_message
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.subscribe(MQTT_TOPIC)
        client.loop_start()
        self.client = client
        log.info("MQTT subscribed %s:%s %s", MQTT_HOST, MQTT_PORT, MQTT_TOPIC)

    async def run(self) -> None:
        self.start_mqtt()
        log.info("edge gateway cloud=%s buffer=%s", CLOUD_URL, BUFFER_PATH)
        while True:
            await self.flush()
            await self.poll_commands()
            await asyncio.sleep(FLUSH_INTERVAL)


def main() -> None:
    gw = EdgeGateway()
    asyncio.run(gw.run())


if __name__ == "__main__":
    main()
