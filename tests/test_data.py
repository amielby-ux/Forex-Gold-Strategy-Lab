import pandas as pd
import pytest
from strategy_lab.data import load_ohlc_csv, resample_ohlc

def test_csv_requires_timezone(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_text("timestamp,open,high,low,close\n2024-01-01 00:00:00,100,101,99,100\n")
    with pytest.raises(ValueError, match="UTC offset"):
        load_ohlc_csv(path)

def test_csv_accepts_utc(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_text("timestamp,open,high,low,close\n2024-01-01T00:00:00Z,100,101,99,100\n")
    df = load_ohlc_csv(path)
    assert str(df.index.tz) == "UTC"

def test_resampling_omits_partial_buckets():
    idx = pd.date_range("2024-01-01", periods=31, freq="min", tz="UTC")
    df = pd.DataFrame({"open":100., "high":101., "low":99., "close":100.}, index=idx)
    out = resample_ohlc(df, "15min")
    assert len(out) == 2
