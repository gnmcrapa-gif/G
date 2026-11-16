import numpy as np
import pandas as pd

from btc_quant.research import make_features, score_predictions


def test_features_use_only_current_and_past_closes():
    frame = pd.DataFrame({"close": np.arange(100.0, 200.0)})
    first = make_features(frame)
    changed = frame.copy()
    changed.loc[99, "close"] = 99999.0
    second = make_features(changed)
    pd.testing.assert_series_equal(first.loc[:98, "ret_1"], second.loc[:98, "ret_1"])


def test_score_predictions_counts_oos_forecasts():
    frame = pd.DataFrame({
        "horizon": [1, 1, 1],
        "actual": [0.1, -0.1, 0.0],
        "zero": [0.0, 0.0, 0.0],
        "drift": [0.01, 0.01, 0.01],
        "momentum": [0.1, -0.1, 0.1],
        "ridge": [0.08, -0.08, 0.02],
    })
    result = score_predictions(frame)
    assert result["holdout_metrics"]["1"]["zero"]["n"] == 3
    assert result["status"] == "SCORED_NOT_PROMOTED"
