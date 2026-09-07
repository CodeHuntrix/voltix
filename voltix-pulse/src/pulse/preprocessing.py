"""
Voltix Pulse Engine — Preprocessing Module
Converts raw machine telemetry into the standard Voltix schema and performs causal chronological splitting.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Default paths
RAW_LAPTOP_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "S4P10.csv")
if not os.path.exists(RAW_LAPTOP_PATH):
    RAW_LAPTOP_PATH = os.path.join(PROJECT_ROOT, "S4P10.csv")

RAW_COMPRESSOR_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "MetroPT3(AirCompressor).csv")
if not os.path.exists(RAW_COMPRESSOR_PATH):
    RAW_COMPRESSOR_PATH = os.path.join(PROJECT_ROOT, "MetroPT3(AirCompressor).csv")

PROCESSED_DIR = os.environ.get("VOLTIX_PROCESSED_DIR", os.path.join(PROJECT_ROOT, "data", "processed"))


def preprocess_laptop_charger(
    input_path: str = RAW_LAPTOP_PATH,
    output_path: str = os.path.join(PROCESSED_DIR, "laptop_charger_processed.csv")
) -> pd.DataFrame:
    """
    Preprocess S4P10.csv (ESP32 NILM dataset, Plug 10: Laptop).
    Standardizes schema: ts, machine_id, i_rms_a, v_nominal, pf_assumed, kw_est, temp_c, state_label, notes.
    """
    print(f"[PREPROCESSING] Loading Laptop Charger data from: {input_path}")
    df_raw = pd.read_csv(input_path)
    
    # Sort chronologically
    df_raw = df_raw.sort_values(by="time").reset_index(drop=True)
    
    # Remove duplicates on time
    df_raw = df_raw.drop_duplicates(subset=["time"]).reset_index(drop=True)
    
    # Drop missing irms
    df_raw = df_raw.dropna(subset=["irms"]).reset_index(drop=True)
    df_raw["irms"] = pd.to_numeric(df_raw["irms"], errors="coerce")
    df_raw = df_raw.dropna(subset=["irms"]).reset_index(drop=True)
    
    # Construct timestamps starting from synthetic base date since 'time' is elapsed seconds
    base_ts = datetime(2024, 1, 1, 0, 0, 0)
    timestamps = [base_ts + timedelta(seconds=float(t)) for t in df_raw["time"]]
    
    # Ground-truth semantic state mapping based on physical power/current:
    # < 0.02 A: OFF (unplugged / zero current)
    # 0.02 to < 0.20 A: IDLE / LOW_LOAD (trickle charge / standby, ~30-35W)
    # >= 0.20 A: ACTIVE (active battery charging / active computing, 45-86W)
    # Note: WASTE is not distinguishable from this dataset and is not fabricated.
    conditions = [
        df_raw["irms"] < 0.02,
        (df_raw["irms"] >= 0.02) & (df_raw["irms"] < 0.20),
        df_raw["irms"] >= 0.20
    ]
    labels = ["OFF", "IDLE", "ACTIVE"]
    state_labels = np.select(conditions, labels, default="IDLE")
    
    df_processed = pd.DataFrame({
        "ts": [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps],
        "machine_id": "laptop_charger_01",
        "i_rms_a": np.round(df_raw["irms"].astype(float), 4),
        "v_nominal": np.round(df_raw["vrms"].astype(float), 2) if "vrms" in df_raw else 230.0,
        "pf_assumed": np.round(df_raw["power_factor"].astype(float), 3) if "power_factor" in df_raw else 0.85,
        "kw_est": np.round(df_raw["p_active"].astype(float) / 1000.0, 4) if "p_active" in df_raw else np.nan,
        "temp_c": np.nan,
        "state_label": state_labels,
        "notes": "ESP32 NILM trace S4P10 laptop charger"
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_processed.to_csv(output_path, index=False)
    print(f"[PREPROCESSING] Saved {len(df_processed)} processed rows to: {output_path}")
    return df_processed


def preprocess_air_compressor(
    input_path: str = RAW_COMPRESSOR_PATH,
    output_path: str = os.path.join(PROCESSED_DIR, "compressor_processed.csv"),
    max_rows: int | None = None
) -> pd.DataFrame:
    """
    Preprocess MetroPT-3 air compressor telemetry.
    Standardizes schema: ts, machine_id, i_rms_a, v_nominal, pf_assumed, kw_est, temp_c, state_label, notes.
    """
    print(f"[PREPROCESSING] Loading Air Compressor data from: {input_path}")
    if max_rows:
        df_raw = pd.read_csv(input_path, nrows=max_rows)
    else:
        df_raw = pd.read_csv(input_path)
        
    # Drop unnamed index column if present
    if "Unnamed: 0" in df_raw.columns:
        df_raw = df_raw.drop(columns=["Unnamed: 0"])
        
    # Parse timestamp and sort chronologically
    df_raw["timestamp"] = pd.to_datetime(df_raw["timestamp"])
    df_raw = df_raw.sort_values(by="timestamp").reset_index(drop=True)
    df_raw = df_raw.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    
    # Drop missing Motor_current
    df_raw = df_raw.dropna(subset=["Motor_current"]).reset_index(drop=True)
    df_raw["Motor_current"] = pd.to_numeric(df_raw["Motor_current"], errors="coerce")
    df_raw = df_raw.dropna(subset=["Motor_current"]).reset_index(drop=True)
    
    # Derive ground-truth operational states from physical signals:
    # < 0.20 A: OFF (motor unpowered, stopped, TP2 ~ 0 bar)
    # >= 4.80 A: ACTIVE (loaded compression, pumping air, TP2 > 8 bar)
    # [0.20, 4.80) A: IDLE (unloaded motor running ~3.8 A, intake closed, 0 bar pressure)
    conditions = [
        df_raw["Motor_current"] < 0.20,
        df_raw["Motor_current"] >= 4.80
    ]
    labels = ["OFF", "ACTIVE"]
    state_labels = np.select(conditions, labels, default="IDLE")
    
    # Estimate kW = sqrt(3) * 400V * I * 0.85 / 1000
    kw_est = np.round(np.sqrt(3) * 400.0 * df_raw["Motor_current"] * 0.85 / 1000.0, 4)
    
    df_processed = pd.DataFrame({
        "ts": df_raw["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        "machine_id": "compressor_01",
        "i_rms_a": np.round(df_raw["Motor_current"].astype(float), 4),
        "v_nominal": 400.0,
        "pf_assumed": 0.85,
        "kw_est": kw_est,
        "temp_c": np.round(df_raw["Oil_temperature"].astype(float), 2) if "Oil_temperature" in df_raw else np.nan,
        "state_label": state_labels,
        "notes": "MetroPT-3 industrial air compressor telemetry"
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_processed.to_csv(output_path, index=False)
    print(f"[PREPROCESSING] Saved {len(df_processed)} processed rows to: {output_path}")
    return df_processed


def get_chronological_splits(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset chronologically into train, validation, and test sets.
    Strictly avoids temporal data leakage.
    """
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    test_df = df.iloc[val_end:].copy().reset_index(drop=True)
    
    print(f"[SPLIT] Total rows: {n} -> Train: {len(train_df)} ({train_ratio*100:.1f}%), Val: {len(val_df)} ({val_ratio*100:.1f}%), Test: {len(test_df)} ({test_ratio*100:.1f}%)")
    return train_df, val_df, test_df


if __name__ == "__main__":
    print("Running preprocessing for both machines...")
    preprocess_laptop_charger()
    preprocess_air_compressor()
