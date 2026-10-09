"""Audit imported market OHLC bars before research use."""
from pathlib import Path
import json
import pandas as pd
from .data import load_ohlc_csv

def audit(df: pd.DataFrame, expected_frequency: str = "1min") -> dict:
    if expected_frequency not in ("1min", "15min", "1h", "4h"):
        raise ValueError("Unsupported frequency")
    if len(df) < 2:
        raise ValueError("Need at least two bars")
    step = pd.Timedelta(expected_frequency)
    gaps = df.index.to_series().diff().dropna()
    irregular = gaps[gaps != step]
    missing_slots = sum(max(int(delta / step) - 1, 0) for delta in gaps if delta > step)
    # Gaps include weekends and market closures, not necessarily data errors.
    return {"bars":int(len(df)), "start_utc":df.index[0].isoformat(),
            "end_utc":df.index[-1].isoformat(), "expected_frequency":expected_frequency,
            "irregular_intervals":int(len(irregular)),
            "estimated_missing_slots_including_market_closures":int(missing_slots),
            "largest_gap":str(gaps.max()),"first_irregular_timestamps":
            [t.isoformat() for t in irregular.index[:10]],
            "min_price":float(df.low.min()),"max_price":float(df.high.max())}

def main():
    import argparse
    p = argparse.ArgumentParser(description="Audit a historical OHLC CSV")
    p.add_argument("csv", type=Path)
    p.add_argument("--frequency",choices=["1min","15min","1h","4h"],default="1min")
    args=p.parse_args()
    print(json.dumps(audit(load_ohlc_csv(args.csv),args.frequency),indent=2))

if __name__=="__main__":
    main()
