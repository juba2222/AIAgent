import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.stattools import grangercausalitytests

# CCXT for exchange data
import ccxt

# Transfer Entropy from pyinform (if installed)
try:
    from pyinform.transferentropy import transfer_entropy
except Exception:
    transfer_entropy = None  # Fallback if not available

class CorrelationAgent:
    """Correlation Agent for high‑frequency market analysis.

    Responsibilities:
    1️⃣ Fetch minute‑level OHLCV data via CCXT for selected assets.
    2️⃣ Compute rolling Pearson correlation matrix (default 120‑minute window).
    3️⃣ Detect lead‑lag relationships using Granger Causality (max lag 5).
    4️⃣ Optionally calculate Transfer Entropy for non‑linear directionality.
    5️⃣ Emit a structured payload for the Orchestrator.
    """

    def __init__(self):
        # Initialise CCXT exchange (Binance as default). Keys are optional for public data.
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        # Mapping of logical asset names to exchange symbols
        self.symbols = {
            "BTC": "BTC/USDT",
            "ETH": "ETH/USDT",
            "SOL": "SOL/USDT",
            "NASDAQ": "NASDAQ",          # placeholder – will be fetched via yfinance later
            "GOLD": "XAU/USD",
            "DXY": "DXY"                # placeholder – via yfinance
        }
        # Settings
        self.correlation_window = 120  # minutes for rolling correlation
        self.granger_maxlag = 5

    # ---------------------------------------------------------------------
    # Helper: fetch minute‑level OHLCV from CCXT and return a pandas Series of closes
    # ---------------------------------------------------------------------
    def _fetch_ccxt_series(self, symbol, timeframe='1m', limit=500):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            # Convert ms timestamp to datetime index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df['close']
        except Exception as e:
            print(f"Error fetching {symbol} from CCXT: {e}")
            return pd.Series(dtype=float)

    # ---------------------------------------------------------------------
    # Helper: fetch price series for assets not on CCXT (e.g., Nasdaq, DXY, Gold)
    # ---------------------------------------------------------------------
    def _fetch_yf_series(self, ticker, period='2d', interval='1m'):
        import yfinance as yf
        try:
            data = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
            if data.empty:
                return pd.Series(dtype=float)
            return data['Close']
        except Exception as e:
            print(f"Error fetching {ticker} from Yahoo Finance: {e}")
            return pd.Series(dtype=float)

    # ---------------------------------------------------------------------
    # Core: build a DataFrame of aligned price series for key assets
    # ---------------------------------------------------------------------
    def _build_price_dataframe(self):
        price_series = {}
        # CCXT assets
        for name in ["BTC", "ETH", "SOL"]:
            price_series[name] = self._fetch_ccxt_series(self.symbols[name])
        # Non‑CCXT assets via yfinance (NASDAQ index, Gold, DXY)
        price_series["NASDAQ"] = self._fetch_yf_series('^IXIC')
        price_series["GOLD"] = self._fetch_yf_series('GC=F')
        price_series["DXY"] = self._fetch_yf_series('DX-Y.NYB')
        # Align all series on the same index (inner join)
        df = pd.concat(price_series, axis=1, join='inner')
        df.dropna(inplace=True)
        return df

    # ---------------------------------------------------------------------
    # Rolling Pearson correlation over the configured window (in minutes)
    # ---------------------------------------------------------------------
    def _rolling_correlation(self, df):
        # Resample to minute frequency if needed (already minute)
        corr_matrix = {}
        window = self.correlation_window
        # Use rolling apply for each pair
        for col_a in df.columns:
            for col_b in df.columns:
                if col_a >= col_b:
                    continue
                series_a = df[col_a]
                series_b = df[col_b]
                # Rolling correlation returns a series; take the latest value
                rolling_corr = series_a.rolling(window).corr(series_b)
                latest_corr = rolling_corr.iloc[-1]
                corr_matrix[f"{col_a}_{col_b}"] = float(latest_corr) if pd.notna(latest_corr) else None
        return corr_matrix

    # ---------------------------------------------------------------------
    # Granger causality detection (returns p‑value for the hypothesis that A causes B)
    # ---------------------------------------------------------------------
    def _granger_causality(self, series_a, series_b):
        try:
            data = pd.concat([series_a, series_b], axis=1).dropna()
            data.columns = ['a', 'b']
            # Test if a Granger‑causes b
            test_result = grangercausalitytests(data[['b', 'a']], maxlag=self.granger_maxlag, verbose=False)
            # Use the smallest p‑value across lags
            pvals = [test_result[lag][0]['ssr_ftest'][1] for lag in range(1, self.granger_maxlag + 1)]
            return min(pvals)
        except Exception as e:
            print(f"Granger test error: {e}")
            return None

    # ---------------------------------------------------------------------
    # Transfer Entropy (non‑linear directionality) – optional fallback
    # ---------------------------------------------------------------------
    def _transfer_entropy(self, series_a, series_b, k=1):
        if transfer_entropy is None:
            return None
        try:
            # Discretize to a small number of bins for entropy calculation
            bins = 5
            a_disc = pd.cut(series_a, bins=bins, labels=False).astype(int)
            b_disc = pd.cut(series_b, bins=bins, labels=False).astype(int)
            return float(transfer_entropy(a_disc.tolist(), b_disc.tolist(), k=k))
        except Exception as e:
            print(f"Transfer entropy error: {e}")
            return None

    # ---------------------------------------------------------------------
    # Public method to generate the full correlation payload
    # ---------------------------------------------------------------------
    def generate(self):
        # 1️⃣ Build aligned price DataFrame
        price_df = self._build_price_dataframe()
        if price_df.empty:
            return {"error": "Insufficient data to compute correlations."}

        # 2️⃣ Rolling correlation matrix (latest values)
        corr_matrix = self._rolling_correlation(price_df)

        # 3️⃣ Lead‑lag detection (Granger + optional Transfer Entropy)
        lead_lag_info = {}
        assets = list(price_df.columns)
        for i, asset_a in enumerate(assets):
            for asset_b in assets[i+1:]:
                p_val = self._granger_causality(price_df[asset_a], price_df[asset_b])
                # Simple heuristic: p < 0.05 => A leads B
                if p_val is not None and p_val < 0.05:
                    lead_lag_info[f"{asset_a}_leads_{asset_b}"] = True
                else:
                    lead_lag_info[f"{asset_a}_leads_{asset_b}"] = False
                # Transfer Entropy (if library available)
                if transfer_entropy:
                    te = self._transfer_entropy(price_df[asset_a], price_df[asset_b])
                    lead_lag_info[f"te_{asset_a}_to_{asset_b}"] = te

        # 4️⃣ Decoupling alerts – compare current correlation to historical baseline
        # For simplicity, compute baseline as mean correlation over the past 24h (1440 minutes)
        baseline_corr = {}
        for col in corr_matrix:
            series_a, series_b = col.split('_')
            rolling_series = price_df[series_a].rolling(self.correlation_window).corr(price_df[series_b])
            baseline = rolling_series.mean()
            baseline_corr[col] = float(baseline) if pd.notna(baseline) else None

        decoupling_alerts = {}
        for pair, curr_corr in corr_matrix.items():
            base = baseline_corr.get(pair)
            if base is None or curr_corr is None:
                continue
            # If correlation magnitude changes sign or drops > 0.5 absolute diff, raise alert
            if (curr_corr * base) < 0 or abs(curr_corr - base) > 0.5:
                decoupling_alerts[pair] = {
                    "current": curr_corr,
                    "baseline": base,
                    "alert": "Decoupling detected"
                }

        # 5️⃣ Assemble payload
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "correlation_matrix": corr_matrix,
            "lead_lag": lead_lag_info,
            "decoupling_alerts": decoupling_alerts,
            "price_snapshot": price_df.iloc[-1].to_dict()
        }
        return payload

# ---------------------------------------------------------------------
# Simple sanity‑check when run as script
# ---------------------------------------------------------------------
if __name__ == "__main__":
    agent = CorrelationAgent()
    result = agent.generate()
    print(result)