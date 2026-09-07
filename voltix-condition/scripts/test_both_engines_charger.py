"""
End-to-End Test for Voltix Pulse Engine (Layer 1) & Condition Engine (Layer 3)
Evaluates both models on laptop charger telemetry sequences.
"""

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Add package paths
sys.path.insert(0, os.path.join(project_root, "voltix-pulse"))
sys.path.insert(0, os.path.join(project_root, "voltix-condition", "src"))

from src.pulse.predict import predict_pulse_state, reset_machine_state
from condition.inference import predict_drift, reset_inference_cache

def test_both_engines_laptop_charger():
    print("=" * 80)
    print("       VOLTIX CHARGER DEMO: PULSE ENGINE (LAYER 1) + CONDITION ENGINE (LAYER 3)      ")
    print("=" * 80)

    reset_machine_state()
    reset_inference_cache()

    machine_id = "laptop_charger_01"

    # Simulated test sequence for laptop charger:
    # 1. Unplugged / Unpowered (OFF)
    # 2. Trickle / Float charge (IDLE)
    # 3. Active fast charge / high compute load (ACTIVE - Normal)
    # 4. Degradation / Drift scenario during ACTIVE state (ACTIVE - Drift)

    test_telemetry = [
        {"ts": "00:00:00", "i_rms_a": 0.000, "history": [0.000, 0.000], "desc": "Unplugged charger (OFF)"},
        {"ts": "00:00:02", "i_rms_a": 0.000, "history": [0.000, 0.000], "desc": "Unplugged charger (OFF)"},
        {"ts": "00:01:00", "i_rms_a": 0.160, "history": [0.160, 0.160], "desc": "Trickle / float charge (IDLE)"},
        {"ts": "00:01:02", "i_rms_a": 0.162, "history": [0.160, 0.160], "desc": "Trickle / float charge (IDLE)"},
        {"ts": "00:02:00", "i_rms_a": 0.250, "history": [0.250, 0.250], "desc": "Active fast charge (ACTIVE - Normal)"},
        {"ts": "00:02:02", "i_rms_a": 0.260, "history": [0.250, 0.255], "desc": "Active fast charge (ACTIVE - Normal)"},
        {"ts": "00:02:04", "i_rms_a": 0.258, "history": [0.255, 0.260], "desc": "Active fast charge (ACTIVE - Normal)"},
        {"ts": "00:03:00", "i_rms_a": 0.520, "history": [0.510, 0.515], "desc": "Capacitor degradation / current drift (ACTIVE - Elevated)"},
        {"ts": "00:03:02", "i_rms_a": 0.525, "history": [0.515, 0.520], "desc": "Capacitor degradation / current drift (ACTIVE - Elevated)"},
        {"ts": "00:03:04", "i_rms_a": 0.530, "history": [0.520, 0.525], "desc": "Capacitor degradation / current drift (ACTIVE - Elevated)"},
        {"ts": "00:03:06", "i_rms_a": 0.528, "history": [0.525, 0.530], "desc": "Capacitor degradation / current drift (ACTIVE - Elevated)"},
        {"ts": "00:03:08", "i_rms_a": 0.532, "history": [0.528, 0.530], "desc": "Capacitor degradation / current drift (ACTIVE - Elevated)"},
    ]

    print(f"\n{'Time':<10} | {'Current':<9} | {'Pulse State (L1)':<18} | {'Pulse Conf':<10} | {'Drift Flag (L3)':<16} | {'Drift Score':<12} | {'Description'}")
    print("-" * 120)

    for step in test_telemetry:
        i_rms = step["i_rms_a"]
        history = step["history"]

        # 1. Layer 1: Pulse Engine state prediction
        pulse_state, pulse_conf, model_ver = predict_pulse_state(
            machine_id=machine_id,
            i_rms_a=i_rms,
            history_i=history
        )

        # 2. Layer 3: Condition Drift prediction
        drift_res = predict_drift(
            machine_id=machine_id,
            i_rms_a=i_rms,
            history_i=history,
            state=pulse_state
        )

        flag_str = "TRUE (ALERT)" if drift_res["flag"] else "false (ok)"
        score_str = f"{drift_res['drift_score']:.4f}"

        print(f"{step['ts']:<10} | {i_rms:<9.3f} | {pulse_state:<18} | {pulse_conf:<10.2f} | {flag_str:<16} | {score_str:<12} | {step['desc']}")

    print("=" * 120)
    print("SUCCESS: Both Layer 1 (Pulse GMM) and Layer 3 (Condition Drift) executed properly on laptop charger!")

if __name__ == "__main__":
    test_both_engines_laptop_charger()
