# Voltix Condition / Drift Engine — `drift-v1`

**Owner:** Ramitha  
**Layer:** Layer 3 (Condition / Drift) in the Voltix Intelligence Stack  
**Model version:** `drift-v1`  
**Status:** Validated on Laptop Charger dataset (ESP32 NILM)  
**Package:** `voltix-condition`

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

## Module directory structure

```text
voltix-condition/
├── src/
│   └── condition/                    # Core Condition / Drift package
│       ├── __init__.py
│       ├── data_loader.py            # Data loading & steady-state filtering
│       ├── baseline.py               # Calibrated Baseline Z-Score model
│       ├── isolation_forest.py       # Comparative IsolationForest model
│       ├── persistence.py            # 3/5 sliding window persistence filter
│       ├── evaluate.py               # Benchmark evaluation engine
│       └── inference.py              # Live streaming predict_drift API
├── data/
│   ├── raw/                          # Raw S4P10.csv dataset
│   ├── processed/                    # Processed Voltix-schema CSVs
│   └── features/                     # Extracted train/val/test feature splits
├── models/
│   └── drift/                        # Model artifacts
│       ├── laptop_charger_01_baseline.json
│       └── laptop_charger_01_meta.json
├── reports/
│   ├── drift_evaluation_report.md
│   └── plots/                        # Generated evaluation figures
├── scripts/
│   ├── setup_essential_charger_data.py
│   └── run_drift_pipeline.py         # End-to-end training & evaluation
├── tests/
│   └── test_drift_engine.py          # Pytest suite
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Quick start

### 1. Install dependencies

```bash
pip install -r voltix-condition/requirements.txt
```

### 2. Run full pipeline (from root or voltix-condition)

```bash
cd voltix-condition
python scripts/run_drift_pipeline.py
```

### 3. Run tests

```bash
cd voltix-condition
pytest tests/test_drift_engine.py -v
```

---

## Integration with Voltix Ingestion API (`apps/api`)

The Layer 3 engine is wired to the backend ingest service via `apps/api/app/services/drift.py`.
When new telemetry arrives for an ACTIVE machine:
1. `predict_drift()` calculates the current anomaly score vs learned baseline.
2. If `flag == True` with sustained persistence, a `drift` alert is created in PostgreSQL with severity `warning` or `critical`.
3. Alert deduplication prevents alert spam (maximum 1 drift alert per 30 minutes).
