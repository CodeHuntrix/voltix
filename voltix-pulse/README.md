# Voltix Pulse Engine — Machine-Specific GMM Models

Intelligent electrical operating state and energy waste classification for MSME machinery.

The **Pulse Engine** receives electrical current telemetry from industrial and commercial machines and maps it into standard Voltix operational states:
* **`OFF`**: Machine is unpowered or drawing negligible/leakage current.
* **`IDLE`**: Machine is powered and running, but not performing productive work (e.g., unloaded compressor motor, laptop on float/standby).
* **`ACTIVE`**: Machine is actively performing useful work (e.g., compressing air under pressure, active battery charging/compute).
* **`WASTE`**: Machine is drawing electrical power unnecessarily / prolonged no-load operation beyond configured debounce thresholds.

---

## 1. Core Architecture & Design Principles

```text
                    ELECTRICAL TELEMETRY
                   (i_rms_a, 3-sample history)
                            ↓
                    VOLTIX PULSE ENGINE
                            |
                  Machine ID / Type Router
                            |
              +-------------+-------------+
              |                           |
      laptop_charger_01             compressor_01
              |                           |
     Laptop Charger GMM            Compressor GMM
   (Covariance: Full, n=3)     (Covariance: Full, n=3)
              |                           |
       OFF / IDLE / ACTIVE         OFF / IDLE / ACTIVE
              |                           |
    (No continuous ground                 v
     truth for waste)             Duration / Policy Rule
              |                   (Threshold: 300s / 5 min)
              |                           |
              |               prolonged unnecessary IDLE
              |                           |
              v                           v
     Final State:                Final State:
     OFF / IDLE / ACTIVE         OFF / IDLE / ACTIVE / WASTE
```

### Key Architectural Tenet: Decoupled GMM vs. Waste Policy
* **GMM Responsibility**: Identifies the machine's **instantaneous electrical operating condition** (`OFF`, `IDLE`, `ACTIVE`) from current magnitude and short-term rolling dynamics.
* **Pulse Engine Responsibility**: Identifies **`WASTE`** as a temporal policy state. An unloaded air compressor motor draws ~3.8 A whether idling for 20 seconds during a normal pressure cycle or idling for 10 minutes unnecessarily. Instantaneous current alone cannot differentiate these; duration of sustained `IDLE` determines `WASTE`.
* **Zero Fabrication**: No synthetic `WASTE` labels are fabricated for datasets that do not support them.

---

## 2. Dataset Sources & Preprocessing

### Dataset A — Laptop Charger
* **Source**: ESP32 NILM Dataset (`S4P10.csv`, Plug 10: Laptop).
* **Telemetry**: 14,878 rows, 0 missing values, time span: 129s to 28,923s (8.00 continuous hours).
* **Sampling Rate**: ~0.50 Hz (2.0s median interval), matching the Voltix Pulse 0.5–2 Hz specification.
* **Physical Profile**:
  * $t=129\text{s}$: 3 unplugged/zero-current samples ($< 0.01\text{ A}$) $\rightarrow$ `OFF`.
  * Hour 0: Rapid battery charging ($0.25 - 0.41\text{ A}$, $50 - 86\text{ W}$) $\rightarrow$ `ACTIVE`.
  * Hours 1–8: Float / trickle charge maintaining full battery on AC ($0.14 - 0.18\text{ A}$, $\sim 32\text{ W}$) $\rightarrow$ `IDLE` / low-load.
* **Limitation**: The dataset records a single 8-hour continuous session without independent operational ground truth for prolonged waste. Evaluated honestly as `OFF`, `IDLE`, and `ACTIVE`.

### Dataset B — Industrial Air Compressor
* **Source**: MetroPT-3 Predictive Maintenance Dataset (`MetroPT3(AirCompressor).csv`).
* **Telemetry**: 1,516,948 rows, 0 missing values in `Motor_current`, 7 months of continuous operation.
* **Sampling Rate**: 10.0 seconds (0.10 Hz).
* **Physical Profile**:
  * Motor unpowered: `Motor_current < 0.20 A`, `TP2 ≈ -0.01 bar`, `COMP` inactive $\rightarrow$ `OFF`.
  * Motor unloaded/offloaded: `3.0 A <= Motor_current < 4.8 A` (mean: 3.8A), `TP2 ≈ -0.01 bar` (0 bar generated), intake valve closed $\rightarrow$ `IDLE`.
  * Motor loaded compression: `Motor_current >= 4.8 A` (mean: 6.0A), `TP2 > 8.0 bar`, reservoir pressure actively rising $\rightarrow$ `ACTIVE`.

---

## 3. Feature Engineering

Features are computed **strictly causally** over past observations only, preventing lookahead bias:
1. `i_rms_a`: Instantaneous RMS current (A).
2. `i_mean_3samples`: 3-sample causal rolling mean.
3. `i_std_3samples`: 3-sample causal rolling standard deviation.

**Effective Time Window**:
* Laptop Charger: 3 samples $\times 2.0\text{s} \approx 6.0\text{ seconds}$.
* Air Compressor: 3 samples $\times 10.0\text{s} = 30.0\text{ seconds}$.

---

## 4. Model Training & Component Selection

Models are trained using `sklearn.mixture.GaussianMixture` strictly on the chronological training split (70%):
```bash
python src/pulse/train.py --all
```

Candidate components $n \in [3, 4, 5, 6]$ are evaluated on BIC, AIC, and physical interpretability. For both machines, **3 components** were chosen to align with real physical states (`OFF`, `IDLE`, `ACTIVE`) rather than forcing artificial mathematical splits.

---

## 5. Model Evaluation & Visualizations

To evaluate both models on their held-out test splits (15%):
```bash
python src/pulse/evaluate.py --all
```

### Generated Plots (`reports/plots/`):
* `current_timeline_<machine>.png`: Test telemetry timeline.
* `cluster_scatter_<machine>.png`: Feature space separation.
* `state_timeline_<machine>.png`: Instantaneous GMM vs. duration-aware Pulse final state.
* `confusion_matrix_<machine>.png`: Confusion matrix on held-out test split.
* `cluster_stats_<machine>.png`: Cluster current statistics and mapped states.

---

## 6. How to Run Online Inference

```python
from src.pulse.predict import predict_pulse_state

# Example: Streaming telemetry for Air Compressor
state, confidence, version = predict_pulse_state(
    machine_id="compressor_01",
    i_rms_a=3.85,
    history_i=[3.82, 3.84]
)
print(f"State: {state}, Confidence: {confidence:.4f}, Version: {version}")
# Output: State: IDLE, Confidence: 0.9982, Version: gmm-v1

# When unloaded operation persists for >= 300 seconds:
# State automatically transitions to WASTE via the Pulse Engine policy.
```

---

## 7. Model Artifacts

* `models/pulse/laptop_charger_gmm.joblib` & `models/pulse/laptop_charger_meta.json`
* `models/pulse/compressor_gmm.joblib` & `models/pulse/compressor_meta.json`
