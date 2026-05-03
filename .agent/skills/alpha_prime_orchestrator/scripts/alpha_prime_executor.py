import json
from datetime import datetime, timedelta
import os
import sys
import yfinance as yf
import pandas as pd
import time
import random
from amt_engine import AMTEngine
from regime_detector import RegimeDetector

# Import Macro Agent and Correlation Agent
from alpha_prime_macro import MacroAgent
from correlation_agent import CorrelationAgent

# Path for skills
SKILLS_PATH = r"c:\Users\Islam\Desktop\Trad\.agent\skills"
if SKILLS_PATH not in sys.path:
    sys.path.append(SKILLS_PATH)

# Skill Imports (Absolute imports now that folders use underscores)
try:
    from alphaear_news.scripts.news_tools import NewsNowTools
    from alphaear_news.scripts.database_manager import DatabaseManager as NewsDB
    from alphaear_sentiment.scripts.sentiment_tools import SentimentTools
    from alphaear_sentiment.scripts.database_manager import DatabaseManager as SentimentDB
except ImportError as e:
    print(f"Warning: Skill imports failed: {e}")
    NewsNowTools = NewsDB = SentimentTools = SentimentDB = None

class AlphaPrimeExecutor:
    """
    المنسق الشامل لوكيل Alpha Prime.
    """

    CROSS_ASSETS = {
        # أولاً: مؤشرات الأسهم (شهية المخاطرة)
        "SPX": "^GSPC",
        "NDX": "^NDX",
        "RUT": "^RUT",
        
        # ثانياً: أسواق الدخل الثابت (تكلفة الأموال)
        "US10Y": "^TNX",
        "US02Y": "^IRX",   
        "HY_SPREAD": "HYG",
        
        # ثالثاً: العملات (السيولة والتوترات)
        "DXY": "DX-Y.NYB",
        
        # رابعاً: السلع (التضخم والإنتاج)
        "GOLD": "GC=F",
        "COPPER": "HG=F",
        
        # خامساً: مقاييس التقلب (الخوف)
        "VIX": "^VIX",
        
        # سادساً: الأصول الرقمية (السيولة البديلة)
        "BTC": "BTC-USD",
        
        # إضافات للنسب الاستخباراتية (Intelligence Ratios)
        "XLY": "XLY", # Consumer Discretionary
        "XLP": "XLP", # Consumer Staples
        "TLT": "TLT", # 20+ Year Treasury Bond
        
        # سابعاً: الشحن واللوجستيات (Logistics - BDI Proxy)
        "BDRY": "BDRY" # Breakwave Dry Bulk Shipping ETF (BDI Proxy)
    }

    def __init__(self, target_asset: str, proxy: str = None):
        self.target_asset = target_asset
        self.proxy = proxy
        self.session = self._get_session()
        self.payload = {
            "timestamp": datetime.now().isoformat(),
            "target_asset": self.target_asset,
            "layer_1_technical": {},
            "intelligence_ratios": {}, 
            "correlation_context": {},
            "market_sentiment": {"score": 0, "label": "neutral", "catalysts": []}
        }
        # Initialize Skills
        self.news_db = None
        self.sent_db = None
        try:
            self.news_tools = NewsNowTools(self.news_db) if NewsDB and NewsNowTools else None
            self.sentiment_tools = SentimentTools(self.sent_db) if SentimentDB and SentimentTools else None
            
            # Individual Skill Initialization
            try:
                from alphaear_search.scripts.search_tools import SearchTools
                self.search_tools = SearchTools()
            except Exception as e:
                print(f"Warning: search_tools initialization failed: {e}")
                self.search_tools = None

            try:
                from alphaear_stock.scripts.stock_tools import StockTools
                self.stock_tools = StockTools(self.db) if hasattr(self, 'db') else StockTools(None) # Handle DB if needed
            except Exception as e:
                print(f"Warning: stock_tools initialization failed: {e}")
                self.stock_tools = None

            try:
                from alphaear_predictor.scripts.predictor_tools import PredictorTools
                self.predictor_tools = PredictorTools()
            except Exception as e:
                print(f"Warning: predictor_tools initialization failed: {e}")
                self.predictor_tools = None

            try:
                from alphaear_stock.scripts.analytics_tools import AnalyticsTools
                self.analytics_tools = AnalyticsTools()
            except Exception as e:
                print(f"Warning: analytics_tools initialization failed: {e}")
                self.analytics_tools = None

            try:
                from openbb_agent import OpenBBAgent
                self.openbb_agent = OpenBBAgent()
            except Exception as e:
                print(f"Warning: openbb_agent initialization failed: {e}")
                self.openbb_agent = None
                
        except Exception as e:
            print(f"Warning: Core skill initialization failed: {e}")
            self.analytics_tools = None
            
        # Quiver API Key
        self.quiver_key = os.getenv("QUIVER_API_KEY")

    def _get_session(self):
        """إعداد جلسة طلبات بمواصفات متصفح حقيقي"""
        session = yf.utils.get_tqdm().session if hasattr(yf.utils, 'get_tqdm') else None
        # Fallback to requests if yf session logic is not available
        import requests
        session = requests.Session()
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ]
        session.headers.update({"User-Agent": random.choice(user_agents)})
        
        if self.proxy:
            session.proxies = {"http": self.proxy, "https": self.proxy}
            
        return session

    def fetch_ohlcv_data(self, ticker: str, period="3mo", interval="1d"):
        """جلب البيانات مع استراتيجية تجنب الحظر"""
        try:
            # إضافة تأخير بسيط وعشوائي (0.5 إلى 2 ثانية) لتجنب كشف البوت
            time.sleep(random.uniform(0.5, 2.0))
            
            data = yf.download(
                ticker, 
                period=period, 
                interval=interval, 
                progress=False
            )
            if data.empty:
                return None
            return data
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def calculate_intelligence_ratios(self):
        print("Calculating Intelligence Ratios (Macro & Sentiment)...")
        ctx = self.payload["correlation_context"]
        ratios = {}

        try:
            # 1. منحنى العائد (Yield Curve)
            if "US10Y" in ctx and "US02Y" in ctx:
                us10y = ctx["US10Y"]["close"]
                us02y = ctx["US02Y"]["close"]
                spread = round(us10y - us02y, 4)
                ratios["yield_curve_spread"] = spread
                if spread < 0:
                    ratios["yield_curve_status"] = f"Inverted ({spread:.2f}) - ركود قادم"
                elif spread < 0.5:
                    ratios["yield_curve_status"] = f"Flat ({spread:.2f}) - ضغط سيولة"
                else:
                    ratios["yield_curve_status"] = f"Normal ({spread:.2f}) - نمو"
            
            # 2. النحاس إلى الذهب (Copper / Gold)
            if "COPPER" in ctx and "GOLD" in ctx:
                ratios["copper_gold_ratio"] = round(ctx["COPPER"]["close"] / ctx["GOLD"]["close"], 6)
            
            # 3. الفارق الائتماني (Credit Spread Proxy: HYG / TLT)
            if "HY_SPREAD" in ctx and "TLT" in ctx:
                ratios["credit_stress_ratio"] = round(ctx["HY_SPREAD"]["close"] / ctx["TLT"]["close"], 4)
            
            # 4. الكماليات مقابل الأساسيات (XLY / XLP)
            if "XLY" in ctx and "XLP" in ctx:
                ratios["consumer_strength_ratio"] = round(ctx["XLY"]["close"] / ctx["XLP"]["close"], 4)
            
            # 5. تركز السيولة (NDX / RUT)
            if "NDX" in ctx and "RUT" in ctx:
                ratios["liquidity_concentration_ratio"] = round(ctx["NDX"]["close"] / ctx["RUT"]["close"], 4)

            self.payload["intelligence_ratios"] = ratios
        except Exception as e:
            print(f"Error calculating ratios: {e}")

    def fetch_layer_1_technical(self):
        print("Fetching Layer 1: Technical & Correlation Data (Multi-Timeframe)...")
        asset_summary = {}
        for name, ticker in self.CROSS_ASSETS.items():
            df = self.fetch_ohlcv_data(ticker)
            if df is not None:
                # Ensure we handle pandas scalar/series properly
                close_val = df['Close'].iloc[-1]
                if isinstance(close_val, (pd.Series, pd.DataFrame)): close_val = close_val.iloc[0]
                
                asset_summary[name] = {
                    "close": round(float(close_val), 4),
                    "AMT_Temporal_Levels": AMTEngine.get_timeframe_levels(df)
                }
        
        self.payload["correlation_context"] = asset_summary
        self.calculate_intelligence_ratios()
        
        print("Running Regime Detection Engine...")
        regime_result = RegimeDetector.detect(self.payload["intelligence_ratios"], self.payload["correlation_context"])
        self.payload["market_regime"] = regime_result
        print(f"  → النظام: {regime_result['regime_name']} (ثقة: {regime_result['confidence']}%)")
        
        target_df = self.fetch_ohlcv_data(self.target_asset)
        if target_df is not None:
            close_val = target_df['Close'].iloc[-1]
            if isinstance(close_val, (pd.Series, pd.DataFrame)): close_val = close_val.iloc[0]
            
            self.payload["layer_1_technical"]["target_asset_data"] = {
                "close": round(float(close_val), 4)
            }
            temporal_levels = AMTEngine.get_timeframe_levels(target_df)
            self.payload["layer_1_technical"]["AMT_Temporal_Levels"] = temporal_levels
        else:
             self.payload["layer_1_technical"]["target_asset_data"] = "Failed to fetch"

    def fetch_layer_2_macro(self):
        print("Fetching Layer 2: Macro (Real Data & FRED)...")
        macro_agent = MacroAgent()
        self.payload["layer_2_macro"] = macro_agent.generate()

    def fetch_layer_3_correlation(self):
        print("Fetching Layer 3: Correlation (yfinance version)...")
        corr_agent = CorrelationAgent()
        self.payload["layer_3_correlation"] = corr_agent.generate()

    def fetch_layer_4_smart_money(self):
        print(f"Fetching Layer 4: Smart Money (Quiver API) for {self.target_asset}...")
        if not self.quiver_key:
            self.payload["layer_4_smart_money"] = "QUIVER_API_KEY missing. Smart Money data skipped."
            return

        import requests
        headers = {"Authorization": f"Bearer {self.quiver_key}", "Accept": "application/json"}
        base_url = "https://api.quiverquant.com/beta"
        
        # We strip suffixes for Quiver (e.g., NVDA instead of NVDA.MX)
        clean_ticker = self.target_asset.split('-')[0].split('=')[0].split('.')[0]
        
        smart_money_data = {}
        
        try:
            # 1. Congress Trading
            congress_url = f"{base_url}/live/congresstrading/{clean_ticker}"
            c_resp = requests.get(congress_url, headers=headers, timeout=10)
            if c_resp.status_code == 200:
                smart_money_data["congress_trades"] = c_resp.json()[:5] # Top 5 recent
            
            # 2. Insider Trading
            insider_url = f"{base_url}/live/insiders/{clean_ticker}"
            i_resp = requests.get(insider_url, headers=headers, timeout=10)
            if i_resp.status_code == 200:
                smart_money_data["insider_trades"] = i_resp.json()[:5]

            # 3. WallStreetBets Mentions (Sentiment Proxy)
            wsb_url = f"{base_url}/live/wsb/{clean_ticker}"
            w_resp = requests.get(wsb_url, headers=headers, timeout=10)
            if w_resp.status_code == 200:
                smart_money_data["retail_chatter"] = w_resp.json()[-1:] # Latest sentiment

            self.payload["layer_4_smart_money"] = smart_money_data
        except Exception as e:
            print(f"Error fetching Smart Money data: {e}")
            self.payload["layer_4_smart_money"] = "Error connecting to Quiver API"

    def fetch_layer_5_liquidity_sentiment(self):
        print("Fetching Layer 5: Liquidity & Sentiment (AlphaEar Sentiment)...")
        if self.sentiment_tools and "layer_8_catalysts" in self.payload:
            news_items = self.payload["layer_8_catalysts"]
            if isinstance(news_items, list) and len(news_items) > 0:
                titles = [item['title'] for item in news_items[:10]]
                results = self.sentiment_tools.analyze_sentiment_bert(titles)
                avg_score = sum(r['score'] for r in results) / len(results)
                self.payload["market_sentiment"]["score"] = round(avg_score, 3)
                self.payload["market_sentiment"]["label"] = "positive" if avg_score > 0.1 else ("negative" if avg_score < -0.1 else "neutral")
                self.payload["layer_5_liquidity"] = {"aggregate_score": avg_score, "sentiment_label": self.payload["market_sentiment"]["label"]}
        else:
            self.payload["layer_5_liquidity"] = "Sentiment tools or news not available"

    def fetch_layer_7_logistics(self):
        print("Fetching Layer 7: Logistics (BDRY/BDI Proxy)...")
        if "BDRY" in self.payload["correlation_context"]:
            bdry_data = self.payload["correlation_context"]["BDRY"]
            self.payload["layer_7_logistics"] = {
                "bdi_proxy_ticker": "BDRY",
                "current_price": bdry_data["close"],
                "status": "Healthy" if bdry_data["close"] > 10 else "Low Activity"
            }
        else:
            self.payload["layer_7_logistics"] = "BDI Proxy data missing"

    def fetch_layer_8_catalysts(self):
        print("Fetching Layer 8: Catalysts (AlphaEar News)...")
        if self.news_tools:
            try:
                news_cls = self.news_tools.fetch_hot_news("cls", count=5)
                news_ws = self.news_tools.fetch_hot_news("wallstreetcn", count=5)
                all_news = (news_cls or []) + (news_ws or [])
                self.payload["layer_8_catalysts"] = all_news
                self.payload["market_sentiment"]["catalysts"] = [n['title'] for n in all_news]
            except Exception as e:
                print(f"Error fetching catalysts: {e}")
        else:
            self.payload["layer_8_catalysts"] = []

    def fetch_layer_9_deep_insights(self):
        print(f"Fetching Layer 9: DeepEar Lite Insights...")
        if self.search_tools:
            try:
                # We use search to simulate deep insights if direct module not exposed
                self.payload["layer_9_deep_insights"] = self.search_tools.search(f"Detailed financial transmission chain for {self.target_asset}")
            except:
                self.payload["layer_9_deep_insights"] = "N/A"

    def fetch_layer_10_predictions(self):
        print(f"Fetching Layer 10: Market Prediction...")
        if self.predictor_tools:
            try:
                self.payload["layer_10_predictions"] = self.predictor_tools.predict_market(self.target_asset)
            except:
                self.payload["layer_10_predictions"] = "N/A"

    def fetch_layer_11_web_context(self):
        print(f"Fetching Layer 11: Web Context (Search)...")
        if self.search_tools:
            try:
                self.payload["layer_11_web_context"] = self.search_tools.search(f"Latest macro events affecting {self.target_asset} today")
            except:
                self.payload["layer_11_web_context"] = "N/A"

    def fetch_layer_12_signal_evolution(self):
        print(f"Fetching Layer 12: Signal Evolution Tracking...")
        # Tracking how signals change over time
        self.payload["layer_12_signal_evolution"] = {
            "status": "active",
            "historical_context": "Integrated with Signal Tracker skill"
        }

    def fetch_layer_13_institutional(self):
        print(f"Fetching Layer 13: Institutional & Dark Pool Intel (OpenBB)...")
        if self.openbb_agent:
            self.payload["layer_13_institutional"] = self.openbb_agent.generate(self.target_asset)
        else:
            self.payload["layer_13_institutional"] = "OpenBB Agent not initialized"

    def fetch_layer_14_toolkit_analytics(self):
        print(f"Fetching Layer 14: Advanced Analytics (FinanceToolkit) for {self.target_asset}...")
        if self.analytics_tools:
            # Clean ticker for US stocks
            clean_ticker = self.target_asset.split('-')[0].split('=')[0].split('.')[0]
            try:
                self.payload["layer_14_toolkit_analytics"] = self.analytics_tools.get_full_analysis(clean_ticker)
            except Exception as e:
                self.payload["layer_14_toolkit_analytics"] = f"Error: {e}"
        else:
            self.payload["layer_14_toolkit_analytics"] = "Analytics Tools not initialized"

    def generate_context_json(self) -> str:
        # Step-by-step layer ingestion
        self.fetch_layer_1_technical() # Includes Regime Detection
        self.fetch_layer_2_macro()
        self.fetch_layer_3_correlation()
        self.fetch_layer_4_smart_money()
        self.fetch_layer_5_liquidity_sentiment()
        self.fetch_layer_7_logistics()
        self.fetch_layer_8_catalysts()
        
        # New Integrated Layers
        self.fetch_layer_9_deep_insights()
        self.fetch_layer_10_predictions()
        self.fetch_layer_11_web_context()
        self.fetch_layer_12_signal_evolution()
        self.fetch_layer_13_institutional()
        self.fetch_layer_14_toolkit_analytics()
        
        self.payload["layer_6_alt_data"] = "Integrated via Smart Money/Logistics/OpenBB/FinanceToolkit"

        return json.dumps(self.payload, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    executor = AlphaPrimeExecutor(target)
    context_json = executor.generate_context_json()
    temp_file = os.path.join(os.path.dirname(__file__), "alpha_prime_context.json")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(context_json)
    print(f"\n✅ Intelligence context generated for {target}\n📄 File: {temp_file}")
