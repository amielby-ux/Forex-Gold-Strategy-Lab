"""Read-only forward signal recorder for periodically updated M1 market CSV.

This is NOT an order execution engine. Feed must contain genuine UTC data.
Only finalized candles are considered. No claims of live connectivity.
"""
import argparse
import json
from pathlib import Path
import pandas as pd
from .core import STRATEGIES, signals, validate_bars
from .data import load_ohlc_csv

def latest_closed_signal(df: pd.DataFrame, strategy: str, timeframe: str,
                         asof: pd.Timestamp) -> dict:
    """Return latest fully closed signal; exclude the currently forming bar.

    Bar timestamps are interpreted as bar START times.
    Resampling is aligned to UTC boundaries. Missing M1 source bars invalidate
    their enclosing higher-timeframe bar.
    """
    if timeframe not in ("15min", "1h", "4h"):
        raise ValueError("Unsupported timeframe")
    if asof.tzinfo is None:
        raise ValueError("asof must be timezone-aware")
    asof = asof.tz_convert("UTC")
    df = validate_bars(df)
    if df.index.tz is None:
        raise ValueError("UTC timestamps required")
    df = df.tz_convert("UTC")
    if (df.index.second != 0).any() or (df.index.microsecond != 0).any():
        raise ValueError("Expected minute-aligned timestamps")
    # Filter incomplete one-minute candles before aggregating.
    df = df.loc[df.index + pd.Timedelta("1min") <= asof]
    if df.empty:
        raise ValueError("No closed M1 candles")
    grouped = df.resample(timeframe, label="left", closed="left")
    candles = grouped.agg({"open":"first","high":"max","low":"min","close":"last"})
    counts = grouped["close"].count()
    expected = int(pd.Timedelta(timeframe) / pd.Timedelta("1min"))
    # A full count of distinct, minute-aligned timestamps implies no missing
    # minute slots inside the bucket.
    candles = candles[(counts == expected) &
                      (candles.index + pd.Timedelta(timeframe) <= asof)].dropna()
    if len(candles) < 210:
        raise ValueError(f"Need at least 210 complete {timeframe} candles; got {len(candles)}")
    position = int(signals(candles, strategy).iloc[-1])
    stamp = candles.index[-1]
    return {"strategy":strategy,"timeframe":timeframe,
            "bar_open_utc":stamp.isoformat(),
            "bar_close_utc":(stamp+pd.Timedelta(timeframe)).isoformat(),
            "signal":position,"signal_label":{1:"LONG",-1:"SHORT",0:"FLAT"}[position],
            "last_mid_close":float(candles.close.iloc[-1]),
            "complete_bars":len(candles),
            "mode":"read_only_forward_observation","orders_sent":0}

def append_once(output: Path, record: dict) -> bool:
    """Idempotent by strategy/timeframe/closed-bar timestamp."""
    key = (record["strategy"],record["timeframe"],record["bar_close_utc"])
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        for line in output.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            old=json.loads(line)
            if (old["strategy"],old["timeframe"],old["bar_close_utc"]) == key:
                return False
    with output.open("a",encoding="utf-8") as f:
        f.write(json.dumps(record,allow_nan=False)+"\n")
    return True

def main():
    p=argparse.ArgumentParser(description="Record closed-bar signals; NO trading orders")
    p.add_argument("csv",help="Continuously refreshed UTC M1 OHLC CSV")
    p.add_argument("--asof",help="UTC observation time (default: current UTC)")
    p.add_argument("--output",default="data/forward_signals.jsonl")
    p.add_argument("--strategy",choices=STRATEGIES,default="ema_cross")
    p.add_argument("--timeframe",choices=["15min","1h","4h"],default="15min")
    args=p.parse_args()
    now=pd.Timestamp(args.asof) if args.asof else pd.Timestamp.now(tz="UTC")
    result=latest_closed_signal(load_ohlc_csv(args.csv),args.strategy,args.timeframe,now)
    result["observed_at_utc"]=pd.Timestamp.now(tz="UTC").isoformat()
    result["recorded"]=append_once(Path(args.output),result)
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
