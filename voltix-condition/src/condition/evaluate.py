"""Evaluation runner comparing Baseline Z-Score vs IsolationForest on synthetic drift streams."""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any

from .data_loader import load_voltix_dataset, filter_active_data
from .features import extract_features_df
from .baseline import BaselineDriftModel
from .isolation_forest import IsolationForestDriftModel
from .scoring import DriftScorer


def evaluate_model_on_stream(model, scorer: DriftScorer, df_stream: pd.DataFrame, is_baseline: bool = True) -> Dict[str, Any]:
    """Evaluates a model instance over a sequence of stream samples."""
    scorer.reset_buffer()
    
    flags = []
    scores = []
    severities = []
    
    df_feat = extract_features_df(df_stream, window_size=model.params.get("window_size", 15) if is_baseline else 15)
    
    for idx, row in df_feat.iterrows():
        feat_dict = {
            "i_rms_a": float(row["i_rms_a"]),
            "i_rolling_mean": float(row["i_rolling_mean"]),
            "i_rolling_std": float(row["i_rolling_std"]),
        }
        
        if is_baseline:
            raw_score, _ = model.calculate_z_score(feat_dict)
            baseline_mean = model.params["means"]["i_rms_a"]
            baseline_std = model.params["stds"]["i_rms_a"]
        else:
            raw_score, _ = model.calculate_score(feat_dict)
            baseline_mean = 0.173
            baseline_std = 0.033
            
        flag, score, severity, msg = scorer.evaluate_sample(
            raw_z_score=raw_score,
            feature_val=float(row["i_rms_a"]),
            baseline_mean=baseline_mean,
            baseline_std=baseline_std,
        )
        
        flags.append(flag)
        scores.append(score)
        severities.append(severity)

    flags_arr = np.array(flags)
    scores_arr = np.array(scores)
    
    return {
        "sample_count": len(df_stream),
        "flag_count": int(np.sum(flags_arr)),
        "flag_rate": float(np.mean(flags_arr)),
        "mean_score": float(np.mean(scores_arr)),
        "max_score": float(np.max(scores_arr)),
        "flags": flags,
        "scores": scores,
    }


def run_full_evaluation(synthetic_streams: Dict[str, str], baseline_model: BaselineDriftModel, if_model: IsolationForestDriftModel) -> pd.DataFrame:
    """Runs cross-evaluation over all synthetic streams."""
    results = []
    
    for stream_name, file_path in synthetic_streams.items():
        df_stream = pd.read_csv(file_path)
        
        # Scorer instance for baseline
        scorer_base = DriftScorer(z_threshold=baseline_model.params.get("z_threshold", 3.0), score_lambda=0.4)
        res_base = evaluate_model_on_stream(baseline_model, scorer_base, df_stream, is_baseline=True)
        
        # Scorer instance for IsolationForest
        scorer_if = DriftScorer(z_threshold=1.5, score_lambda=0.5)
        res_if = evaluate_model_on_stream(if_model, scorer_if, df_stream, is_baseline=False)
        
        results.append({
            "Stream": stream_name,
            "Baseline_Flag_Rate (%)": round(res_base["flag_rate"] * 100, 2),
            "Baseline_Mean_Score": round(res_base["mean_score"], 4),
            "IsoForest_Flag_Rate (%)": round(res_if["flag_rate"] * 100, 2),
            "IsoForest_Mean_Score": round(res_if["mean_score"], 4),
        })

    return pd.DataFrame(results)
