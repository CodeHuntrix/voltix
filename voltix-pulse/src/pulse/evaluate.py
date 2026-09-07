"""
Voltix Pulse Engine — Evaluation Module
Evaluates machine-specific GMM models on chronologically held-out test sets,
computes classification metrics, generates high-res visualization plots, and outputs markdown reports.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import argparse
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Headless backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from src.pulse.features import FEATURE_NAMES, FEATURES_DIR
from src.pulse.model_registry import resolve_machine_id, get_machine_config
from src.pulse.predict import reset_machine_state, predict_pulse_state

PLOTS_DIR = os.environ.get("VOLTIX_PLOTS_DIR", os.path.join(PROJECT_ROOT, "reports", "plots"))
REPORT_PATH = os.environ.get("VOLTIX_REPORT_PATH", os.path.join(PROJECT_ROOT, "reports", "evaluation_report.md"))


def evaluate_machine(machine_identifier: str) -> dict:
    """
    Evaluates a single machine's GMM model on its held-out test set.
    Generates 5 required plots and computes complete metrics.
    """
    m_id = resolve_machine_id(machine_identifier)
    config = get_machine_config(m_id)
    machine_type = config["machine_type"]
    
    print("\n" + "=" * 60)
    print(f"EVALUATING VOLTIX PULSE MODEL: {m_id} ({machine_type})")
    print("=" * 60)
    
    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    
    # Load model and metadata
    model_path = config["model_file"]
    meta_path = config["meta_file"]
    
    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        raise FileNotFoundError(f"Model or metadata for {m_id} not found. Run train.py first.")
        
    gmm = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    # Load test features
    test_path = os.path.join(FEATURES_DIR, f"{machine_type}_features_test.csv")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test feature file not found at {test_path}. Run train.py first.")
        
    test_df = pd.read_csv(test_path)
    X_test = test_df[FEATURE_NAMES].values
    y_true = test_df["state_label"].values
    
    # 1. GMM predictions and confidence on test set
    cluster_preds = gmm.predict(X_test)
    probabilities = gmm.predict_proba(X_test)
    confidences = np.max(probabilities, axis=1)
    
    cluster_map = meta["cluster_map"]
    gmm_pred_states = [cluster_map.get(str(c), "IDLE") for c in cluster_preds]
    
    # 2. Compute metrics against ground truth
    eval_labels = ["OFF", "IDLE", "ACTIVE"]
    acc = accuracy_score(y_true, gmm_pred_states)
    prec_macro = precision_score(y_true, gmm_pred_states, average="macro", zero_division=0)
    rec_macro = recall_score(y_true, gmm_pred_states, average="macro", zero_division=0)
    f1_macro = f1_score(y_true, gmm_pred_states, average="macro", zero_division=0)
    
    cm = confusion_matrix(y_true, gmm_pred_states, labels=eval_labels)
    clf_rep = classification_report(y_true, gmm_pred_states, labels=eval_labels, output_dict=True, zero_division=0)
    
    # 3. Simulate Pulse Engine with Duration-based WASTE rule
    reset_machine_state(m_id)
    pulse_final_states = []
    dt = meta.get("sampling_interval_seconds", 1.0)
    
    for i in range(len(test_df)):
        i_curr = float(X_test[i, 0])
        # History is past 2 samples
        hist = [float(X_test[i-2, 0]), float(X_test[i-1, 0])] if i >= 2 else ([float(X_test[0, 0])] if i == 1 else None)
        p_state, p_conf, _ = predict_pulse_state(m_id, i_curr, history_i=hist, time_delta_seconds=dt)
        pulse_final_states.append(p_state)
        
    waste_count = pulse_final_states.count("WASTE")
    idle_count = pulse_final_states.count("IDLE")
    active_count = pulse_final_states.count("ACTIVE")
    off_count = pulse_final_states.count("OFF")
    
    print(f"\n[TEST PERFORMANCE: {m_id}]")
    print(f"  Test samples:     {len(X_test)}")
    print(f"  Accuracy:         {acc:.4f} ({acc*100:.2f}%)")
    print(f"  Macro Precision:  {prec_macro:.4f}")
    print(f"  Macro Recall:     {rec_macro:.4f}")
    print(f"  Macro F1-Score:   {f1_macro:.4f}")
    print(f"  Mean Confidence:  {np.mean(confidences):.4f}")
    print(f"  States Evaluated: {eval_labels}")
    print(f"  GMM Predictions:  OFF={gmm_pred_states.count('OFF')}, IDLE={gmm_pred_states.count('IDLE')}, ACTIVE={gmm_pred_states.count('ACTIVE')}")
    print(f"  Pulse Final:      OFF={off_count}, IDLE={idle_count}, ACTIVE={active_count}, WASTE={waste_count}")
    
    # ==========================================
    # GENERATE 5 HIGH-RESOLUTION PLOTS
    # ==========================================
    
    # Plot 1: Current over time
    plt.figure(figsize=(12, 4))
    time_indices = np.arange(len(test_df))
    # If timestamps exist, plot up to 500 points or subsample for readability
    n_plot = min(1000, len(test_df))
    plt.plot(time_indices[:n_plot], test_df["i_rms_a"].iloc[:n_plot], color="#1f77b4", lw=1.2, label="i_rms_a (Test)")
    plt.title(f"{m_id} — Current Telemetry Timeline (First {n_plot} Test Samples)", fontsize=12, fontweight="bold")
    plt.xlabel(f"Observation Steps (Nominal interval: {dt}s)", fontsize=10)
    plt.ylabel("RMS Current (A)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plot1_path = os.path.join(PLOTS_DIR, f"current_timeline_{machine_type}.png")
    plt.savefig(plot1_path, dpi=200)
    plt.close()
    
    # Plot 2: Feature distribution / clusters
    plt.figure(figsize=(8, 6))
    scatter_colors = {"OFF": "#7f7f7f", "IDLE": "#ff7f0e", "ACTIVE": "#2ca02c", "WASTE": "#d62728"}
    for state_name in eval_labels:
        mask = np.array(gmm_pred_states) == state_name
        if np.any(mask):
            plt.scatter(
                X_test[mask, 0],
                X_test[mask, 2],
                c=scatter_colors.get(state_name, "#1f77b4"),
                label=f"Predicted {state_name}",
                alpha=0.6,
                edgecolors="none",
                s=20
            )
    plt.title(f"{m_id} — GMM Feature Space & Clusters (i_rms_a vs i_std_3samples)", fontsize=12, fontweight="bold")
    plt.xlabel("Instantaneous Current i_rms_a (A)", fontsize=10)
    plt.ylabel("Rolling Std Dev i_std_3samples (A)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plot2_path = os.path.join(PLOTS_DIR, f"cluster_scatter_{machine_type}.png")
    plt.savefig(plot2_path, dpi=200)
    plt.close()
    
    # Plot 3: State timeline (GMM instantaneous vs Pulse Engine final)
    plt.figure(figsize=(14, 5))
    n_t = min(800, len(test_df))
    steps = np.arange(n_t)
    state_to_num = {"OFF": 0, "IDLE": 1, "ACTIVE": 2, "WASTE": 3}
    num_gmm = [state_to_num.get(s, 1) for s in gmm_pred_states[:n_t]]
    num_pulse = [state_to_num.get(s, 1) for s in pulse_final_states[:n_t]]
    
    plt.step(steps, num_gmm, where="post", color="#1f77b4", lw=1.5, alpha=0.7, label="GMM Instantaneous State")
    plt.step(steps, num_pulse, where="post", color="#d62728", lw=1.8, linestyle="--", label="Pulse Final State (with Waste Rule)")
    plt.yticks([0, 1, 2, 3], ["OFF", "IDLE", "ACTIVE", "WASTE"])
    plt.ylim(-0.5, 3.5)
    plt.title(f"{m_id} — State Timeline: GMM vs Pulse Engine Policy", fontsize=12, fontweight="bold")
    plt.xlabel(f"Observation Steps ({dt}s per step)", fontsize=10)
    plt.ylabel("Operating State", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plot3_path = os.path.join(PLOTS_DIR, f"state_timeline_{machine_type}.png")
    plt.savefig(plot3_path, dpi=200)
    plt.close()
    
    # Plot 4: Confusion matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=eval_labels,
        yticklabels=eval_labels
    )
    plt.title(f"{m_id} — Confusion Matrix (Held-out Test Set)", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted State", fontsize=10)
    plt.ylabel("Ground Truth State", fontsize=10)
    plt.tight_layout()
    plot4_path = os.path.join(PLOTS_DIR, f"confusion_matrix_{machine_type}.png")
    plt.savefig(plot4_path, dpi=200)
    plt.close()
    
    # Plot 5: Cluster statistics
    plt.figure(figsize=(7, 4.5))
    stats = meta["cluster_stats"]
    c_ids = sorted(list(stats.keys()), key=lambda k: stats[k]["mean_current"])
    means = [stats[c]["mean_current"] for c in c_ids]
    stds = [stats[c]["std_current"] for c in c_ids]
    labels_mapped = [f"Cluster {c}\n({stats[c]['mapped_state']})" for c in c_ids]
    colors = [scatter_colors.get(stats[c]["mapped_state"], "#1f77b4") for c in c_ids]
    
    bars = plt.bar(labels_mapped, means, yerr=stds, capsize=5, color=colors, alpha=0.85, edgecolor="black")
    for bar, m in zip(bars, means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f"{m:.2f}A", ha="center", va="bottom", fontweight="bold")
    plt.title(f"{m_id} — Cluster Mean Current & Mapped States", fontsize=12, fontweight="bold")
    plt.ylabel("Mean RMS Current (A)", fontsize=10)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plot5_path = os.path.join(PLOTS_DIR, f"cluster_stats_{machine_type}.png")
    plt.savefig(plot5_path, dpi=200)
    plt.close()
    
    eval_result = {
        "machine_id": m_id,
        "machine_type": machine_type,
        "test_samples": len(X_test),
        "accuracy": round(acc, 4),
        "macro_precision": round(prec_macro, 4),
        "macro_recall": round(rec_macro, 4),
        "macro_f1": round(f1_macro, 4),
        "mean_confidence": round(float(np.mean(confidences)), 4),
        "min_confidence": round(float(np.min(confidences)), 4),
        "median_confidence": round(float(np.median(confidences)), 4),
        "unique_labels": eval_labels,
        "classification_report": clf_rep,
        "confusion_matrix": cm.tolist(),
        "pulse_final_distribution": {
            "OFF": off_count,
            "IDLE": idle_count,
            "ACTIVE": active_count,
            "WASTE": waste_count
        },
        "plots": [plot1_path, plot2_path, plot3_path, plot4_path, plot5_path]
    }
    
    return eval_result


def generate_markdown_report(results: list[dict]) -> None:
    """Writes a comprehensive evaluation report to reports/evaluation_report.md."""
    lines = [
        "# Voltix Pulse Engine — GMM Evaluation Report",
        "",
        "## Executive Summary",
        "",
        "The **Voltix Pulse Engine** implements machine-specific Gaussian Mixture Models (`sklearn.mixture.GaussianMixture`) "
        "to classify the instantaneous electrical operating states of MSME equipment without modifying upstream MQTT telemetry "
        "or downstream TimescaleDB/API contracts.",
        "",
        "> [!IMPORTANT]",
        "> **Core Architectural Principle**: The GMM classifies the machine's **instantaneous electrical operating condition** (`OFF`, `IDLE`, `ACTIVE`). "
        "> `WASTE` is treated as a temporal policy state managed by the Pulse Engine rather than an artificial instantaneous cluster, "
        "> because prolonged unloaded idle draws identical electrical current to normal idle.",
        "",
        "---",
        ""
    ]
    
    for r in results:
        m_id = r["machine_id"]
        m_type = r["machine_type"]
        lines.extend([
            f"## Machine Evaluation: {m_id} ({m_type})",
            "",
            "### Performance Summary",
            "",
            f"- **Chronological Test Samples**: {r['test_samples']:,}",
            f"- **Overall Test Accuracy**: `{r['accuracy'] * 100:.2f}%`",
            f"- **Macro Precision**: `{r['macro_precision']:.4f}`",
            f"- **Macro Recall**: `{r['macro_recall']:.4f}`",
            f"- **Macro F1-Score**: `{r['macro_f1']:.4f}`",
            f"- **GMM Posterior Confidence**: Mean = `{r['mean_confidence']:.4f}`, Median = `{r['median_confidence']:.4f}`, Min = `{r['min_confidence']:.4f}`",
            "",
            "### State Coverage & Pulse Final Distribution",
            "",
            "| State | GMM Supported | Test Ground Truth | Pulse Engine Final (with Waste Policy) |",
            "| :--- | :--- | :--- | :--- |",
            f"| `OFF` | Yes | `{r['classification_report'].get('OFF', {}).get('support', 0)}` | `{r['pulse_final_distribution']['OFF']}` |",
            f"| `IDLE` | Yes | `{r['classification_report'].get('IDLE', {}).get('support', 0)}` | `{r['pulse_final_distribution']['IDLE']}` |",
            f"| `ACTIVE` | Yes | `{r['classification_report'].get('ACTIVE', {}).get('support', 0)}` | `{r['pulse_final_distribution']['ACTIVE']}` |",
            f"| `WASTE` | Temporal Policy | `0 (Not in instantaneous dataset)` | `{r['pulse_final_distribution']['WASTE']}` |",
            "",
            "### Per-Class Performance Breakdown",
            "",
            "| Class | Precision | Recall | F1-Score | Support |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ])
        
        for state in r["unique_labels"]:
            metrics = r["classification_report"].get(state, {})
            p = metrics.get("precision", 0)
            rec = metrics.get("recall", 0)
            f1 = metrics.get("f1-score", 0)
            sup = metrics.get("support", 0)
            lines.append(f"| `{state}` | {p:.4f} | {rec:.4f} | {f1:.4f} | {sup} |")
            
        lines.extend([
            "",
            "### Generated Visualizations",
            "",
            f"1. `current_timeline_{m_type}.png` — Raw current timeline across test sequence.",
            f"2. `cluster_scatter_{m_type}.png` — Feature space separation (`i_rms_a` vs `i_std_3samples`).",
            f"3. `state_timeline_{m_type}.png` — Instantaneous GMM vs duration-aware Pulse final state.",
            f"4. `confusion_matrix_{m_type}.png` — Confusion matrix on held-out test data.",
            f"5. `cluster_stats_{m_type}.png` — Cluster current statistics and semantic state mapping.",
            "",
            "---",
            ""
        ])
        
    lines.extend([
        "## Honest Limitations & Dataset Constraints",
        "",
        "1. **Laptop Charger (`S4P10.csv`)**: Records 8 continuous hours of a laptop on AC power (initial charging followed by sustained trickle charge). "
        "The dataset provides zero ground-truth basis to differentiate normal low-load standby from prolonged energy waste. "
        "Consequently, no synthetic `WASTE` labels were fabricated.",
        "2. **Air Compressor (`MetroPT-3`)**: Industrial screw compressor telemetry unambiguously reveals `OFF` (~0.04A), `UNLOADED/IDLE` (~3.8A), and `LOADED/ACTIVE` (~6.0A). "
        "Because an unloaded compressor draws ~3.8A whether idling normally or wasting energy, instantaneous GMM clustering isolates `IDLE`. "
        "The Pulse Engine applies a configurable temporal rule (`WASTE_DURATION_SECONDS = 300`) to classify prolonged idle operation as `WASTE`.",
        "3. **Causal Time-Series Integrity**: Features were computed causally over 3 samples with strict chronological train/val/test splits, guaranteeing zero lookahead bias.",
        ""
    ])
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n[REPORT] Saved evaluation report to: {REPORT_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Voltix Pulse GMM Models")
    parser.add_argument("--machine", choices=["laptop_charger", "compressor"], help="Evaluate specific machine")
    parser.add_argument("--all", action="store_true", help="Evaluate all machine models")
    
    args = parser.parse_args()
    
    results = []
    if args.all or (not args.machine):
        print("Evaluating all machine models...")
        results.append(evaluate_machine("laptop_charger"))
        results.append(evaluate_machine("compressor"))
    elif args.machine:
        results.append(evaluate_machine(args.machine))
        
    generate_markdown_report(results)


if __name__ == "__main__":
    main()
