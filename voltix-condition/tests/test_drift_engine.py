"""Automated test suite for Voltix Condition / Drift Engine (`drift-v1`)."""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure condition package in src is in python path
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(pkg_root, "src"))
sys.path.insert(0, pkg_root)

from condition.data_loader import load_voltix_dataset, filter_active_data
from condition.features import extract_features_df, extract_features_single
from condition.baseline import BaselineDriftModel
from condition.isolation_forest import IsolationForestDriftModel
from condition.scoring import DriftScorer
from condition.inference import predict_drift, reset_inference_cache
from condition.synthetic import generate_synthetic_streams


@pytest.fixture(scope="module")
def processed_data_path():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "laptop_charger_01.csv"))
    if not os.path.exists(path):
        pytest.skip(f"Processed dataset not found at {path}")
    return path


@pytest.fixture(scope="module")
def models_dir():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "drift"))
    os.makedirs(path, exist_ok=True)
    return path


@pytest.fixture(scope="module")
def trained_baseline_model(processed_data_path, models_dir):
    df = load_voltix_dataset(processed_data_path)
    df_active = filter_active_data(df)
    df_feat = extract_features_df(df_active, window_size=15)
    
    model = BaselineDriftModel(machine_id="laptop_charger_01")
    model.fit(df_feat)
    model.save(models_dir)
    return model


def test_non_active_skipping():
    reset_inference_cache()
    states_to_skip = ["OFF", "IDLE", "WASTE"]
    for state in states_to_skip:
        res = predict_drift(machine_id="laptop_charger_01", i_rms_a=0.55, state=state)
        assert res["flag"] is False
        assert res["drift_score"] == 0.0
        assert res["severity"] == "low"
        assert res["message"] == "skipped_non_active"


def test_api_contract_schema(trained_baseline_model, models_dir):
    reset_inference_cache()
    res = predict_drift(machine_id="laptop_charger_01", i_rms_a=0.17, state="ACTIVE", models_dir=models_dir)
    
    expected_keys = {"machine_id", "flag", "drift_score", "severity", "model_version", "message", "ts"}
    assert set(res.keys()) == expected_keys
    assert isinstance(res["flag"], bool)
    assert isinstance(res["drift_score"], float)
    assert 0.0 <= res["drift_score"] <= 1.0
    assert res["severity"] in ["low", "medium", "high"]
    assert res["model_version"] == "drift-v1"


def test_normal_active_low_false_positive(trained_baseline_model, processed_data_path, models_dir):
    reset_inference_cache()
    df = load_voltix_dataset(processed_data_path)
    # Skip warmup: drop first 30 rows after steady-state filter so rolling window is warm
    df_active = filter_active_data(df)
    # Test on a contiguous slice from the middle of the session (fully warm)
    df_test = df_active.iloc[100:400].reset_index(drop=True)

    flags = []
    history = list(df_active["i_rms_a"].values[:100])  # pre-populate history
    for idx, row in df_test.iterrows():
        val = float(row["i_rms_a"])
        res = predict_drift(
            machine_id="laptop_charger_01",
            i_rms_a=val,
            history_i=history,
            state="ACTIVE",
            models_dir=models_dir,
        )
        flags.append(res["flag"])
        history.append(val)

    false_alarm_rate = float(np.mean(flags))
    assert false_alarm_rate < 0.02, f"False alarm rate too high on steady-state data: {false_alarm_rate * 100:.2f}%"



def test_synthetic_drift_detection(trained_baseline_model, processed_data_path, models_dir):
    reset_inference_cache()
    # Test +20% drift stream
    df = load_voltix_dataset(processed_data_path)
    df_active = filter_active_data(df).head(100)
    
    flags = []
    history = []
    for idx, row in df_active.iterrows():
        drifted_val = float(row["i_rms_a"]) * 1.25  # +25% drift
        res = predict_drift(machine_id="laptop_charger_01", i_rms_a=drifted_val, history_i=history, state="ACTIVE", models_dir=models_dir)
        flags.append(res["flag"])
        history.append(drifted_val)
        
    detection_rate = np.mean(flags[10:])  # check after persistence window warm-up
    assert detection_rate > 0.80, f"Drift detection rate too low: {detection_rate * 100:.2f}%"


def test_persistence_logic():
    scorer = DriftScorer(z_threshold=3.0, persistence_m=3, persistence_n=5)
    
    # 1. Single spike -> should NOT set flag = True
    flag1, score1, _, _ = scorer.evaluate_sample(raw_z_score=4.0, feature_val=0.5, baseline_mean=0.17, baseline_std=0.03)
    assert flag1 is False
    
    # 2. Second spike -> still flag = False (needs M=3)
    flag2, _, _, _ = scorer.evaluate_sample(raw_z_score=4.0, feature_val=0.5, baseline_mean=0.17, baseline_std=0.03)
    assert flag2 is False
    
    # 3. Third spike -> NOW flag = True
    flag3, score3, sev3, _ = scorer.evaluate_sample(raw_z_score=4.0, feature_val=0.5, baseline_mean=0.17, baseline_std=0.03)
    assert flag3 is True
    assert score3 > 0.70
    assert sev3 in ["medium", "high"]
