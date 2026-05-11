import pandas as pd
import numpy as np
from src.intelligence_layers.quant_metrics import QuantEngine

def test_quant_engine():
    # إنشاء بيانات وهمية
    dates = pd.date_range(start="2023-01-01", periods=100)
    data = 100 + np.random.normal(0, 1, 100).cumsum()
    df = pd.DataFrame({"Close": data}, index=dates)

    market_data = 100 + np.random.normal(0, 1, 100).cumsum()
    market_df = pd.DataFrame({"Close": market_data}, index=dates)

    metrics = QuantEngine.get_risk_metrics(df, market_df)
    print("Metrics calculated:", metrics)
    assert "daily_volatility" in metrics
    assert "ewma_volatility" in metrics
    assert "var_95" in metrics
    assert "beta" in metrics
    print("Test passed!")

if __name__ == "__main__":
    test_quant_engine()
