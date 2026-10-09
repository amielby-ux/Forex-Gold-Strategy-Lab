"""Deterministic, next-bar execution backtesting baseline.

All prices are mid OHLC. Signals are computed at bar close and filled at
the NEXT bar's open. Spread is quoted in PRICE units, not pips.
The simulator uses one position at a time and a constant unit size.
No stop/target, leverage, funding or portfolio margin are modeled yet.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

SYMBOLS = ("XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD")
TIMEFRAMES = ("15min", "1h", "4h")

def validate_bars(df: pd.DataFrame) -> pd.DataFrame:
    required = {"open", "high", "low", "close"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing OHLC columns: {sorted(required - set(df.columns))}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DatetimeIndex required")
    if df.index.tz is None:
        raise ValueError("Timestamps must be timezone-aware (UTC recommended)")
    if df.empty or not df.index.is_monotonic_increasing or df.index.has_duplicates:
        raise ValueError("Bars must be nonempty, unique and chronologically sorted")
    out = df.copy()
    for col in required:
        out[col] = pd.to_numeric(out[col], errors="raise")
    if not np.isfinite(out[list(required)].to_numpy(dtype=float)).all():
        raise ValueError("OHLC contains NaN or infinity")
    if (out[list(required)] <= 0).any().any():
        raise ValueError("OHLC must be positive")
    if ((out.high < out[["open", "close", "low"]].max(axis=1)) |
        (out.low > out[["open", "close", "high"]].min(axis=1))).any():
        raise ValueError("Invalid OHLC candle")
    return out

def ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False, min_periods=n).mean()

def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    change = series.diff()
    up = change.clip(lower=0).ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    down = (-change.clip(upper=0)).ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    rs = up / down.replace(0, np.nan)
    result = 100 - 100 / (1 + rs)
    return result.where(down != 0, 100).where(up != 0, 0).where((up + down) != 0, 50)

def signals(df: pd.DataFrame, name: str) -> pd.Series:
    """Desired position after each close: -1, 0 or +1."""
    c, h, l = df.close, df.high, df.low
    s = pd.Series(0, index=df.index, dtype=int)
    if name == "trend":
        a, b = ema(c, 50), ema(c, 200)
        s = pd.Series(np.where(a > b, 1, np.where(a < b, -1, 0)), index=c.index)
        s[(a.isna()) | (b.isna())] = 0
    elif name == "ema_cross":
        a, b = ema(c, 20), ema(c, 50)
        s = pd.Series(np.where(a > b, 1, np.where(a < b, -1, 0)), index=c.index)
        s[b.isna()] = 0
    elif name == "breakout":
        hi, lo = h.shift(1).rolling(20).max(), l.shift(1).rolling(20).min()
        s[c > hi] = 1
        s[c < lo] = -1
        s = s.replace(0, np.nan).ffill().fillna(0).astype(int)
    elif name == "rsi_reversion":
        r = rsi(c)
        s[r < 30] = 1
        s[r > 70] = -1
        s = s.replace(0, np.nan).ffill().fillna(0).astype(int)
    elif name == "bollinger":
        avg = c.rolling(20).mean()
        sd = c.rolling(20).std()
        s[c < avg - 2*sd] = 1
        s[c > avg + 2*sd] = -1
        s = s.replace(0, np.nan).ffill().fillna(0).astype(int)
    elif name == "macd":
        m = ema(c, 12) - ema(c, 26)
        sig = ema(m, 9)
        s = pd.Series(np.where(m > sig, 1, np.where(m < sig, -1, 0)), index=c.index)
        s[sig.isna()] = 0
    elif name == "support_resistance":
        hi, lo = h.shift(1).rolling(50).max(), l.shift(1).rolling(50).min()
        s[c > hi] = 1
        s[c < lo] = -1
        s = s.replace(0, np.nan).ffill().fillna(0).astype(int)
    elif name == "candlestick_trend":
        bull = (c > df.open) & (c.shift(1) < df.open.shift(1)) & (c >= df.open.shift(1)) & (df.open <= c.shift(1))
        bear = (c < df.open) & (c.shift(1) > df.open.shift(1)) & (c <= df.open.shift(1)) & (df.open >= c.shift(1))
        trend = ema(c, 50)
        s[bull & (c > trend)] = 1
        s[bear & (c < trend)] = -1
        s = s.replace(0, np.nan).ffill().fillna(0).astype(int)
    elif name == "trend_pullback":
        a, b = ema(c, 20), ema(c, 100)
        s[(a > b) & (c.shift(1) < a.shift(1)) & (c > a)] = 1
        s[(a < b) & (c.shift(1) > a.shift(1)) & (c < a)] = -1
        s = s.replace(0, np.nan).ffill().fillna(0).astype(int)
    elif name == "multi_factor":
        a, b, r = ema(c, 20), ema(c, 100), rsi(c)
        s[(a > b) & (r > 50) & (c > a)] = 1
        s[(a < b) & (r < 50) & (c < a)] = -1
    else:
        raise ValueError(f"Unknown strategy: {name}")
    return s.astype(int).clip(-1, 1)

STRATEGIES = ("trend", "ema_cross", "breakout", "rsi_reversion",
              "bollinger", "macd", "support_resistance", "candlestick_trend",
              "trend_pullback", "multi_factor")

@dataclass(frozen=True)
class CostModel:
    spread: float = 0.0  # full bid-ask spread in quote-price units
    slippage: float = 0.0  # adverse price movement per fill in quote-price units
    commission: float = 0.0  # quote-currency amount per unit per fill
    def __post_init__(self):
        if min(self.spread, self.slippage, self.commission) < 0:
            raise ValueError("Costs cannot be negative")

def backtest(df: pd.DataFrame, desired: pd.Series, costs: CostModel = CostModel()) -> dict:
    """Trades filled at NEXT open; force-close at final close, charged costs.

    Returns quote-currency P&L for one base unit, NOT account percentage return.
    This baseline is not comparable across symbols without normalization.
    """
    df = validate_bars(df)
    if not desired.index.equals(df.index) or desired.isna().any() or not desired.isin([-1, 0, 1]).all():
        raise ValueError("Signal index mismatch or invalid position")
    pos, entry, entry_time, trades = 0, None, None, []
    charge = costs.spread / 2 + costs.slippage + costs.commission
    for i in range(1, len(df)):
        target = int(desired.iloc[i-1])  # only information known at prior close
        if target == pos:
            continue
        mid = float(df.open.iloc[i])
        if pos:
            exit_price = mid - pos * (costs.spread/2 + costs.slippage)
            pnl = pos * (exit_price - entry) - costs.commission
            trades.append({"entry_time": entry_time, "exit_time": df.index[i], "side": pos, "pnl": pnl})
        pos = target
        if pos:
            entry = mid + pos * (costs.spread/2 + costs.slippage)
            entry_time = df.index[i]
        else:
            entry, entry_time = None, None
    if pos:
        mid = float(df.close.iloc[-1])
        exit_price = mid - pos * (costs.spread/2 + costs.slippage)
        trades.append({"entry_time": entry_time, "exit_time": df.index[-1],
                       "side": pos, "pnl": pos * (exit_price - entry) - costs.commission})
    pnls = np.asarray([t["pnl"] for t in trades], dtype=float)
    equity = np.r_[0., np.cumsum(pnls)]
    peak = np.maximum.accumulate(equity)
    wins = pnls[pnls > 0].sum()
    losses = -pnls[pnls < 0].sum()
    return {"trades": trades, "count": len(trades),
            "net_pnl_quote_per_unit": float(pnls.sum()),
            "win_rate": float((pnls > 0).mean()) if len(pnls) else None,
            "profit_factor": float(wins/losses) if losses > 0 else None,
            "expectancy_quote_per_unit": float(pnls.mean()) if len(pnls) else None,
            "max_drawdown_quote_per_unit": float((peak - equity).max())}

def chronological_split(df: pd.DataFrame, train=0.6, validation=0.2):
    if not (0 < train < 1 and 0 < validation < 1 and train + validation < 1):
        raise ValueError("Invalid split proportions")
    a, b = int(len(df)*train), int(len(df)*(train+validation))
    if min(a, b-a, len(df)-b) < 2:
        raise ValueError("Insufficient bars for split")
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]
