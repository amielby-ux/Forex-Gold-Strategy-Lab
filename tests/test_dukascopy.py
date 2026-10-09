from datetime import datetime, timezone
import lzma
import struct
import pytest
from strategy_lab.dukascopy import decode_hour, hour_url, ticks_to_minutes

HOUR = datetime(2024, 1, 8, 8, tzinfo=timezone.utc)

def test_month_is_zero_based():
    assert "/2024/00/08/08h_ticks.bi5" in hour_url("XAUUSD", HOUR)

def test_decode_and_resample():
    packed = struct.pack(">IIIff", 5000, 2030123, 2029123, 1., 2.)
    ticks = decode_hour(lzma.compress(packed), HOUR, 1000)
    assert ticks.iloc[0]["bid"] == pytest.approx(2029.123)
    assert ticks.iloc[0]["ask"] == pytest.approx(2030.123)
    bars = ticks_to_minutes(ticks)
    assert len(bars) == 1
    assert bars.iloc[0]["spread_close"] == pytest.approx(1.)

def test_corrupt_payload_rejected():
    with pytest.raises(ValueError, match="record length"):
        decode_hour(lzma.compress(b"broken"), HOUR, 1000)
