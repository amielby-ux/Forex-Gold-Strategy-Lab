import json
import numpy as np
import pandas as pd
import pytest
from strategy_lab.forward_test import latest_closed_signal, append_once

def sample(minutes=211*15):
    idx=pd.date_range("2024-01-08T00:00:00Z",periods=minutes,freq="min")
    close=2000+np.arange(minutes)*.001
    return pd.DataFrame({"open":close,"high":close+.2,
                         "low":close-.2,"close":close},index=idx)

def test_only_closed_candles_are_used():
    df=sample()
    # Last minute of final 15min bucket not yet closed
    t=df.index[-1]+pd.Timedelta(seconds=20)
    record=latest_closed_signal(df,"ema_cross","15min",t)
    assert record["complete_bars"]==210
    assert record["orders_sent"]==0
    assert record["bar_close_utc"]=="2024-01-10T04:30:00+00:00"

def test_missing_minute_discards_whole_bucket():
    df=sample().drop(pd.Timestamp("2024-01-08T01:00:00Z"))
    with pytest.raises(ValueError,match="210 complete"):
        latest_closed_signal(df,"ema_cross","15min",df.index[-1]+pd.Timedelta(minutes=1))

def test_idempotent_record(tmp_path):
    p=tmp_path/"observations.jsonl"
    r={"strategy":"ema_cross","timeframe":"15min","bar_close_utc":"2024-01-01T00:15:00Z"}
    assert append_once(p,r)
    assert not append_once(p,r)
    assert len(p.read_text().splitlines())==1
