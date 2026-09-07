# Voltix V1

Hybrid IoT energy ops for MSME machining floors: Raspberry Pi edge gateway + FastAPI/Timescale cloud, React web ops console, Expo floor/owner app. CT-only estimated kW — not billing-grade metering.

## Quick start (cloud stack)

```bash
cd "C:\Users\thahs\SIH PROJECT\voltix"
docker compose up --build
```

Services:

| Service    | URL / port        |
| ---------- | ----------------- |
| API        | http://localhost:8000 |
| Health     | http://localhost:8000/health |
| Timescale  | localhost:5432    |
| Redis      | localhost:6379    |
| Simulator  | posts telemetry every 2s |

Demo login (seeded on API start):

- Email: `owner@voltix.demo`
- Password: `voltix-demo`

Also: `tech@voltix.demo` / `voltix-demo` (technician).

## Web ops console

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` and `/ws` to the API.

## Mobile (Expo)

```bash
cd apps/mobile
npm install
npx expo start
```

Set `EXPO_PUBLIC_API_URL` to your machine LAN IP (e.g. `http://192.168.1.10:8000`) when using a physical device.

## Edge gateway (Pi)

```bash
cd apps/edge
pip install -r requirements.txt
export CLOUD_URL=http://<vps-or-lan>:8000
export EDGE_INGEST_API_KEY=voltix-edge-dev-key
export MQTT_HOST=127.0.0.1
python gateway.py
```

Or on Pi: `sudo bash install.sh` (systemd unit). Edge buffers to SQLite when cloud is down and flushes on reconnect; polls approved AutoCut commands and publishes to `voltix/commands/{device_id}`.

## Simulator (without Compose)

```bash
# API must be up + seeded
cd apps/simulator
pip install -r requirements.txt
set CLOUD_URL=http://localhost:8000
python simulate.py
```

## Architecture (V1)

- **Ingest:** edge/simulator → `POST /api/v1/ingest/telemetry` (API key) → Timescale `telemetry` + `machine_latest`
- **Pulse:** threshold + debounce → OFF / ACTIVE / IDLE / WASTE (`model_version=rules-v1`)
- **Ranker / alerts:** waste score; sustained WASTE (~10m) raises alerts
- **AutoCut:** suggest → approve → edge poll → MQTT relay topic → ack + audit
- **M&V:** baselines + intervention report + CSV export
- **Realtime:** `WS /ws/sites/{id}?token=…`

## Honest limits

- CT-only estimated kW (assumed V / PF)
- AutoCut for eligible ≤10A relay loads only
- No billing, no full PdM, dataset training deferred (simulator + seed fixtures)

## Repo layout

```
apps/api  apps/worker  apps/edge  apps/web  apps/mobile  apps/simulator
packages/shared
docker-compose.yml
```

## Dev notes

- Git branch: `main` is the demo trunk. Work on a `feature/*` branch and merge to `main`.
- Env template: `.env.example`
