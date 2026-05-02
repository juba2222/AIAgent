import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from fredapi import Fred

class MacroAgent:
    """
    Macro Agent that fetches real macro data from yfinance and FRED,
    normalizes it using Z-scores, detects market regime,
    and calculates a Macro Score (0-100).
    """

    def __init__(self, fred_api_key=None):
        # Configuration
        self.window = 30  # Days for rolling Z-score
        self.history_period = "6mo" # To get enough data for Z-scores

        # API Symbols
        self.symbols = {
            "US10Y": "^TNX",
            "VIX": "^VIX",
            "DXY": "DX-Y.NYB", # Primary DXY ticker
            "HYG": "HYG",      # High Yield Corporate Bond
            "TLT": "TLT",      # 20+ Year Treasury Bond
            "SPX": "^GSPC"
        }
        
        # FRED Series IDs
        self.fred_series = {
            "M2": "M2SL",
            "CPI": "CPIAUCSL",
            "Unemployment": "UNRATE",
            "FedFunds": "FEDFUNDS"
        }

        # API Keys
        self.fred_api_key = fred_api_key or os.getenv('FRED_API_KEY') or "b609be7997d67f67cf3d1ac99609128b".strip()
        self.fred = None
        if self.fred_api_key:
            try:
                self.fred = Fred(api_key=self.fred_api_key)
            except Exception as e:
                print(f"Error initializing FRED API: {e}")

    def _fetch_yf_history(self, ticker):
        """Fetch historical data from yfinance."""
        try:
            data = yf.download(ticker, period=self.history_period, interval="1d", progress=False)
            if data.empty:
                return pd.Series(dtype=float)
            return data['Close']
        except Exception as e:
            print(f"Error fetching history for {ticker}: {e}")
            return pd.Series(dtype=float)

    def _fetch_fred_latest(self, series_id):
        """Fetch latest value from FRED."""
        if not self.fred:
            return None
        try:
            data = self.fred.get_series(series_id)
            if not data.empty:
                return data.iloc[-1], data.iloc[-2] # Current and previous
        except Exception as e:
            print(f"Error fetching FRED series {series_id}: {e}")
        return None, None

    def _calculate_z_score(self, series):
        """Calculate the latest Z-score of a series."""
        if len(series) < self.window:
            return 0.0
        
        # Ensure we are working with a 1D series
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]

        mean = series.rolling(window=self.window).mean()
        std = series.rolling(window=self.window).std()
        z_scores = (series - mean) / std
        
        latest_z = z_scores.iloc[-1]
        
        # Handle cases where latest_z is still a series or NaN
        if isinstance(latest_z, (pd.Series, pd.DataFrame)):
            latest_z = latest_z.iloc[0]
            
        if pd.isna(latest_z):
            return 0.0
            
        # Clip Z-score to [-3, 3]
        return float(max(-3.0, min(3.0, float(latest_z))))

    def _detect_regime(self, z_scores, macro_data):
        """
        Detect Market Regime based on Dynamic Correlation Framework.
        - Goldilocks: Low VIX, Normal Yield Curve, Low Inflation.
        - Stagflation: High Inflation (CPI), Rising/High Yields, Negative Yield Curve.
        - Recession: High VIX, Inverted Yield Curve, Falling yields.
        - Reflation: Rising Growth, Moderate Inflation.
        """
        # Heuristic Logic
        vix_z = z_scores.get('VIX', 0)
        dxy_z = z_scores.get('DXY', 0)
        yield_z = z_scores.get('US10Y', 0)
        
        cpi = macro_data.get('CPI', {}).get('value')
        unrate = macro_data.get('Unemployment', {}).get('value')
        
        if vix_z > 1.5:
            return "Recession/Panic"
        elif cpi and cpi > 4.0 and yield_z > 1.0:
            return "Stagflation"
        elif vix_z < -0.5 and yield_z < 0.5:
            return "Goldilocks"
        elif yield_z > 1.0 and dxy_z < 0:
            return "Reflation"
        else:
            return "Transition/Neutral"

    def _calculate_macro_score(self, z_scores):
        """Calculate a composite Macro Score (0-100)."""
        # 0 is extremely bearish, 100 is extremely bullish
        # VIX: high is bad
        # DXY: high is usually bad for risk
        # Yields: context dependent, but high volatility is usually bad
        
        weights = {
            'VIX': -30,
            'DXY': -20,
            'US10Y': -10,
            'HYG_TLT': 40 # Credit spread proxy
        }
        
        score = 50 # Baseline
        for key, z in z_scores.items():
            weight = weights.get(key, 0)
            # Map Z [-3, 3] to score impact
            impact = (z / 3) * weight
            score += impact
            
        return int(max(0, min(100, score)))

    def generate(self):
        """Main execution logic."""
        print("MacroAgent: Fetching real market data...")
        
        # 1. Fetch yfinance data
        hist_data = {}
        z_scores = {}
        raw_prices = {}
        
        for name, ticker in self.symbols.items():
            series = self._fetch_yf_history(ticker)
            if not series.empty:
                hist_data[name] = series
                z_scores[name] = self._calculate_z_score(series)
                # Take the last scalar value properly
                val = series.iloc[-1]
                if isinstance(val, (pd.Series, pd.DataFrame)):
                    val = val.iloc[0]
                raw_prices[name] = float(val)
        
        # Calculate Credit Spread Proxy (HYG / TLT)
        if 'HYG' in hist_data and 'TLT' in hist_data:
            ratio = hist_data['HYG'] / hist_data['TLT']
            z_scores['HYG_TLT'] = self._calculate_z_score(ratio)
            # Ensure scalar conversion
            val = ratio.iloc[-1]
            if isinstance(val, (pd.Series, pd.DataFrame)):
                val = val.iloc[0]
            raw_prices['CreditSpreadProxy'] = float(val)

        # 2. Fetch FRED data
        print("MacroAgent: Fetching FRED macro indicators...")
        macro_stats = {}
        for name, series_id in self.fred_series.items():
            curr, prev = self._fetch_fred_latest(series_id)
            if curr is not None:
                macro_stats[name] = {
                    "value": float(curr),
                    "previous": float(prev),
                    "change": float(curr - prev) if prev else 0
                }

        # 3. Analyze
        regime = self._detect_regime(z_scores, macro_stats)
        macro_score = self._calculate_macro_score(z_scores)
        
        # 4. Result
        result = {
            "timestamp": datetime.now().isoformat(),
            "macro_score": macro_score,
            "regime": regime,
            "z_scores": z_scores,
            "macro_stats": macro_stats,
            "raw_market_prices": raw_prices
        }
        return result

if __name__ == "__main__":
    # Test with provided key
    agent = MacroAgent()
    print("Running Macro Agent with Real Data...")
    report = agent.generate()
    import json
    print(json.dumps(report, indent=4, ensure_ascii=False))