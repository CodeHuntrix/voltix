"""Feature engineering utilities for Voltix Condition / Drift Engine."""

import pandas as pd
import numpy as np
from typing import List


def extract_features_df(df: pd.DataFrame, window_size: int = 15) -> pd.DataFrame:
    """
    Extracts rolling features for a DataFrame containing 'i_rms_a'.
    Features computed:
    - i_rms_a: current sample
    - i_rolling_mean: rolling mean over window_size
    - i_rolling_std: rolling std over window_size
    """
    df_feat = df.copy()
    df_feat["i_rolling_mean"] = df_feat["i_rms_a"].rolling(window=window_size, min_periods=1).mean()
    df_feat["i_rolling_std"] = df_feat["i_rms_a"].rolling(window=window_size, min_periods=1).std().fillna(0.0)
    return df_feat


def extract_features_single(current_val: float, history: List[float] | None = None, window_size: int = 15) -> dict:
    """
    Extracts feature dictionary for online single-sample inference given history buffer.
    """
    if history is None or len(history) == 0:
        full_window = [current_val]
    else:
        full_window = list(history[-window_size + 1:]) + [current_val]
        
    arr = np.array(full_window, dtype=float)
    rolling_mean = float(np.mean(arr))
    rolling_std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    
    return {
        "i_rms_a": float(current_val),
        "i_rolling_mean": rolling_mean,
        "i_rolling_std": rolling_std,
    }
