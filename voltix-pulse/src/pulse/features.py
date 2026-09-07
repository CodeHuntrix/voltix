"""
Voltix Pulse Engine — Feature Engineering Module
Computes causal, observation-based rolling temporal features without future leakage.
Features:
  - i_rms_a: instantaneous current
  - i_mean_3samples: 3-sample causal rolling mean
  - i_std_3samples: 3-sample causal rolling standard deviation
"""

import os
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
FEATURE_NAMES = ["i_rms_a", "i_mean_3samples", "i_std_3samples"]
FEATURES_DIR = os.environ.get("VOLTIX_FEATURES_DIR", os.path.join(PROJECT_ROOT, "data", "features"))


def compute_causal_features(
    series: pd.Series,
    window: int = 3,
    history_prefix: pd.Series | None = None
) -> tuple[pd.Series, pd.Series]:
    """
    Compute causal rolling mean and standard deviation over past observations only.
    Strictly avoids future data leakage.
    If history_prefix is supplied (from prior chronological split), prepends it to maintain
    continuity at split boundaries without lookahead bias.
    """
    if history_prefix is not None and len(history_prefix) > 0:
        # Prepend up to (window - 1) observations from previous chronological split
        tail = history_prefix.iloc[-(window - 1):]
        combined = pd.concat([tail, series], ignore_index=True)
        r_mean = combined.rolling(window=window, min_periods=1).mean().iloc[len(tail):].reset_index(drop=True)
        r_std = combined.rolling(window=window, min_periods=1).std().fillna(0.0).iloc[len(tail):].reset_index(drop=True)
    else:
        r_mean = series.rolling(window=window, min_periods=1).mean()
        r_std = series.rolling(window=window, min_periods=1).std().fillna(0.0)
        
    return r_mean, r_std


def extract_features_for_dataframe(
    df: pd.DataFrame,
    history_prefix: pd.Series | None = None
) -> pd.DataFrame:
    """
    Extracts the feature matrix [i_rms_a, i_mean_3samples, i_std_3samples]
    along with target state_label and metadata columns.
    """
    df_feat = df.copy()
    i_series = df_feat["i_rms_a"].astype(float)
    
    r_mean, r_std = compute_causal_features(i_series, window=3, history_prefix=history_prefix)
    
    df_feat["i_mean_3samples"] = np.round(r_mean, 4)
    df_feat["i_std_3samples"] = np.round(r_std, 4)
    
    return df_feat


def generate_and_save_features(
    machine: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str = FEATURES_DIR
) -> dict[str, pd.DataFrame]:
    """
    Generates causal features for train, val, and test splits with strict chronological order.
    Saves features to CSV files in data/features/.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Train features: strictly causal within training data
    train_feat = extract_features_for_dataframe(train_df, history_prefix=None)
    
    # 2. Val features: causal with training tail as history (no future leakage)
    val_feat = extract_features_for_dataframe(val_df, history_prefix=train_df["i_rms_a"])
    
    # 3. Test features: causal with validation tail as history (no future leakage)
    test_feat = extract_features_for_dataframe(test_df, history_prefix=val_df["i_rms_a"])
    
    train_path = os.path.join(output_dir, f"{machine}_features_train.csv")
    val_path = os.path.join(output_dir, f"{machine}_features_val.csv")
    test_path = os.path.join(output_dir, f"{machine}_features_test.csv")
    
    train_feat.to_csv(train_path, index=False)
    val_feat.to_csv(val_path, index=False)
    test_feat.to_csv(test_path, index=False)
    
    print(f"[FEATURES] Generated and saved feature splits for '{machine}':")
    print(f"  Train: {train_path} ({len(train_feat)} rows)")
    print(f"  Val:   {val_path} ({len(val_feat)} rows)")
    print(f"  Test:  {test_path} ({len(test_feat)} rows)")
    
    return {"train": train_feat, "val": val_feat, "test": test_feat}
