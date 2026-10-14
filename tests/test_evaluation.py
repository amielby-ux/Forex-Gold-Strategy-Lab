import numpy as np
import pandas as pd
from strategy_lab.core import CostModel
from strategy_lab.evaluation import evaluate_candidates, validation_ranking

def test_evaluation_is_deterministic():
    idx = pd.date_range("2020-01-01", periods=400, freq="h", tz="UTC")
    close = pd.Series(100 + np.sin(np.arange(400)/8)*2 + np.arange(400)*0.02, index=idx)
    df = pd.DataFrame({"open":close,"high":close+1,"low":close-1,"close":close}, index=idx)
    first = evaluate_candidates(df, CostModel(spread=.02), ("ema_cross", "macd"))
    second = evaluate_candidates(df, CostModel(spread=.02), ("ema_cross", "macd"))
    assert [x.validation["net_pnl_quote_per_unit"] for x in first] == [x.validation["net_pnl_quote_per_unit"] for x in second]
    assert validation_ranking(first, minimum_trades=1000) == []
