"""
Voltix Demo Synchronizer for 135W Laptop / Charger Demo Video
Runs a synchronized 60-second cycle matching the Arduino Uno OLED display:
  0s  - 10s: IDLE   (~0.05A, ~230V, ~11.5W)  [Charger in wall socket, cable disconnected from laptop]
  10s - 35s: ACTIVE (~0.58A, ~229V, ~132W)   [Charger plugged into laptop, active charging/running]
  35s - 45s: IDLE   (~0.05A, ~230V, ~11.5W)  [Charger unplugged from laptop, wall socket still ON]
  45s - 60s: OFF    (0.00A, 0.0V, 0.0W)      [Wall socket switched OFF]
"""

import asyncio
import os
import random
import sys
import time
from datetime import datetime, timezone
import httpx

CLOUD_URL = os.getenv("CLOUD_URL", "http://127.0.0.1:8000").rstrip("/")
API_KEY = os.getenv("EDGE_INGEST_API_KEY", "voltix-edge-dev-key")
DEVICE_ID = "esp32-laptop-01"

CYCLE_DURATION = 60  # total loop length in seconds

def get_telemetry_for_second(second: int):
    # Phase 1: 0s to 10s -> IDLE
    if second < 10:
        phase = "IDLE (Unplugged)"
        current = round(random.uniform(0.045, 0.055), 3)
        voltage = round(random.uniform(229.5, 231.2), 1)
        power_w = round(voltage * current * 0.95, 1)
        temp_c = round(random.uniform(30.8, 31.4), 1)
    # Phase 2: 10s to 35s -> ACTIVE
    elif second < 35:
        phase = "ACTIVE (Charging)"
        current = round(random.uniform(0.560, 0.610), 3)
        voltage = round(random.uniform(228.0, 230.5), 1)
        power_w = round(voltage * current * 0.96, 1)  # ~125W - 135W
        temp_c = round(random.uniform(33.2, 34.6), 1)
    # Phase 3: 35s to 45s -> IDLE
    elif second < 45:
        phase = "IDLE (Unplugged)"
        current = round(random.uniform(0.045, 0.055), 3)
        voltage = round(random.uniform(229.5, 231.2), 1)
        power_w = round(voltage * current * 0.95, 1)
        temp_c = round(random.uniform(32.0, 32.8), 1)
    # Phase 4: 45s to 60s -> OFF
    else:
        phase = "OFF (Socket Cut)"
        current = 0.000
        voltage = 0.0
        power_w = 0.0
        temp_c = round(random.uniform(30.0, 30.5), 1)

    kw_est = round(power_w / 1000.0, 4)
    return phase, current, voltage, power_w, kw_est, temp_c

async def main():
    print("=" * 65)
    print("   VOLTIX 135W LAPTOP DEMO SYNCHRONIZER (FOR VIDEO & PPT)")
    print("=" * 65)
    print("Timing Sequence:")
    print("  00s - 10s: IDLE   | Cable held disconnected from laptop")
    print("  10s - 35s: ACTIVE | Cable plugged into laptop (135W load)")
    print("  35s - 45s: IDLE   | Cable removed from laptop")
    print("  45s - 60s: OFF    | Wall socket switched OFF")
    print("=" * 65)
    print("\nPress ENTER when you are ready to start filming (press Arduino RESET simultaneously)!")
    input(">>> Press ENTER to START: ")

    start_time = time.time()
    async with httpx.AsyncClient(timeout=5.0) as http:
        while True:
            elapsed = int(time.time() - start_time)
            second = elapsed % CYCLE_DURATION
            phase, current, voltage, power_w, kw_est, temp_c = get_telemetry_for_second(second)

            point = {
                "device_id": DEVICE_ID,
                "ts": datetime.now(timezone.utc).isoformat(),
                "i_rms_a": current,
                "v_nominal": voltage if voltage > 0 else 230.0,
                "pf_assumed": 0.95 if current > 0.1 else 0.85,
                "kw_est": kw_est,
                "temp_c": temp_c,
            }

            try:
                resp = await http.post(
                    f"{CLOUD_URL}/api/v1/ingest/telemetry",
                    headers={"X-API-Key": API_KEY},
                    json={"points": [point]},
                )
                status = f"HTTP {resp.status_code}"
            except Exception as e:
                status = f"ERR: {e}"

            # Visual cue for recording
            cue = ""
            if second == 10:
                cue = "  <--- *** PLUG INTO LAPTOP NOW ***"
            elif second == 35:
                cue = "  <--- *** UNPLUG FROM LAPTOP NOW ***"
            elif second == 45:
                cue = "  <--- *** SWITCH OFF SOCKET NOW ***"

            sys.stdout.write(
                f"\r[{second:02d}s/{CYCLE_DURATION}s] {phase:<17} | {current:.3f}A | {voltage:5.1f}V | {power_w:5.1f}W | {status}{cue}\n"
            )
            sys.stdout.flush()

            await asyncio.sleep(1.0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo stopped.")
