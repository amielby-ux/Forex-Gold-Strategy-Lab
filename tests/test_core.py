import numpy as np
import pandas as pd
import pytest
from strategy_lab.core import CostModel, STRATEGIES, backtest, chronological_split, signals, validate_bars

def bars(n=300):
    ix = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    close = pd.Series(100 + np.arange(n)*0.1, index=ix)
    return pd.DataFrame({"open": close, "high": close+1, "low": close-1, "close": close}, index=ix)

def test_all_strategies_emit_valid_positions():
    df = bars()
    for name in STRATEGIES:
        s = signals(df, name)
        assert s.index.equals(df.index)
        assert s.isin([-1, 0, 1]).all()

def test_next_open_not_same_bar_and_costs():
    df = bars(4)
    s = pd.Series([1, 0, 0, 0], index=df.index)
    no_cost = backtest(df, s)
    with_cost = backtest(df, s, CostModel(spread=0.2, slippage=0.05, commission=0.01))
    assert no_cost["count"] == 1
    assert no_cost["trades"][0]["entry_time"] == df.index[1]
    assert no_cost["trades"][0]["exit_time"] == df.index[2]
    assert with_cost["net_pnl_quote_per_unit"] == pytest.approx(no_cost["net_pnl_quote_per_unit"] - 0.31)

def test_invalid_data_rejected():
    df = bars()
    df.iloc[0, df.columns.get_loc("high")] = 1
    with pytest.raises(ValueError):
        validate_bars(df)

def test_chronological_splits_do_not_overlap():
    a, b, c = chronological_split(bars(100))
    assert (len(a), len(b), len(c)) == (60, 20, 20)
    assert a.index[-1] < b.index[0] < c.index[0]
