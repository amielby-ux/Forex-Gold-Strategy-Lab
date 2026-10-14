"""Run baseline strategy comparisons on user-supplied UTC OHLC CSV."""
import argparse
import json
import pandas as pd
from .core import STRATEGIES, CostModel, validate_bars, signals, backtest, chronological_split

def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="CSV with timestamp,open,high,low,close (UTC)")
    p.add_argument("--spread", type=float, required=True, help="Full spread in quote-price units")
    p.add_argument("--slippage", type=float, default=0.)
    p.add_argument("--commission", type=float, default=0.)
    args = p.parse_args()
    df = pd.read_csv(args.csv, parse_dates=["timestamp"]).set_index("timestamp")
    if df.index.tz is None:
        raise ValueError("CSV timestamps must include UTC timezone offset")
    df = validate_bars(df)
    train, validation, test = chronological_split(df)
    cost = CostModel(args.spread, args.slippage, args.commission)
    # Indicator warm-up from earlier data; positions are evaluated only within each segment.
    rows = []
    for name in STRATEGIES:
        desired = signals(df, name)
        for label, segment in (("train", train), ("validation", validation), ("test", test)):
            result = backtest(segment, desired.loc[segment.index], cost)
            rows.append({"strategy": name, "split": label, **{k:v for k,v in result.items() if k != "trades"}})
    print(json.dumps(rows, indent=2, allow_nan=False))
if __name__ == "__main__":
    main()
