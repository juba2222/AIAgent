import pandas as pd
import numpy as np

class OptionsGexEngine:
    """
    محرك تحليل تمركزات الغاما (Gamma Exposure) وحدود السيولة (Dimension 9).
    """

    @staticmethod
    def calculate_simulated_gex(df):
        """
        محاكاة GEX بناءً على مستويات السعر والحجم والتقلب،
        في حال غياب بيانات الأوبشن اللحظية.
        """
        if df is None or df.empty:
            return {}

        close = df['Close'].iloc[-1]
        if isinstance(close, (pd.Series, pd.DataFrame)):
            close = close.iloc[0]

        # محاكاة مستويات GEX الكبرى (حوائط العقود)
        # استخدام التقلب السنوي لتقدير الحدود
        returns = df['Close'].pct_change().dropna()
        if isinstance(returns, pd.DataFrame): returns = returns.iloc[:, 0]

        volatility = returns.std() * np.sqrt(252) # Annualized Vol

        # تقدير مستويات غاما بناءً على المستويات النفسية والتقلب
        # الحوائط عادة ما تكون عند 1-2 انحراف معياري شهري
        monthly_vol = volatility / np.sqrt(12)

        call_wall = float(close * (1 + monthly_vol))
        put_wall = float(close * (1 - monthly_vol))

        # Gamma Flip: نقطة التعادل؛ عادة ما تكون قريبة من المتوسط المتحرك 20 يوم
        gamma_flip = float(df['Close'].tail(20).mean())
        if isinstance(gamma_flip, pd.Series): gamma_flip = gamma_flip.iloc[0]

        return {
            "current_gex": "Positive" if float(close) > gamma_flip else "Negative",
            "call_wall": round(call_wall, 2),
            "put_wall": round(put_wall, 2),
            "gamma_flip": round(gamma_flip, 2),
            "liquidity_zones": [round(call_wall, 2), round(put_wall, 2)]
        }

    @staticmethod
    def get_options_context(assets_dict, executor):
        options_data = {}
        for name, ticker in assets_dict.items():
            df = executor.fetch_ohlcv_data(ticker)
            if df is not None:
                options_data[name] = OptionsGexEngine.calculate_simulated_gex(df)
        return options_data
