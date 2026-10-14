import pandas as pd
from strategy_lab.data_quality import audit

def test_audit_flags_gap_without_claiming_bad_market_data():
    idx = pd.DatetimeIndex(["2024-01-08T00:00:00Z","2024-01-08T00:01:00Z",
                            "2024-01-08T00:04:00Z"])
    df = pd.DataFrame({"open":[100,101,102],"high":[101,102,103],
                       "low":[99,100,101],"close":[100,101,102]},index=idx)
    report = audit(df)
    assert report["irregular_intervals"] == 1
    assert report["estimated_missing_slots_including_market_closures"] == 2
    assert report["bars"] == 3
