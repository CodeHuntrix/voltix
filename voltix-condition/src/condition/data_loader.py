"""Data loading and cleaning utilities for Voltix Condition / Drift Engine."""

import os
import pandas as pd
import numpy as np


def load_voltix_dataset(file_path: str) -> pd.DataFrame:
    """
    Loads a Voltix-schema telemetry CSV file.
    Expected columns: ts, machine_id, i_rms_a, v_nominal, pf_assumed, kw_est, temp_c, state_label, notes
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    required_cols = ["ts", "machine_id", "i_rms_a", "state_label"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {file_path}")
            
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def filter_active_data(
    df: pd.DataFrame,
    steady_state_min_irms: float = 0.12,
    skip_warmup_rows: int = 30,
) -> pd.DataFrame:
    """
    Filters dataset to return only steady-state ACTIVE rows.

    Parameters
    ----------
    steady_state_min_irms:
        Minimum current (A) to be treated as steady ACTIVE operation.
        Rows below this are startup transients and are excluded.
    skip_warmup_rows:
        Number of initial ACTIVE rows to skip to allow rolling features to stabilise.
    """
    df_active = df[df["state_label"] == "ACTIVE"].copy()
    # Drop startup transients (sub-threshold current before charger settles)
    df_active = df_active[df_active["i_rms_a"] >= steady_state_min_irms].reset_index(drop=True)
    # Skip warmup to allow rolling window to fill with stable values
    if skip_warmup_rows > 0 and len(df_active) > skip_warmup_rows:
        df_active = df_active.iloc[skip_warmup_rows:].reset_index(drop=True)
    return df_active
