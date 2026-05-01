import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.stattools import grangercausalitytests

class MacroAgent:
    """
    Macro Agent that fetches macro data, normalizes it, detects regime,
    calculates a Macro Score (0-100), and sets a Veto flag for dangerous confluence.
    """

    def __init__(self):
        # Configuration
        self.window = 30  # Days for rolling Z-score

        # API Endpoints (symbols)
        self.crypto_symbols = {
            "US10Y_TLT": "^TNX",   # 10Y Treasury Yield proxy
        }
        self.macro_symbols = {
            "VIX": "^VIX",
            "DXY": "DX-Y.NYB",
            "JNK": "JNK",         # High Yield Corporate Bond ETF
            "LQD": "LQD",         # Investment Grade Corporate Bond ETF
        }

        # Init API clients (keys loaded from environment)
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.alpaca_api_key = os.getenv('ALPACA_API_KEY')
        self.alpaca_secret = os.getenv('ALPACA_API_SECRET')

        # For now we'll mock data fetching; replace later with real API calls

    def _fetch_latest_price(self, symbol):
        """Mokup of fetching latest price using yfinance for demonstration."""
        try:
            if symbol.startswith('^'):
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                return hist['Close'].iloc[-1]
            else:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                return hist['Close'].iloc[-1]
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    def _fetch_fred_series(self, series_name):
        """Fetch M2 Money Supply series using FRED API (mocked)."""
        try:
            from fredapi import Fred
            fred = Fred(api_key=self.fred_api_key)
            data = fred.get_series(series_name)
            if len(data) > 0:
                return data.iloc[-1]
        except Exception as e:
            print(f"Error fetching FRED series {series_name}: {e}")
        return None

    def _calculate_z_score(self, series_data):
        """Calculate Z-score using rolling window."""
        series = pd.Series(series_data, dtype=float)
        if len(series.dropna()) < self.window:
            rolling_mean = series.dropna().mean()
            rolling_std = series.dropna().std()
        else:
            rolling_mean = series.rolling(window=self.window).mean()
            rolling_std = series.rolling(window=self.window).std()
        z_scores = (series - rolling_mean) / rolling_std
        z_scores_clipped = z_scores.clip(-3, 3)
        return z_scores_clipped.dropna()

    def _detect_regime(self, z_scores):
        """Detect regime based on heuristic mapping of high-dimensional z-scores."""
        # Simple heuristic: map cluster label to regime name
        # Since we don't fit KMeans here, fallback to heuristic naming
        if z_scores.get('DXY', 0) > 1.5 and z_scores.get('VIX', 0) > 1.5 and z_scores.get('US10Y_TLT', 0) > 1.5:
            return "Geopolitical Panic"
        elif z_scores.get('DXY', 0) > 1.5 and z_scores.get('VIX', 0) > 1.5:
            return "Liquidity Shock"
        elif z_scores.get('DXY', 0) < -1.5 and z_scores.get('US10Y_TLT', 0) < -1.5:
            return "Deflation"
        else:
            return "Goldilocks"

    def _calculate_macro_score(self, z_scores):
        """Calculate Macro Score from Z-scores (0-100) using linear mapping."""
        total = 0
        contributions = {}
        for key, val in z_scores.items():
            # Map Z-score range [-3, 3] to contribution [0, 20]
            contribution = max(0, min(20, (val + 3) * (20 / 6)))
            contributions[key] = contribution
            total += contribution
        return int(total), contributions

    def _check_veto(self, z_scores):
        """Veto flag = True if all three danger metrics are > 1.5 Z-score."""
        dangerous = [
            z_scores.get('DXY', 0) > 1.5,
            z_scores.get('VIX', 0) > 1.5,
            z_scores.get('US10Y_TLT', 0) > 1.5
        ]
        return all(dangerous)

    def generate(self):
        """Main entry point: fetch data, compute scores, and return structured result."""
        # ---- 1. Fetch raw data ----
        raw_data = {}
        # Treasury Yield proxy (US10Y)
        us10y_price = self._fetch_latest_price(self.crypto_symbols["US10Y_TLT"])
        raw_data["US10Y"] = us10y_price

        # VIX
        vix_price = self._fetch_latest_price(self.macro_symbols["VIX"])
        raw_data["VIX"] = vix_price

        # DXY
        dxy_price = self._fetch_latest_price(self.macro_symbols["DXY"])
        raw_data["DXY"] = dxy_price

        # Credit Spread (JNK - LQD)
        jnk_price = self._fetch_latest_price(self.macro_symbols["JNK"])
        lqd_price = self._fetch_latest_price(self.macro_symbols["LQD"])
        raw_data["CreditSpread"] = jnk_price - lqd_price if jnk_price and lqd_price else None

        # M2 Money Supply (mock)
        m2_supply = self._fetch_fred_series('M2SL')
        raw_data["M2"] = m2_supply

        # ---- 2. Build time series for Z-score calculations ----
        # For demonstration, we will simulate a short series of last 100 daily returns
        # In production, store historical values (e.g., in DB or file)
        def simulate_series(value, period=100, delta=None):
            series = [value]
            for _ in range(period-1):
                change = np.random.normal(delta) if delta else 0
                series.append(max(0, series[-1] * (1 + change)))
            return series[:period]

        # Create a small synthetic series for each metric to compute Z-scores
        series_len = 60  # days for rolling
        # Real implementation would pull from a DB or file; here we mock using random walk
        import random
        random.seed(42)

        def generate_rolling_series(base_value):
            return simulate_series(base_value, period=series_len, delta=0.001)

        # Generate rolling data (deque-like) for each metric
        def get_z_scores(metric_name, base_value):
            series = generate_rolling_series(base_value)
            z_series = self._calculate_z_score(series)
            return z_series.iloc[-1]

        z_scores = {
            'DXY': get_z_scores('DXY', raw_data['DXY']),
            'VIX': get_z_scores('VIX', raw_data['VIX']),
            'US10Y_TLT': get_z_scores('US10Y_TLT', raw_data['US10Y']),
        }

        # ---- 3. Compute regime, score, veto ----
        regime = self._detect_regime(z_scores)
        macro_score, contributions = self._calculate_macro_score(z_scores)
        veto = self._check_veto(z_scores)

        # ---- 4. Build and return result ----
        result = {
            "macro_score": macro_score,
            "regime": regime,
            "veto": veto,
            "raw": raw_data,
            "z_scores": z_scores,
            "contributions_by_metric": contributions
        }
        return result

if __name__ == "__main__":
    agent = MacroAgent()
    print("Running Macro Agent...")
    result = agent.generate()
    print(result)