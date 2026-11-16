import numpy as np
import pandas as pd

from btc_quant.ledger import generate_forecast_events


def test_forecast_ledger_uses_validation_selected_alpha_by_horizon():
    n = 1200
    end = pd.Timestamp.now(tz="UTC").floor("D") - pd.Timedelta(days=1)
    timestamps = pd.date_range(end=end, periods=n, freq="D")
    t = np.arange(n, dtype=float)
    close = 30000.0 * np.exp(np.cumsum(0.0001 + 0.006 * np.sin(t / 19.0)))
    open_price = close * (1.0 + 0.001 * np.cos(t / 11.0))
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": open_price,
        "high": np.maximum(open_price, close) * 1.01,
        "low": np.minimum(open_price, close) * 0.99,
        "close": close,
        "volume": np.full(n, 100.0),
    })
    alphas = {1: 100.0, 3: 10.0, 7: 1.0, 30: 0.1}
    events = generate_forecast_events(
        frame, "manifest-hash", "test-commit",
        min_train_rows=100, ridge_alpha_by_horizon=alphas,
    )
    assert {event["horizon"] for event in events} == {1, 3, 7, 30}
    for event in events:
        alpha = alphas[event["horizon"]]
        assert f"alpha-{alpha:g}" in event["model_version"]
        assert f"alpha={alpha:g}" in event["notes"]
