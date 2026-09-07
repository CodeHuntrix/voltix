"""
Voltix Pulse Engine — Training Module
Trains machine-specific Gaussian Mixture Models (GMM) with component search,
causal training, physical cluster mapping, and sanity verification.
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
from sklearn.mixture import GaussianMixture

from src.pulse.preprocessing import (
    preprocess_laptop_charger,
    preprocess_air_compressor,
    get_chronological_splits
)
from src.pulse.features import (
    FEATURE_NAMES,
    generate_and_save_features,
    FEATURES_DIR
)
from src.pulse.model_registry import (
    MODEL_REGISTRY,
    get_machine_config,
    resolve_machine_id
)

MODELS_DIR = os.environ.get("VOLTIX_MODELS_DIR", os.path.join(PROJECT_ROOT, "models", "pulse"))


def evaluate_candidate_components(
    X_train: np.ndarray,
    candidates: list[int] = [3, 4, 5, 6]
) -> list[dict]:
    """
    Evaluates candidate GMM components using BIC, AIC, and cluster separation.
    """
    results = []
    print(f"\n[MODEL SELECTION] Evaluating candidate GMM components {candidates}...")
    print(f"{'n_components':>12} | {'BIC':>14} | {'AIC':>14} | {'Converged':>10}")
    print("-" * 56)
    
    for n in candidates:
        gmm = GaussianMixture(
            n_components=n,
            covariance_type="full",
            random_state=42,
            n_init=10,
            max_iter=200
        )
        gmm.fit(X_train)
        bic = float(gmm.bic(X_train))
        aic = float(gmm.aic(X_train))
        converged = bool(gmm.converged_)
        
        # Check cluster means separation
        means = np.sort(gmm.means_[:, 0])
        print(f"{n:>12} | {bic:>14.1f} | {aic:>14.1f} | {str(converged):>10}")
        results.append({
            "n_components": n,
            "bic": round(bic, 2),
            "aic": round(aic, 2),
            "converged": converged,
            "current_means_sorted": [round(float(m), 4) for m in means]
        })
        
    return results


def map_clusters_to_states(
    gmm: GaussianMixture,
    X_train: np.ndarray,
    y_train: pd.Series,
    machine_type: str
) -> tuple[dict[int, str], dict[int, dict]]:
    """
    Data-driven semantic mapping of unsupervised GMM clusters to physical operational states.
    Does NOT assume cluster 0 = state 0.
    Uses learned current distribution and ground truth / operational characteristics.
    """
    cluster_preds = gmm.predict(X_train)
    n_components = gmm.n_components
    
    cluster_summary = []
    for c in range(n_components):
        mask = cluster_preds == c
        count = int(mask.sum())
        if count > 0:
            c_currents = X_train[mask, 0]
            mean_curr = float(np.mean(c_currents))
            median_curr = float(np.median(c_currents))
            std_curr = float(np.std(c_currents))
            min_curr = float(np.min(c_currents))
            max_curr = float(np.max(c_currents))
            
            # State distribution within cluster
            sub_y = y_train.iloc[mask]
            state_dist = sub_y.value_counts(normalize=True).to_dict()
            majority_state = sub_y.mode().iloc[0] if len(sub_y) > 0 else "UNKNOWN"
        else:
            mean_curr = median_curr = std_curr = min_curr = max_curr = 0.0
            state_dist = {}
            majority_state = "UNKNOWN"
            
        cluster_summary.append({
            "cluster_id": c,
            "count": count,
            "pct": round(count / len(X_train) * 100, 2),
            "mean_current": round(mean_curr, 4),
            "median_current": round(median_curr, 4),
            "std_current": round(std_curr, 4),
            "min_current": round(min_curr, 4),
            "max_current": round(max_curr, 4),
            "majority_state": majority_state,
            "state_distribution": {k: round(v, 4) for k, v in state_dist.items()}
        })
        
    # Sort clusters strictly by mean current to determine physical levels
    sorted_by_current = sorted(cluster_summary, key=lambda x: x["mean_current"])
    
    cluster_map = {}
    if machine_type == "compressor":
        # Industrial compressor physical thresholds:
        # OFF: negligible current (< 0.10 A, motor stopped)
        # IDLE: unloaded current (~3.7 - 4.2 A, motor running without compression)
        # ACTIVE: loaded current (> 4.5 A, active compression pumping air)
        for item in sorted_by_current:
            c_id = item["cluster_id"]
            m_curr = item["mean_current"]
            if m_curr < 0.20:
                cluster_map[c_id] = "OFF"
            elif m_curr < 4.50:
                cluster_map[c_id] = "IDLE"
            else:
                cluster_map[c_id] = "ACTIVE"
    else:
        # Laptop charger physical thresholds (ESP32 NILM S4P10):
        # S4P10 records active charging transitioning to trickle charge over 8 hours.
        # OFF: negligible current (< 0.02 A)
        # IDLE / LOW_LOAD: trickle charge / standby (0.02 A <= current < 0.20 A, ~30-35W)
        # ACTIVE: active battery charging / compute (current >= 0.20 A, ~50-86W)
        for item in sorted_by_current:
            c_id = item["cluster_id"]
            m_curr = item["mean_current"]
            maj_s = item["majority_state"]
            if m_curr < 0.05:
                cluster_map[c_id] = "OFF"
            elif m_curr < 0.20:
                cluster_map[c_id] = "IDLE"
            else:
                cluster_map[c_id] = "ACTIVE"
                
    # Update cluster summary with mapped state
    stats_dict = {}
    for item in cluster_summary:
        c_id = item["cluster_id"]
        item["mapped_state"] = cluster_map[c_id]
        stats_dict[str(c_id)] = item
        
    return cluster_map, stats_dict


def verify_physical_sanity(cluster_map: dict[int, str], stats_dict: dict[int, dict]) -> bool:
    """
    Verifies that mean(OFF) <= mean(IDLE) <= mean(ACTIVE).
    Reports and fails gracefully if learned physics are inverted.
    """
    state_means = {"OFF": [], "IDLE": [], "ACTIVE": []}
    for c_id, state in cluster_map.items():
        mean_c = stats_dict[str(c_id)]["mean_current"]
        state_means[state].append(mean_c)
        
    avg_off = np.mean(state_means["OFF"]) if state_means["OFF"] else 0.0
    avg_idle = np.mean(state_means["IDLE"]) if state_means["IDLE"] else avg_off
    avg_active = np.mean(state_means["ACTIVE"]) if state_means["ACTIVE"] else avg_idle
    
    print("\n[PHYSICAL SANITY CHECK]")
    if state_means["OFF"]:
        print(f"  OFF Mean Current:    {avg_off:.4f} A")
    else:
        print("  OFF Mean Current:    [N/A in continuous operational clusters; physical cutoff < 0.02A]")
    print(f"  IDLE Mean Current:   {avg_idle:.4f} A")
    print(f"  ACTIVE Mean Current: {avg_active:.4f} A")
    
    if avg_off <= avg_idle <= avg_active:
        print("  -> PASSED: Physical ordering satisfied (OFF <= IDLE <= ACTIVE)")
        return True
    else:
        print("  -> WARNING: Physical ordering anomaly detected!")
        return False


def train_machine_model(
    machine_identifier: str,
    selected_components: int | None = None
) -> tuple[GaussianMixture, dict]:
    """
    End-to-end training pipeline for a single machine model:
    1. Preprocess raw data (if not cached)
    2. Split chronologically (70/15/15)
    3. Generate causal features (i_rms_a, i_mean_3samples, i_std_3samples)
    4. Search and select defensible n_components (testing 3, 4, 5, 6)
    5. Fit final GMM strictly on X_train
    6. Perform data-driven cluster-to-state mapping
    7. Perform physical sanity check
    8. Save .joblib model and .json metadata
    """
    m_id = resolve_machine_id(machine_identifier)
    config = get_machine_config(m_id)
    machine_type = config["machine_type"]
    
    print("\n" + "=" * 60)
    print(f"TRAINING VOLTIX PULSE GMM: {m_id} ({machine_type})")
    print("=" * 60)
    
    # 1. Preprocess raw data
    if machine_type == "laptop_charger":
        df_processed = preprocess_laptop_charger()
    elif machine_type == "compressor":
        # 200k rows provides over 23 days of real industrial compressor cycling
        df_processed = preprocess_air_compressor(max_rows=200000)
    else:
        raise ValueError(f"Unknown machine type: {machine_type}")
        
    # 2. Chronological split (70% train, 15% val, 15% test)
    train_df, val_df, test_df = get_chronological_splits(df_processed, 0.70, 0.15, 0.15)
    
    # 3. Generate causal features
    features_dict = generate_and_save_features(machine_type, train_df, val_df, test_df)
    train_feat = features_dict["train"]
    
    X_train = train_feat[FEATURE_NAMES].values
    y_train = train_feat["state_label"]
    
    # 4. Evaluate candidate components [3, 4, 5, 6]
    candidate_evals = evaluate_candidate_components(X_train, [3, 4, 5, 6])
    
    # Selection logic: prefer 3 components for physical interpretability (OFF, IDLE, ACTIVE)
    # as instructed by design corrections, unless explicitly specified
    if selected_components is not None:
        n_final = selected_components
    else:
        # Per design guidelines, 3 components represents the genuine physical states without fabricating clusters
        n_final = 3
        print(f"[SELECTION] Selecting n_components={n_final} for physical interpretability (OFF, IDLE, ACTIVE).")
        
    # 5. Fit final GMM on training split
    print(f"\n[TRAINING] Fitting final GMM with n_components={n_final}, covariance_type='full', n_init=10...")
    final_gmm = GaussianMixture(
        n_components=n_final,
        covariance_type="full",
        random_state=42,
        n_init=10,
        max_iter=200
    )
    final_gmm.fit(X_train)
    
    # 6. Data-driven cluster mapping
    cluster_map, stats_dict = map_clusters_to_states(final_gmm, X_train, y_train, machine_type)
    
    # 7. Physical sanity check
    sanity_passed = verify_physical_sanity(cluster_map, stats_dict)
    
    # 8. Construct metadata JSON
    meta = {
        "model_version": "gmm-v1",
        "machine_id": m_id,
        "machine_type": machine_type,
        "algorithm": "GaussianMixture",
        "n_components": n_final,
        "covariance_type": "full",
        "random_state": 42,
        "features": FEATURE_NAMES,
        "sampling_interval_seconds": config["sampling_interval_seconds"],
        "effective_feature_window_seconds": config["effective_feature_window_seconds"],
        "training_samples": len(X_train),
        "cluster_map": {str(k): v for k, v in cluster_map.items()},
        "cluster_stats": stats_dict,
        "states_supported": sorted(list(set(cluster_map.values()))),
        "candidate_evaluations": candidate_evals,
        "physical_sanity_passed": sanity_passed,
        "waste_detection": config["waste_detection"],
        "notes": (
            "Model learns instantaneous electrical state (OFF, IDLE, ACTIVE). "
            "WASTE is a temporal/policy rule applied by the Pulse Engine upon sustained IDLE duration."
        )
    }
    
    # Save artifacts
    model_path = config["model_file"]
    meta_path = config["meta_file"]
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    joblib.dump(final_gmm, model_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
        
    print(f"\n[ARTIFACTS SAVED]")
    print(f"  Model:    {model_path}")
    print(f"  Metadata: {meta_path}")
    
    return final_gmm, meta


def main():
    parser = argparse.ArgumentParser(description="Train Voltix Pulse GMM Models")
    parser.add_argument("--machine", choices=["laptop_charger", "compressor"], help="Train specific machine")
    parser.add_argument("--all", action="store_true", help="Train all machine models")
    parser.add_argument("--components", type=int, default=None, help="Override n_components")
    
    args = parser.parse_args()
    
    if args.all or (not args.machine):
        print("Training all machine-specific models sequentially...")
        train_machine_model("laptop_charger", selected_components=args.components)
        train_machine_model("compressor", selected_components=args.components)
    elif args.machine:
        train_machine_model(args.machine, selected_components=args.components)


if __name__ == "__main__":
    main()
