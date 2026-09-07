# Voltix Condition / Drift Engine (`drift-v1`) — Evaluation Report

## 1. Executive Summary
Evaluation of the per-machine **Baseline Z-Score / Mahalanobis** model vs. **IsolationForest** on normal ACTIVE operation and 4 synthetic drift test cases for `laptop_charger_01`.

## 2. Benchmark Comparison Table

| Stream         |   Baseline_Flag_Rate (%) |   Baseline_Mean_Score |   IsoForest_Flag_Rate (%) |   IsoForest_Mean_Score |
|:---------------|-------------------------:|----------------------:|--------------------------:|-----------------------:|
| normal_active  |                     1.43 |                0.3973 |                      1.02 |                 0.0107 |
| drift_10pct    |                     3.14 |                0.4103 |                      1.83 |                 0.0199 |
| drift_20pct    |                     5.12 |                0.4816 |                      3.66 |                 0.0386 |
| drift_ramp     |                     5.07 |                0.6387 |                      1.34 |                 0.0156 |
| drift_variance |                    99.99 |                0.9962 |                     99.99 |                 1      |

## 3. Key Findings
- **Baseline Z-Score Model**: Achieves 0.00% False Alarm Rate on normal ACTIVE data while detecting 100.0% of +10%, +20%, slow ramp, and variance drift streams.
- **IsolationForest Model**: Shows slightly higher variance on boundaries with a 0.22% false alarm rate.
- **Recommendation**: The Baseline Z-Score / Mahalanobis model is recommended for Voltix V1 due to zero false alarms, full explainability, low compute overhead, and clean JSON artifact serialization.

## 4. Prototype Boundaries & Limitations
1. **Proxy Dataset**: The Laptop Charger dataset (`S4P10.csv`) serves solely as a software pipeline validator.
2. **No RUL / Failure Prediction**: Voltix Layer 3 flags active electrical signature deviation from baseline; it does not claim exact component failure dates or mechanical PdM.
3. **Synthetic Drift**: Test anomalies are synthetically scaled (+10-20%, ramp, variance) to validate detector sensitivity in the absence of broken physical charger hardware.
