import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

class QuantEngine:
    """
    محرك المقاييس الكمية وإدارة المخاطر (Dimension 5).
    يوفر نماذج التقلب (GARCH/EWMA)، VaR، وبيتا.
    """

    @staticmethod
    def calculate_ewma_volatility(returns, span=30):
        """
        حساب التقلب باستخدام المتوسط المتحرك المرجح أسياً (EWMA).
        """
        if len(returns) < 2:
            return 0.0
        # حساب التباين المرجح أسياً
        vols = returns.ewm(span=span).std() * np.sqrt(252)
        return float(vols.iloc[-1])

    @staticmethod
    def calculate_var(returns, confidence_level=0.95, timeframe=1):
        """
        حساب القيمة المعرضة للخطر (Value at Risk) باستخدام المحاكاة التاريخية.
        """
        if len(returns) < 20:
            return 0.0

        var_percentile = 1 - confidence_level
        var = np.percentile(returns, var_percentile * 100)

        # تعديل حسب الإطار الزمني (عادة يوم واحد)
        var_adjusted = var * np.sqrt(timeframe)
        return float(abs(var_adjusted))

    @staticmethod
    def calculate_beta(asset_returns, market_returns):
        """
        حساب بيتا (Beta) للأصل مقابل مؤشر السوق (S&P 500).
        """
        # محاذاة البيانات
        combined = pd.concat([asset_returns, market_returns], axis=1).dropna()
        if len(combined) < 20:
            return 1.0

        combined.columns = ['asset', 'market']

        X = add_constant(combined['market'])
        model = OLS(combined['asset'], X).fit()

        return float(model.params['market'])

    @staticmethod
    def get_risk_metrics(asset_df, market_df=None):
        """
        تجميع كافة المقاييس الكمية.
        """
        if asset_df is None or asset_df.empty:
            return {}

        # حساب العوائد اللوغاريتمية
        close_prices = asset_df['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]

        returns = np.log(close_prices / close_prices.shift(1)).dropna()

        metrics = {
            "daily_volatility": float(returns.std() * np.sqrt(252)),
            "ewma_volatility": QuantEngine.calculate_ewma_volatility(returns),
            "var_95": QuantEngine.calculate_var(returns, 0.95),
            "var_99": QuantEngine.calculate_var(returns, 0.99),
        }

        if market_df is not None and not market_df.empty:
            market_close = market_df['Close']
            if isinstance(market_close, pd.DataFrame):
                market_close = market_close.iloc[:, 0]
            market_returns = np.log(market_close / market_close.shift(1)).dropna()
            metrics["beta"] = QuantEngine.calculate_beta(returns, market_returns)

        return metrics
