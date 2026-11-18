import io
import zipfile

from btc_quant.acquisition import _parse_binance_zip, _save_raw


def test_parse_binance_zip_preserves_venue_ohlcv_schema():
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("klines.csv", "1704067200000,42000,43000,41000,42500,12\n")
    frame = _parse_binance_zip(content.getvalue())
    assert list(frame.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert frame.iloc[0]["close"] == 42500


def test_parse_binance_zip_supports_microsecond_timestamps():
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("klines.csv", "1704067200000000,42000,43000,41000,42500,12\n")
    frame = _parse_binance_zip(content.getvalue())
    assert frame.iloc[0]["timestamp"].isoformat() == "2024-01-01T00:00:00+00:00"


def test_raw_manifest_records_schema_grade_and_terms(tmp_path):
    record = _save_raw(
        tmp_path, "sample.json", b"{}",
        "https://example.invalid/sample", "Test public source",
        "TestVenue", "BTC-USD", "USD", source_grade="B",
    )
    assert record["schema_version"] == "1.0"
    assert record["source_grade"] == "B"
    assert "provider terms apply" in record["license_terms_note"]
    assert record["size_bytes"] == 2


def test_binance_daily_window_uses_frozen_utc_asof(monkeypatch, tmp_path):
    from datetime import UTC, date, datetime

    import pandas as pd

    from btc_quant import acquisition

    requested = []
    class Response:
        def __init__(self, status_code):
            self.status_code = status_code
            self.content = b"test-zip"
        def raise_for_status(self):
            return None

    class Session:
        def __init__(self):
            self.headers = {}
        def get(self, url, timeout):
            requested.append(url)
            return Response(200 if "BTCUSDT-1d-2026-11-17.zip" in url else 404)

    monkeypatch.setattr(acquisition.requests, "Session", Session)
    monkeypatch.setattr(acquisition, "_parse_binance_zip", lambda payload: pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-11-17T00:00:00Z")],
        "open": [100.0], "high": [102.0], "low": [99.0],
        "close": [101.0], "volume": [10.0],
    }))
    frame, manifest = acquisition.download_binance_daily(
        tmp_path, start=date(2026, 11, 1),
        now=datetime(2026, 11, 18, 0, 6, tzinfo=UTC),
    )
    assert any("BTCUSDT-1d-2026-11-17.zip" in url for url in requested)
    assert not any("BTCUSDT-1d-2026-11-18.zip" in url for url in requested)
    assert frame.iloc[-1]["timestamp"] == pd.Timestamp("2026-11-17T00:00:00Z")
    assert manifest["last_timestamp"] == "2026-11-17T00:00:00+00:00"


def test_bitstamp_window_uses_frozen_utc_asof(monkeypatch, tmp_path):
    from datetime import UTC, datetime

    import pandas as pd

    from btc_quant import acquisition

    as_of = datetime(2026, 11, 18, 0, 6, tzinfo=UTC)
    candle_ts = int(datetime(2026, 11, 17, 0, 0, tzinfo=UTC).timestamp())
    class Response:
        content = b"bitstamp-json"
        url = "https://www.bitstamp.net/api/v2/ohlc/btcusd/"
        def raise_for_status(self):
            return None
        def json(self):
            return {"data": {"ohlc": [{
                "timestamp": str(candle_ts), "open": "100", "high": "102",
                "low": "99", "close": "101", "volume": "10",
            }]}}

    class Session:
        def __init__(self):
            self.headers = {}
        def get(self, url, params, timeout):
            assert params["end"] == int(as_of.timestamp())
            return Response()

    monkeypatch.setattr(acquisition.requests, "Session", Session)
    frame, manifest = acquisition.download_bitstamp_recent(tmp_path, days=1, now=as_of)
    assert frame.iloc[-1]["timestamp"] == pd.Timestamp("2026-11-17T00:00:00Z")
    assert manifest["last_timestamp"] == "2026-11-17T00:00:00+00:00"
