import os
import requests
import pandas as pd

class TiingoClient:
    """
    عميل Tiingo لجلب بيانات الأسهم والعملات الرقمية بدقة عالية.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("TIINGO_API_KEY")
        self.base_url = "https://api.tiingo.com/tiingo"

    def get_stock_eod(self, ticker, start_date=None):
        """جلب بيانات نهاية اليوم للأسهم."""
        if not self.api_key:
            return None

        url = f"{self.base_url}/daily/{ticker}/prices"
        params = {"token": self.api_key}
        if start_date:
            params["startDate"] = start_date

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                # توحيد أسماء الأعمدة مع yfinance
                df.rename(columns={
                    'adjClose': 'Close',
                    'adjHigh': 'High',
                    'adjLow': 'Low',
                    'adjOpen': 'Open',
                    'adjVolume': 'Volume'
                }, inplace=True)
                return df
        except Exception as e:
            print(f"Tiingo Stock Error: {e}")
        return None

    def get_crypto_latest(self, ticker):
        """جلب بيانات العملات الرقمية اللحظية."""
        if not self.api_key:
            return None

        # Tiingo يستخدم تنسيقات مثل btcusd
        clean_ticker = ticker.replace("-", "").lower()
        url = f"https://api.tiingo.com/tiingo/crypto/top"
        params = {"tickers": clean_ticker, "token": self.api_key}

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        "ticker": ticker,
                        "price": data[0].get('topOfBookData', [{}])[0].get('lastPrice'),
                        "timestamp": data[0].get('topOfBookData', [{}])[0].get('lastSaleTimestamp'),
                        "source": "Tiingo Real-time"
                    }
        except Exception as e:
            print(f"Tiingo Crypto Error: {e}")
        return None
