# Voltix Pulse Engine — GMM Evaluation Report

## Executive Summary

The **Voltix Pulse Engine** implements machine-specific Gaussian Mixture Models (`sklearn.mixture.GaussianMixture`) to classify the instantaneous electrical operating states of MSME equipment without modifying upstream MQTT telemetry or downstream TimescaleDB/API contracts.

> [!IMPORTANT]
> **Core Architectural Principle**: The GMM classifies the machine's **instantaneous electrical operating condition** (`OFF`, `IDLE`, `ACTIVE`). > `WASTE` is treated as a temporal policy state managed by the Pulse Engine rather than an artificial instantaneous cluster, > because prolonged unloaded idle draws identical electrical current to normal idle.

---

## Machine Evaluation: laptop_charger_01 (laptop_charger)

### Performance Summary

- **Chronological Test Samples**: 2,232
- **Overall Test Accuracy**: `87.77%`
- **Macro Precision**: `0.5000`
- **Macro Recall**: `0.4388`
- **Macro F1-Score**: `0.4674`
- **GMM Posterior Confidence**: Mean = `0.9269`, Median = `0.9816`, Min = `0.5953`

### State Coverage & Pulse Final Distribution

| State | GMM Supported | Test Ground Truth | Pulse Engine Final (with Waste Policy) |
| :--- | :--- | :--- | :--- |
| `OFF` | Yes | `0.0` | `0` |
| `IDLE` | Yes | `2232.0` | `1959` |
| `ACTIVE` | Yes | `0.0` | `273` |
| `WASTE` | Temporal Policy | `0 (Not in instantaneous dataset)` | `0` |

### Per-Class Performance Breakdown

| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| `OFF` | 0.0000 | 0.0000 | 0.0000 | 0.0 |
| `IDLE` | 1.0000 | 0.8777 | 0.9349 | 2232.0 |
| `ACTIVE` | 0.0000 | 0.0000 | 0.0000 | 0.0 |

### Generated Visualizations

1. `current_timeline_laptop_charger.png` — Raw current timeline across test sequence.
2. `cluster_scatter_laptop_charger.png` — Feature space separation (`i_rms_a` vs `i_std_3samples`).
3. `state_timeline_laptop_charger.png` — Instantaneous GMM vs duration-aware Pulse final state.
4. `confusion_matrix_laptop_charger.png` — Confusion matrix on held-out test data.
5. `cluster_stats_laptop_charger.png` — Cluster current statistics and semantic state mapping.

---

## Machine Evaluation: compressor_01 (compressor)

### Performance Summary

- **Chronological Test Samples**: 30,000
- **Overall Test Accuracy**: `97.74%`
- **Macro Precision**: `0.9066`
- **Macro Recall**: `0.9771`
- **Macro F1-Score**: `0.9340`
- **GMM Posterior Confidence**: Mean = `0.9999`, Median = `1.0000`, Min = `0.5409`

### State Coverage & Pulse Final Distribution

| State | GMM Supported | Test Ground Truth | Pulse Engine Final (with Waste Policy) |
| :--- | :--- | :--- | :--- |
| `OFF` | Yes | `21669.0` | `21344` |
| `IDLE` | Yes | `6590.0` | `4640` |
| `ACTIVE` | Yes | `1741.0` | `2419` |
| `WASTE` | Temporal Policy | `0 (Not in instantaneous dataset)` | `1597` |

### Per-Class Performance Breakdown

| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| `OFF` | 1.0000 | 0.9850 | 0.9924 | 21669.0 |
| `IDLE` | 1.0000 | 0.9464 | 0.9725 | 6590.0 |
| `ACTIVE` | 0.7197 | 1.0000 | 0.8370 | 1741.0 |

### Generated Visualizations

1. `current_timeline_compressor.png` — Raw current timeline across test sequence.
2. `cluster_scatter_compressor.png` — Feature space separation (`i_rms_a` vs `i_std_3samples`).
3. `state_timeline_compressor.png` — Instantaneous GMM vs duration-aware Pulse final state.
4. `confusion_matrix_compressor.png` — Confusion matrix on held-out test data.
5. `cluster_stats_compressor.png` — Cluster current statistics and semantic state mapping.

---

## Honest Limitations & Dataset Constraints

1. **Laptop Charger (`S4P10.csv`)**: Records 8 continuous hours of a laptop on AC power (initial charging followed by sustained trickle charge). The dataset provides zero ground-truth basis to differentiate normal low-load standby from prolonged energy waste. Consequently, no synthetic `WASTE` labels were fabricated.
2. **Air Compressor (`MetroPT-3`)**: Industrial screw compressor telemetry unambiguously reveals `OFF` (~0.04A), `UNLOADED/IDLE` (~3.8A), and `LOADED/ACTIVE` (~6.0A). Because an unloaded compressor draws ~3.8A whether idling normally or wasting energy, instantaneous GMM clustering isolates `IDLE`. The Pulse Engine applies a configurable temporal rule (`WASTE_DURATION_SECONDS = 300`) to classify prolonged idle operation as `WASTE`.
3. **Causal Time-Series Integrity**: Features were computed causally over 3 samples with strict chronological train/val/test splits, guaranteeing zero lookahead bias.
