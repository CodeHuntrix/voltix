"""Device telemetry simulator — posts ingest batches (and optional MQTT)."""

from __future__ import annotations

import asyncio
import math
import os
import random
import time
from datetime import datetime, timezone

import httpx

CLOUD_URL = os.getenv("CLOUD_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("EDGE_INGEST_API_KEY", "voltix-edge-dev-key")
INTERVAL = float(os.getenv("SIM_INTERVAL", "2.0"))
SITE_BOOTSTRAP = os.getenv("SIM_USE_SEED", "1") == "1"
SKIP_DEVICES = {
    s.strip() for s in os.getenv("SIM_SKIP_DEVICES", "").split(",") if s.strip()
}

# Fallback static map filled after seed discovery
MACHINES: list[dict] = []


async def discover_machines() -> list[dict]:
    """Login as demo owner and fetch site machines."""
    async with httpx.AsyncClient(timeout=20.0) as http:
        # wait for API
        for _ in range(60):
            try:
                r = await http.get(f"{CLOUD_URL}/health")
                if r.status_code == 200 and r.json().get("db"):
                    break
            except Exception:
                pass
            await asyncio.sleep(2)

        login = await http.post(
            f"{CLOUD_URL}/api/v1/auth/login",
            json={"email": "owner@voltix.demo", "password": "voltix-demo"},
        )
        if login.status_code != 200:
            raise RuntimeError(f"login failed: {login.text}")
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        orgs = (await http.get(f"{CLOUD_URL}/api/v1/orgs", headers=headers)).json()
        org_id = orgs[0]["id"]
        sites = (await http.get(f"{CLOUD_URL}/api/v1/orgs/{org_id}/sites", headers=headers)).json()
        site_id = sites[0]["id"]
        machines = (
            await http.get(f"{CLOUD_URL}/api/v1/sites/{site_id}/machines", headers=headers)
        ).json()
        print(f"simulator site={site_id} machines={len(machines)}")
        return machines


def phase_for(machine_name: str, t: float) -> str:
    """Cycle machines through OFF / ACTIVE / IDLE / WASTE patterns."""
    cycle = (t / 60.0 + hash(machine_name) % 7) % 10
    if "Compressor" in machine_name:
        if cycle < 2:
            return "OFF"
        if cycle < 5:
            return "ACTIVE"
        if cycle < 8:
            return "WASTE"  # running unloaded
        return "IDLE"
    if cycle < 1.5:
        return "OFF"
    if cycle < 6:
        return "ACTIVE"
    if cycle < 8:
        return "IDLE"
    return "WASTE"


def sample(machine: dict, t: float) -> dict:
    state = phase_for(machine["name"], t)
    v = machine.get("v_nominal", 230.0)
    pf = machine.get("pf_assumed", 0.85)
    mtype = (machine.get("machine_type") or "").lower()
    name = machine.get("name") or ""

    if "compress" in mtype or "Compressor" in name:
        if state == "OFF":
            i = random.uniform(0.030, 0.042)
        elif state == "ACTIVE":
            i = random.uniform(5.6, 7.4)
        else:
            i = random.uniform(3.55, 3.95)
    elif "laptop" in mtype or "Laptop" in name:
        if state == "OFF":
            i = random.uniform(0.0, 0.008)
        elif state == "ACTIVE":
            i = random.uniform(0.205, 0.225)
        else:
            i = random.uniform(0.160, 0.165)
    elif state == "OFF":
        i = random.uniform(0.0, 0.15)
    elif state == "ACTIVE":
        i = random.uniform(6.0, 14.0) + math.sin(t / 5) * 0.5
    elif state == "IDLE":
        i = random.uniform(0.8, 1.8)
    else:
        i = random.uniform(2.2, 4.5)
    kw = (v * i * pf) / 1000.0
    return {
        "device_id": machine.get("device_id") or f"sim-{machine['id'][:8]}",
        "machine_id": machine["id"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "i_rms_a": round(i, 3),
        "v_nominal": v,
        "pf_assumed": pf,
        "kw_est": round(kw, 4),
        "temp_c": round(30 + random.uniform(0, 12) + (2 if state == "ACTIVE" else 0), 1),
    }


async def run() -> None:
    global MACHINES
    if SITE_BOOTSTRAP:
        # ensure seed
        for attempt in range(30):
            try:
                async with httpx.AsyncClient(timeout=30.0) as http:
                    # trigger seed via internal script endpoint isn't available — rely on compose seed
                    pass
            except Exception:
                pass
            try:
                MACHINES = await discover_machines()
                if MACHINES:
                    break
            except Exception as exc:
                print(f"waiting for seed/API: {exc}")
                await asyncio.sleep(3)
        if not MACHINES:
            raise SystemExit("No machines discovered — run API seed first")
    else:
        raise SystemExit("SIM_USE_SEED=0 requires preconfigured MACHINES")

    t0 = time.time()
    async with httpx.AsyncClient(timeout=15.0) as http:
        while True:
            t = time.time() - t0
            points = [
                sample(m, t)
                for m in MACHINES
                if (m.get("device_id") or "") not in SKIP_DEVICES
            ]
            try:
                resp = await http.post(
                    f"{CLOUD_URL}/api/v1/ingest/telemetry",
                    headers={"X-API-Key": API_KEY},
                    json={"points": points},
                )
                resp.raise_for_status()
                print(f"posted {len(points)} pts accepted={resp.json().get('accepted')}")
            except Exception as exc:
                print(f"ingest error: {exc}")
            await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    asyncio.run(run())
