"""Synthetic drift stream generation for testing Voltix Condition Engine."""

import os
import pandas as pd
import numpy as np


def generate_synthetic_streams(input_csv: str, output_dir: str) -> dict[str, str]:
    """
    Generates synthetic drift test streams from healthy ACTIVE data.
    Clearly tags synthetic anomalies.
    Returns dictionary of stream name -> CSV filepath.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(input_csv)
    df_active = df[df["state_label"] == "ACTIVE"].copy().reset_index(drop=True)
    
    stream_files = {}
    
    # 1. Healthy Normal Active
    df_normal = df_active.copy()
    df_normal["drift_type"] = "none"
    normal_path = os.path.join(output_dir, "normal_active.csv")
    df_normal.to_csv(normal_path, index=False)
    stream_files["normal_active"] = normal_path
    
    # 2. Case A: +10% Level Shift
    df_10pct = df_active.copy()
    df_10pct["i_rms_a"] = (df_10pct["i_rms_a"] * 1.10).round(4)
    df_10pct["drift_type"] = "synthetic_shift_10pct"
    path_10pct = os.path.join(output_dir, "drift_10pct.csv")
    df_10pct.to_csv(path_10pct, index=False)
    stream_files["drift_10pct"] = path_10pct

    # 3. Case B: +20% Level Shift
    df_20pct = df_active.copy()
    df_20pct["i_rms_a"] = (df_20pct["i_rms_a"] * 1.20).round(4)
    df_20pct["drift_type"] = "synthetic_shift_20pct"
    path_20pct = os.path.join(output_dir, "drift_20pct.csv")
    df_20pct.to_csv(path_20pct, index=False)
    stream_files["drift_20pct"] = path_20pct

    # 4. Case C: Slow Upward Ramp (+0.00002 A per sample)
    df_ramp = df_active.copy()
    ramp = np.linspace(0.0, 0.15, len(df_ramp))
    df_ramp["i_rms_a"] = (df_ramp["i_rms_a"] + ramp).round(4)
    df_ramp["drift_type"] = "synthetic_slow_ramp"
    path_ramp = os.path.join(output_dir, "drift_ramp.csv")
    df_ramp.to_csv(path_ramp, index=False)
    stream_files["drift_ramp"] = path_ramp

    # 5. Case D: High Variance (Noise boost)
    df_var = df_active.copy()
    noise = np.random.normal(0, 0.05, size=len(df_var))
    df_var["i_rms_a"] = np.clip(df_var["i_rms_a"] + noise, 0.10, 1.0).round(4)
    df_var["drift_type"] = "synthetic_high_variance"
    path_var = os.path.join(output_dir, "drift_variance.csv")
    df_var.to_csv(path_var, index=False)
    stream_files["drift_variance"] = path_var

    return stream_files
