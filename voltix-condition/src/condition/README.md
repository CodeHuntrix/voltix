# Voltix Condition / Drift Engine — `drift-v1`

**Owner:** Ramitha  
**Layer:** 3 (Condition / Drift) in the Voltix Intelligence Stack  
**Model version:** `drift-v1`  
**Status:** Prototype validated on Laptop Charger dataset (ESP32 NILM)

---

## What this module does

Answers the question:
> *"While this machine is **ACTIVE**, does its electrical behaviour deviate significantly from its own learned normal baseline?"*

It does **not**:
- Replace Eesha's Pulse state classification (Layer 1)
- Predict exact failure dates or Remaining Useful Life
- Issue AutoCut or relay commands
- Claim full predictive maintenance

---

## Project structure

```
voltix/
├── condition/                     # Core Condition / Drift module
│   ├── __init__.py
│   ├── data_loader.py             # Load Voltix-schema CSVs + steady-state filter
│   ├── features.py                # Rolling feature extraction (mean, std, window)
│   ├── baseline.py                # Per-machine Baseline Z-Score / Mahalanobis model
│   ├── isolation_forest.py        # Comparative IsolationForest model (sklearn / numpy)
│   ├── synthetic.py               # Synthetic drift stream generator
│   ├── scoring.py                 # Score normalisation, persistence filter, severity
│   ├── inference.py               # predict_drift(...) API contract
│   └── evaluate.py                # Benchmark evaluation runner
├── apps/api/app/services/
│   └── drift.py                   # Backend hook into Voltix ingest pipeline
├── models/drift/
│   ├── laptop_charger_01_baseline.json
│   ├── laptop_charger_01_meta.json
│   └── laptop_charger_01_drift.joblib
├── data/
│   ├── raw/charger/               # Essential charger CSVs (S4P10_*.csv)
│   ├── processed/                 # Voltix-schema CSVs (laptop_charger_01.csv)
│   └── synthetic/                 # Synthetic drift test streams
├── reports/condition/
│   ├── dataset_inspection_report.md
│   ├── drift_evaluation_report.md
│   └── plots/                     # 10 visualization figures
├── tests/
│   └── test_drift_engine.py       # Pytest suite (5 tests)
└── scripts/
    └── run_drift_pipeline.py      # One-click master script
```

---

## Quick start

### 1. Install dependencies

```bash
pip install scikit-learn==1.4.2 joblib cloudpickle threadpoolctl narwhals pandas numpy matplotlib tabulate --no-deps
```

### 2. Run the full pipeline (train → evaluate → plot → inference demo)

```bash
cd c:\Users\admin\Voltix\voltix
python scripts/run_drift_pipeline.py
```

This will:
1. Load `data/processed/laptop_charger_01.csv`
2. Extract rolling features (window = 15 samples ≈ 30 s)
3. Train the Baseline Z-Score / Mahalanobis model → save to `models/drift/`
4. Train the comparative IsolationForest model → save joblib artifact
5. Generate 5 synthetic drift test streams → `data/synthetic/`
6. Run full benchmark evaluation → print table + save `reports/condition/`
7. Generate 10 publication-quality plots → `reports/condition/plots/`
8. Run a live streaming inference demo

### 3. Run tests

```bash
python -m pytest tests/test_drift_engine.py -v
```

Expected: **5 passed**.

---

## Model parameters (configurable)

All parameters are saved in `models/drift/laptop_charger_01_baseline.json`:

| Parameter | Default | Description |
|---|---|---|
| `window_size` | `15` samples | Rolling feature window (~30 s at 0.5 Hz) |
| `z_threshold` | auto-calibrated | Auto-set at 99th percentile of training scores |
| `target_false_alarm_rate` | `0.01` (1%) | Drives auto-calibration |
| `score_lambda` | `0.4` | Sigmoid normalisation: `S = 1 - exp(-λ·Z)` |
| `persistence_m` | `3` | Anomalous windows required out of N to flag |
| `persistence_n` | `5` | Sliding window length for persistence check |
| `severity_med_thresh` | `0.40` | Medium severity threshold |
| `severity_high_thresh` | `0.75` | High severity threshold |

---

## Python API contract

```python
from condition.inference import predict_drift

result = predict_drift(
    machine_id="laptop_charger_01",
    i_rms_a=0.21,                  # Current reading (A)
    history_i=[0.17, 0.16, ...],   # Rolling history buffer (last N readings)
    state="ACTIVE",                # Pulse state gate
    temp_c=32.5,                   # Optional temperature (not used in v1 model)
    ts="2026-09-06T10:00:00Z",     # ISO timestamp
)
```

### Non-ACTIVE state → automatic skip

```python
predict_drift(machine_id="...", i_rms_a=0.0, state="OFF")
# → {"flag": False, "drift_score": 0.0, "severity": "low",
#     "model_version": "drift-v1", "message": "skipped_non_active", ...}
```

### Response schema

```json
{
  "machine_id": "laptop_charger_01",
  "flag": true,
  "drift_score": 0.87,
  "severity": "high",
  "model_version": "drift-v1",
  "message": "ACTIVE i_rms above baseline band (z=8.4, score=0.87)",
  "ts": "2026-09-06T10:00:01Z"
}
```

---

## Benchmark results (Laptop Charger prototype)

| Stream | Baseline Flag Rate | IsoForest Flag Rate |
|---|---|---|
| normal_active (healthy) | ~1.4% | ~1.0% |
| drift_10pct (+10% shift) | ~3.1% | ~1.8% |
| drift_20pct (+20% shift) | ~5.1% | ~3.7% |
| drift_ramp (slow upward) | ~5.1% | ~1.3% |
| drift_variance (2× noise) | ~100% | ~100% |

---

## Evaluation plots

Located in `reports/condition/plots/`:

| # | Plot |
|---|---|
| 1 | Raw current signature |
| 2 | Normal ACTIVE current distribution |
| 3 | Healthy vs +10% synthetic drift |
| 4 | Healthy vs +20% synthetic drift |
| 5 | Slow upward ramp drift profile |
| 6 | High-noise variance drift profile |
| 7 | Normalised drift score over time (0→1) |
| 8 | Current with alert flags highlighted |
| 9 | Distribution of normal anomaly scores |
| 10 | Distribution of drift anomaly scores |

---

## Voltix integration (how this fits into the pipeline)

```
CT telemetry → Pulse (Eesha, Layer 1) → committed state
                                         ↓
                          if state == "ACTIVE":
                              predict_drift(...)
                                         ↓
                          if flag == True:
                              create alert_type="drift"
                                         ↓
                              Web / Mobile alert panel
```

The backend hook is in [`apps/api/app/services/drift.py`](apps/api/app/services/drift.py) — call `maybe_create_drift_alert(db, machine, state, i_rms_a)` from the ingest handler when state is committed as ACTIVE.

---

## Prototype limitations

1. **Laptop charger ≠ industrial machine** — used solely to validate the software pipeline.
2. **No Voltix ACTIVE/IDLE/WASTE labels in source data** — steady-state ACTIVE approximated by `i_rms_a ≥ 0.12 A`.
3. **Synthetic drift is not real equipment failure** — +10%/+20% level shifts, ramps, and variance boosts are artificially injected.
4. **CT-only, single-phase** — cannot diagnose bearing failures, mechanical wear, or thermal events without additional sensors.
5. **Next step**: Run the same pipeline on MetroPT-3 air compressor dataset for industrial validation.
