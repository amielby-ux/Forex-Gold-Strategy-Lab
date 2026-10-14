"""Import and normalize user-provided OHLC CSVs (no provider dependency).

Timestamps must be explicit UTC or timezone-offset strings; do not silently
interpret naive local times as UTC. Store normalized datasets outside Git.
"""
from pathlib import Path
import pandas as pd
from .core import validate_bars

def load_ohlc_csv(path: str | Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close"}
    if not required.issubset(raw.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(raw.columns))}")
    if raw["timestamp"].isna().any():
        raise ValueError("Missing timestamps")
    # Require a timezone designator for every record to avoid silently
    # interpreting broker-local times as UTC.
    stamps = raw["timestamp"].astype(str)
    if not stamps.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", case=False, regex=True).all():
        raise ValueError("All timestamps must include Z or an explicit UTC offset")
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True, errors="raise")
    return validate_bars(raw.set_index("timestamp").sort_index())

def resample_ohlc(df: pd.DataFrame, frequency: str) -> pd.DataFrame:
    """Resample complete, evenly spaced source bars only.

    Incomplete intervals are excluded using expected source bar counts.
    Intended for 1-minute input resampled to 15min, 1h, or 4h;
    irregular/missing source data must be cleaned before use.
    """
    df = validate_bars(df)
    if frequency not in ("15min", "1h", "4h"):
        raise ValueError("Unsupported frequency")
    if len(df) < 2:
        raise ValueError("Need at least two bars")
    spacing = df.index.to_series().diff().dropna().mode()
    if spacing.empty:
        raise ValueError("Cannot infer source frequency")
    step = spacing.iloc[0]
    target = pd.Timedelta(frequency)
    if step <= pd.Timedelta(0) or target % step != pd.Timedelta(0):
        raise ValueError("Source spacing must divide target frequency")
    expected = int(target / step)
    grouped = df.resample(frequency, label="left", closed="left")
    result = grouped.agg({"open":"first","high":"max","low":"min","close":"last"})
    counts = grouped["close"].count()
    result = result[counts == expected].dropna()
    return validate_bars(result)
