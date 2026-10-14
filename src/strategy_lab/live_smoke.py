"""Live, read-only Dukascopy sample verification.

Fails closed if endpoint, scale, spread, timestamps or bar output are implausible.
A single historical hour is fetched; this is NOT a multi-year backtest.
"""
from datetime import datetime, timezone
import json
from .dukascopy import fetch_hour, ticks_to_minutes

def main():
    hour = datetime(2024, 1, 8, 8, tzinfo=timezone.utc)
    ticks = fetch_hour("XAUUSD", hour, divisor=1000)
    if len(ticks) < 10:
        raise RuntimeError(f"Insufficient live ticks: {len(ticks)}")
    if not ticks.timestamp.between(hour, hour.replace(hour=9), inclusive="left").all():
        raise RuntimeError("Out-of-range timestamps")
    if not ticks.bid.between(1000, 5000).all() or not ticks.ask.between(1000, 5000).all():
        raise RuntimeError("Gold prices implausible: verify instrument point divisor")
    spread = ticks.ask - ticks.bid
    if (spread < 0).any() or spread.median() <= 0 or spread.median() > 10:
        raise RuntimeError("Implausible bid/ask spread: verify price scaling")
    bars = ticks_to_minutes(ticks)
    if bars.empty:
        raise RuntimeError("No minute bars produced")
    result = {"source":"Dukascopy public bi5 archive","symbol":"XAUUSD",
              "utc_hour":hour.isoformat(),"tick_count":len(ticks),
              "minute_bars":len(bars),"first_tick":str(ticks.timestamp.iloc[0]),
              "first_bid":float(ticks.bid.iloc[0]),"first_ask":float(ticks.ask.iloc[0]),
              "median_spread":float(spread.median()),
              "first_minute_mid_close":float(bars.close.iloc[0])}
    print(json.dumps(result, indent=2))
if __name__ == "__main__":
    main()
