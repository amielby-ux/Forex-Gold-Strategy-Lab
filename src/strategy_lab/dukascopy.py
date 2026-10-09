"""Dukascopy public historical hourly tick archive reader.

Endpoint convention: /datafeed/{symbol}/{YYYY}/{zero-based-MM}/{DD}/{HH}h_ticks.bi5
The format is LZMA-compressed big-endian records: time_ms:uint32,
ask_points:uint32, bid_points:uint32, ask_volume:float32, bid_volume:float32.
Gold's point scaling is configurable: VERIFY it with source quotes before use.

Use responsibly, observe provider terms/rate limits, and do not redistribute data.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import argparse
import io
import lzma
import struct
import time
import urllib.error
import urllib.request

import pandas as pd

RECORD = struct.Struct(">IIIff")
BASE = "https://datafeed.dukascopy.com/datafeed"
POINT_DIVISORS = {"XAUUSD": 1000, "EURUSD": 100000, "GBPUSD": 100000,
                  "USDJPY": 1000, "AUDUSD": 100000, "USDCAD": 100000}

def hour_url(symbol: str, hour: datetime) -> str:
    if symbol not in POINT_DIVISORS:
        raise ValueError("Unsupported instrument")
    if hour.tzinfo is None or hour.utcoffset() != timedelta(0):
        raise ValueError("hour must be UTC")
    return f"{BASE}/{symbol}/{hour:%Y}/{hour.month-1:02d}/{hour:%d}/{hour:%H}h_ticks.bi5"

def decode_hour(payload: bytes, hour: datetime, divisor: int) -> pd.DataFrame:
    if divisor <= 0:
        raise ValueError("divisor must be positive")
    raw = lzma.decompress(payload)
    if len(raw) % RECORD.size:
        raise ValueError("Corrupt bi5 record length")
    rows = []
    for offset in range(0, len(raw), RECORD.size):
        millis, ask, bid, ask_volume, bid_volume = RECORD.unpack_from(raw, offset)
        if millis >= 3_600_000:
            raise ValueError("Invalid tick timestamp")
        if ask < bid or bid <= 0:
            raise ValueError("Invalid bid/ask tick")
        rows.append((hour + timedelta(milliseconds=millis), bid/divisor, ask/divisor,
                     bid_volume, ask_volume))
    if not rows:
        return pd.DataFrame(columns=["timestamp","bid","ask","bid_volume","ask_volume"])
    return pd.DataFrame(rows, columns=["timestamp","bid","ask","bid_volume","ask_volume"])

def fetch_hour(symbol: str, hour: datetime, divisor: int, timeout: float = 20.0,
               retries: int = 2) -> pd.DataFrame:
    url = hour_url(symbol, hour)
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StrategyLabResearch/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return decode_hour(response.read(), hour, divisor)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return pd.DataFrame(columns=["timestamp","bid","ask","bid_volume","ask_volume"])
            if exc.code not in (429, 500, 502, 503, 504) or attempt == retries:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == retries:
                raise
        time.sleep(min(2 ** attempt, 8))
    raise RuntimeError("Unexpected retry exit")

def ticks_to_minutes(ticks: pd.DataFrame) -> pd.DataFrame:
    if ticks.empty:
        return pd.DataFrame(columns=["open","high","low","close","bid_close","ask_close","spread_close"])
    ticks = ticks.sort_values("timestamp").set_index("timestamp")
    if ticks.index.tz is None:
        raise ValueError("UTC tick timestamps required")
    mid = (ticks.bid + ticks.ask) / 2
    bars = mid.resample("1min").ohlc()
    bars["bid_close"] = ticks.bid.resample("1min").last()
    bars["ask_close"] = ticks.ask.resample("1min").last()
    bars["spread_close"] = bars.ask_close - bars.bid_close
    return bars.dropna(subset=["open","high","low","close"])

def download(symbol: str, start: datetime, hours: int, output: Path,
             divisor: int, pause: float = 0.3) -> dict:
    if hours < 1 or hours > 168:
        raise ValueError("Single batch must be 1–168 hours")
    if start.tzinfo is None or start.utcoffset() != timedelta(0) or start.minute or start.second or start.microsecond:
        raise ValueError("Start must be aligned to UTC hour")
    if start + timedelta(hours=hours) > datetime.now(timezone.utc):
        raise ValueError("Cannot download future hours")
    frames, empty = [], 0
    for i in range(hours):
        ticks = fetch_hour(symbol, start + timedelta(hours=i), divisor)
        if ticks.empty:
            empty += 1
        else:
            frames.append(ticks_to_minutes(ticks))
        if i < hours-1:
            time.sleep(pause)
    if not frames:
        raise ValueError("No ticks returned. Check instrument, date and source access.")
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    output.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index().to_csv(output, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
    return {"symbol":symbol,"hours_requested":hours,"hours_without_ticks":empty,
            "minute_bars":len(df),"output":str(output)}

def main():
    p = argparse.ArgumentParser(description="Fetch Dukascopy historical ticks into 1-minute mid OHLC")
    p.add_argument("--symbol", choices=sorted(POINT_DIVISORS), default="XAUUSD")
    p.add_argument("--start", required=True, help="UTC hour, e.g. 2024-01-08T08:00:00Z")
    p.add_argument("--hours", type=int, default=24)
    p.add_argument("--divisor", type=int, default=None, help="Provider price-point divisor (verify with quotes)")
    p.add_argument("--output", default="data/dukascopy_1min.csv")
    args = p.parse_args()
    start = datetime.fromisoformat(args.start.replace("Z","+00:00"))
    divisor = args.divisor or POINT_DIVISORS[args.symbol]
    print(download(args.symbol, start, args.hours, Path(args.output), divisor))
if __name__ == "__main__":
    main()
