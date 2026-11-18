import io
import zipfile

import pytest

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


def test_binance_missing_daily_archive_uses_official_spot_rest_fallback(monkeypatch, tmp_path):
    from datetime import UTC, date, datetime

    import pandas as pd

    from btc_quant import acquisition

    as_of = datetime(2026, 11, 18, 0, 6, tzinfo=UTC)
    timestamp_ms = int(datetime(2026, 11, 17, 0, 0, tzinfo=UTC).timestamp() * 1000)
    requested = []
    class Response:
        def __init__(self, status_code, url, payload=None):
            import json
            self.status_code = status_code
            self.url = url
            self._payload = payload
            self.content = json.dumps(payload).encode() if payload is not None else b""
        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")
        def json(self):
            return self._payload

    class Session:
        def __init__(self):
            self.headers = {}
        def get(self, url, timeout, params=None):
            requested.append((url, params))
            if url.endswith("BTCUSDT-1d-2026-11-17.zip"):
                return Response(404, url)
            return Response(200, url, [[timestamp_ms, "100", "102", "99", "101", "10"]])

    monkeypatch.setattr(acquisition.requests, "Session", Session)
    frame, manifest = acquisition.download_binance_daily(
        tmp_path, start=date(2026, 11, 17), now=as_of
    )
    assert len(requested) == 2
    assert "BTCUSDT-1d-2026-11-17.zip" in requested[0][0]
    assert requested[1][0] == "https://data-api.binance.vision/api/v3/klines"
    assert requested[1][1]["startTime"] == timestamp_ms
    assert frame.iloc[-1]["timestamp"] == pd.Timestamp("2026-11-17T00:00:00Z")
    fallback = next(obj for obj in manifest["objects"] if obj.get("source_type") == "daily_rest_fallback")
    assert fallback["data_date_utc"] == "2026-11-17"
    assert fallback["sha256"]


def test_binance_rest_fallback_respects_official_endpoint_access_block(monkeypatch, tmp_path):
    from datetime import UTC, date, datetime

    from btc_quant import acquisition

    requested = []
    class Response:
        def __init__(self, status_code, url):
            self.status_code = status_code
            self.url = url
            self.content = b""
        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    class Session:
        def __init__(self):
            self.headers = {}
        def get(self, url, timeout, params=None):
            requested.append(url)
            return Response(404 if url.endswith("BTCUSDT-1d-2026-11-17.zip") else 451, url)

    monkeypatch.setattr(acquisition.requests, "Session", Session)
    with pytest.raises(RuntimeError, match="No Binance data acquired"):
        acquisition.download_binance_daily(
            tmp_path, start=date(2026, 11, 17),
            now=datetime(2026, 11, 18, 0, 6, tzinfo=UTC),
        )
    assert len(requested) == 2
    assert requested[1] == "https://data-api.binance.vision/api/v3/klines"
    assert all("binance.com" in url or "binance.vision" in url for url in requested)
