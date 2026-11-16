import numpy as np
import pandas as pd

from btc_quant.research import _hac_loss_difference, _ridge_predict, _valid_indices, make_features, score_predictions


def test_features_use_only_current_and_past_closes():
    frame = pd.DataFrame({"close": np.arange(100.0, 200.0)})
    first = make_features(frame)
    changed = frame.copy()
    changed.loc[99, "close"] = 99999.0
    second = make_features(changed)
    pd.testing.assert_frame_equal(first.loc[:98], second.loc[:98])


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
    assert result["holdout_metrics"]["1"]["zero"]["directional_accuracy"] is None
    assert result["status"] == "SCORED_NOT_PROMOTED"


def test_ridge_accepts_read_only_numpy_inputs():
    x_train = np.arange(80.0).reshape(20, 4)
    y_train = np.linspace(-0.1, 0.1, 20)
    x_test = np.array([[81.0, 82.0, 83.0, 84.0]])
    x_train.setflags(write=False)
    y_train.setflags(write=False)
    x_test.setflags(write=False)
    prediction = _ridge_predict(x_train, y_train, x_test)
    assert prediction.shape == (1,)
    assert np.isfinite(prediction).all()


def test_valid_indices_uses_writable_mask_copies():
    target = pd.Series([0.1, np.nan, 0.2, 0.3])
    features = pd.DataFrame({"x": [1.0, 2.0, np.nan, 4.0]})
    indices = np.arange(4)
    selected = _valid_indices(target, features, indices)
    np.testing.assert_array_equal(selected, np.array([0, 3]))


def test_walk_forward_runs_purged_holdout_without_leakage():
    from btc_quant.research import walk_forward

    n = 1600
    end = pd.Timestamp.now(tz="UTC").floor("D") - pd.Timedelta(days=1)
    timestamps = pd.date_range(end=end, periods=n, freq="D")
    t = np.arange(n, dtype=float)
    close = 20000.0 * np.exp(np.cumsum(0.0002 + 0.008 * np.sin(t / 17.0)))
    open_price = close * (1.0 + 0.001 * np.sin(t / 7.0))
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": open_price,
        "high": np.maximum(open_price, close) * 1.01,
        "low": np.minimum(open_price, close) * 0.99,
        "close": close,
        "volume": np.full(n, 100.0),
    })
    predictions, summary = walk_forward(frame, min_train_rows=100, holdout_rows=365)
    assert summary["status"] == "SCORED_NOT_PROMOTED"
    assert summary["holdout_is_untouched"] is True
    assert summary["training_uses_holdout"] is False
    assert set(predictions["horizon"].unique()) == {1, 3, 7, 30}
    assert (predictions["split"] == "final_holdout").all()



def test_hac_loss_difference_detects_persistent_worse_challenger():
    actual = np.zeros(120)
    benchmark = np.zeros(120)
    challenger = np.full(120, 0.02)
    result = _hac_loss_difference(challenger, benchmark, actual, max_lag=6)
    assert result["mean_absolute_loss_difference"] > 0
    assert result["interpretation"] == "challenger_worse"
    assert result["hac_lags"] == 6
    assert result["two_sided_p_value_normal_approx"] < 0.05


def test_score_predictions_reports_regime_metrics_and_paired_tests():
    frame = pd.DataFrame({
        "horizon": [1] * 6,
        "actual": [0.01, -0.01, 0.02, -0.02, 0.01, -0.01],
        "zero": [0.0] * 6,
        "drift": [0.001] * 6,
        "momentum": [0.005, -0.005, 0.005, -0.005, 0.005, -0.005],
        "ridge": [0.02, -0.02, 0.03, -0.03, 0.02, -0.02],
        "regime": ["bull", "bull", "bear", "bear", "range", "range"],
    })
    result = score_predictions(frame)
    assert result["paired_loss_tests"]["1"]["ridge_vs_zero"]["n"] == 6
    assert set(result["regime_metrics"]["1"]) == {"bull", "bear", "range"}
    assert result["regime_metrics"]["1"]["bull"]["n"] == 2


def test_walk_forward_uses_three_purged_validation_folds():
    from btc_quant.research import walk_forward

    n = 1600
    end = pd.Timestamp.now(tz="UTC").floor("D") - pd.Timedelta(days=1)
    timestamps = pd.date_range(end=end, periods=n, freq="D")
    t = np.arange(n, dtype=float)
    close = 20000.0 * np.exp(np.cumsum(0.0002 + 0.008 * np.sin(t / 17.0)))
    open_price = close * (1.0 + 0.001 * np.sin(t / 7.0))
    frame = pd.DataFrame({
        "timestamp": timestamps, "open": open_price,
        "high": np.maximum(open_price, close) * 1.01,
        "low": np.minimum(open_price, close) * 0.99,
        "close": close, "volume": np.full(n, 100.0),
    })
    predictions, summary = walk_forward(frame, min_train_rows=100, holdout_rows=365)
    assert summary["status"] == "SCORED_NOT_PROMOTED"
    for horizon in ("1", "3", "7", "30"):
        assert len(summary["validation_tuning"][horizon]["validation_folds"]) == 3
    assert "regime" in predictions
