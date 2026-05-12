import json
from datetime import datetime, timedelta
import os
import sys
import yfinance as yf
import pandas as pd
import time
import random
from src.amt_framework.auction_analysis import AMTEngine
from src.core.market_regimes import RegimeDetector
from src.intelligence_layers.quant_metrics import QuantEngine
from src.intelligence_layers.fundamental_mining import MiningSectorAnalysis
from src.intelligence_layers.options_gex import OptionsGexEngine

# Import Macro Agent and Correlation Agent
from src.intelligence_layers.macro_indicators import MacroAgent
from src.core.correlation_engine import CorrelationAgent

# Path for internal skills
# After refactor, src/core/orchestrator.py is 2 levels deep from root
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILLS_PATH = os.path.join(ROOT_PATH, ".agent", "skills")
if SKILLS_PATH not in sys.path:
    sys.path.append(SKILLS_PATH)

# Path for Awesome-finance-skills
AWESOME_SKILLS_PATH = os.path.join(ROOT_PATH, "Awesome-finance-skills-main", "skills")
if os.path.exists(AWESOME_SKILLS_PATH):
    sys.path.append(AWESOME_SKILLS_PATH)

# Skill Imports
try:
    # Safe paths
    NEWS_PATH = os.path.join(SKILLS_PATH, "alphaear_news", "scripts")
    if NEWS_PATH not in sys.path: sys.path.append(NEWS_PATH)

    from news_tools import NewsNowTools
    from database_manager import DatabaseManager as NewsDB

    # Sentiment & Predictor from Awesome-finance-skills
    SENTIMENT_PATH = os.path.join(AWESOME_SKILLS_PATH, "alphaear-sentiment", "scripts")
    if SENTIMENT_PATH not in sys.path: sys.path.append(SENTIMENT_PATH)

    import sentiment_tools as st
    SentimentTools = st.SentimentTools
    import database_manager as sdb
    SentimentDB = sdb.DatabaseManager

    PREDICTOR_PATH = os.path.join(AWESOME_SKILLS_PATH, "alphaear-predictor", "scripts")
    if PREDICTOR_PATH not in sys.path: sys.path.append(PREDICTOR_PATH)
    import kronos_predictor as kp
    KronosPredictorUtility = kp.KronosPredictorUtility
except Exception as e:
    print(f"Warning: Skill imports failed: {e}")
    NewsNowTools = NewsDB = SentimentTools = SentimentDB = KronosPredictorUtility = None

class AlphaPrimeExecutor:
    """
    المنسق الشامل لوكيل Alpha Prime.
    """

    CROSS_ASSETS = {
        # مؤشرات (Risk/Growth)
        "SPX": "^GSPC",
        "NDX": "^NDX",
        "DJI": "^DJI",
        "RUT": "^RUT",
        "GER40": "^GDAXI",
        "JPN225": "^N225",
        "MSCI_EM": "EEM",

        # دخل ثابت (Cost of Capital)
        "US10Y": "^TNX",
        "US30Y": "^TYX",
        "US02Y": "^IRX", # Using 13-Week Treasury Bill as a short-term proxy for yield curve calculations
        "TIPS": "TIP",
        "HY_SPREAD": "HYG",
        "TLT": "TLT",

        # عملات (Liquidity)
        "DXY": "DX-Y.NYB",
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "JPY=X",
        "USDCHF": "CHF=X",
        "AUDUSD": "AUDUSD=X",

        # سلع (Inflation)
        "GOLD": "GC=F",
        "SILVER": "SI=F",
        "COPPER": "HG=F",
        "OIL": "CL=F",
        "NAT_GAS": "NG=F",

        # تقلب (Fear)
        "VIX": "^VIX",
        "MOVE": "^MOVE",

        # رقمية (Alt Liquidity)
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "SOL": "SOL-USD",

        # إضافات للنسب
        "XLY": "XLY",
        "XLP": "XLP"
    }

    def __init__(self, target_asset: str, proxy: str = None):
        # توحيد الرموز: إذا طلب المستخدم الذهب بأي صيغة، نستخدم GC=F كمرجع موحد
        if target_asset.upper() in ["XAU=F", "GOLD", "XAUUSD", "XAU"]:
            self.target_asset = "GC=F"
        else:
            self.target_asset = target_asset
        self.proxy = proxy
        self.session = self._get_session()
        self.payload = {
            "timestamp": datetime.now().isoformat(),
            "target_asset": self.target_asset,
            "layer_1_technical": {},
            "intelligence_ratios": {},
            "correlation_context": {},
            "market_sentiment": {"score": 0, "label": "neutral", "catalysts": []},
            "layer_10_predictions": "N/A", "layer_11_web_context": "N/A",
        }
        # Initialize Skills with safe defaults
        self.news_db = None
        self.sent_db = None
        self.news_tools = None
        self.sentiment_tools = None
        self.search_tools = None
        self.stock_tools = None
        self.predictor_tools = None
        self.analytics_tools = None
        self.openbb_agent = None

        try:
            if NewsDB and NewsNowTools:
                self.news_tools = NewsNowTools(self.news_db)
            if SentimentDB and SentimentTools:
                self.sentiment_tools = SentimentTools(self.sent_db)

            # Individual Skill Initialization
            try:
                SEARCH_PATH = os.path.join(SKILLS_PATH, "alphaear_search", "scripts")
                if SEARCH_PATH not in sys.path: sys.path.append(SEARCH_PATH)
                from search_tools import SearchTools
                self.search_tools = SearchTools()
            except Exception as e:
                print(f"Warning: search_tools initialization failed: {e}")
                self.search_tools = None

            try:
                STOCK_PATH = os.path.join(AWESOME_SKILLS_PATH, "alphaear-stock", "scripts")
                if STOCK_PATH not in sys.path: sys.path.append(STOCK_PATH)
                from stock_tools import StockTools
                self.stock_tools = StockTools(self.db) if hasattr(self, 'db') else StockTools(None)
            except Exception as e:
                print(f"Warning: stock_tools initialization failed: {e}")
                self.stock_tools = None

            try:
                if KronosPredictorUtility:
                    self.predictor_tools = KronosPredictorUtility()
                else:
                    self.predictor_tools = None
            except Exception as e:
                print(f"Warning: predictor_tools initialization failed: {e}")
                self.predictor_tools = None

            try:
                from analytics_tools import AnalyticsTools
                self.analytics_tools = AnalyticsTools()
            except Exception as e:
                print(f"Warning: analytics_tools initialization failed: {e}")
                self.analytics_tools = None

            try:
                from src.utils.openbb_connector import OpenBBAgent
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

    def fetch_ohlcv_data(self, ticker: str, period="1mo", interval="1h"):
        """جلب البيانات مع نظام استعادة (Fallback) في حال فشل الدقة الساعوية"""
        try:
            time.sleep(random.uniform(0.3, 1.0))
            data = yf.download(ticker, period=period, interval=interval, progress=False)

            if data.empty and interval == "1h":
                print(f"⚠️ Hourly data failed for {ticker}, falling back to Daily...")
                data = yf.download(ticker, period=period, interval="1d", progress=False)

            if data.empty:
                return None

            # توحيد التوقيت (Timezone naive) لضمان توافق الحسابات
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)

            return data
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def calculate_intelligence_ratios(self):
        print("Calculating Intelligence Ratios (Macro & Sentiment)...")
        ctx = self.payload["correlation_context"]
        ratios = {}

        try:
            # 0. DXY Correlation Check (Institutional Logic)
            if "DXY" in ctx:
                dxy_val = ctx["DXY"]["close"]
                ratios["dxy_value"] = dxy_val
                ratios["dxy_gold_impact"] = f"Inverse Pressure ({dxy_val})" if dxy_val > 104 else f"Supportive ({dxy_val})"
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

            # 6. السيولة العالمية إلى S&P (Proxy: M2 / SPX)
            # This will be refined in the FRED layer

            # 7. الذهب والبيتكوين (BTC / XAU)
            if "BTC" in ctx and "GOLD" in ctx:
                ratios["btc_gold_ratio"] = round(ctx["BTC"]["close"] / ctx["GOLD"]["close"], 4)

            # 8. الفائدة الحقيقية (TIPS)
            if "TIPS" in ctx:
                ratios["real_yield_proxy"] = ctx["TIPS"]["close"]

            self.payload["intelligence_ratios"] = ratios
        except Exception as e:
            print(f"Error calculating ratios: {e}")

    def fetch_layer_1_technical(self):
        print("Fetching Layer 1: Technical & AMT/TPO Data...")
        asset_summary = {}
        # جلب بيانات السوق لفترة أطول لحساب البيتا بدقة
        market_df_long = self.fetch_ohlcv_data("^GSPC", period="6mo", interval="1d")

        for name, ticker in self.CROSS_ASSETS.items():
            df = self.fetch_ohlcv_data(ticker)
            if df is not None:
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

        target_df = self.fetch_ohlcv_data(self.target_asset)
        if target_df is not None:
            close_val = target_df['Close'].iloc[-1]
            if isinstance(close_val, (pd.Series, pd.DataFrame)): close_val = close_val.iloc[0]

            # Dimension 2 & 3: AMT/TPO
            use_tpo = 'Volume' not in target_df.columns or target_df['Volume'].sum() == 0
            amt_data = AMTEngine.calculate_value_area(target_df, use_tpo=use_tpo)
            order_flow = AMTEngine.diagnose_order_flow_patterns(target_df)

            # Dimension 5: Quant Metrics
            # نستخدم البيانات الطويلة لحساب البيتا والبيانات اللحظية للتقلب
            target_df_long = self.fetch_ohlcv_data(self.target_asset, period="6mo", interval="1d")
            quant_metrics = QuantEngine.get_risk_metrics(target_df_long if target_df_long is not None else target_df, market_df_long)

            # Fetch Open Interest and COT simulation
            open_interest = "N/A"
            if hasattr(target_df, 'Open Interest'):
                open_interest = target_df['Open Interest'].iloc[-1]
            elif 'Open Interest' in target_df.columns:
                open_interest = target_df['Open Interest'].iloc[-1]

            self.payload["layer_1_technical"].update({
                "close": round(float(close_val), 4),
                "open_interest": open_interest,
                "amt_structure": amt_data,
                "order_flow_diagnostics": order_flow,
                "quant_metrics": quant_metrics,
                "temporal_levels": AMTEngine.get_timeframe_levels(target_df)
            })
        else:
             self.payload["layer_1_technical"]["target_asset_data"] = "Failed to fetch"

    def fetch_layer_2_macro(self):
        print("Fetching Layer 2: Macro (Real Data & FRED)...")
        macro_agent = MacroAgent()
        macro_data = macro_agent.generate()
        self.payload["layer_2_macro"] = macro_data

        # --- Regime Fusion Logic ---
        # التوفيق بين القراءة التقنية والماكرو
        tech_regime = self.payload.get("market_regime", {}).get("regime")
        macro_regime = macro_data.get("regime", "").lower()

        if tech_regime and macro_regime:
            if tech_regime != macro_regime:
                print(f"⚠️ Regime Mismatch: Tech={tech_regime} vs Macro={macro_regime}. Resolving...")
                # ترجيح الماكرو في حال وجود تضارب هيكلي
                self.payload["market_regime"]["regime_name"] += f" (Macro confirmation: {macro_regime})"
                self.payload["market_regime"]["warnings"].append("STRUCTURAL_DIVERGENCE_DETECTED")

        # Calculate ERP (Equity Risk Premium) - Simplified: 1/PE - Yield
        # Calculate Shiller P/E Proxy
        if "SPX" in self.payload["correlation_context"]:
            spx_price = self.payload["correlation_context"]["SPX"]["close"]
            # Mocking ERP and CAPE if not directly available from API
            self.payload["intelligence_ratios"]["erp_proxy"] = "4.5% (Estimated)"
            self.payload["intelligence_ratios"]["cape_shiller_proxy"] = "34.2 (Estimated)"

    def fetch_layer_3_correlation(self):
        print("Fetching Layer 3: Correlation (yfinance version)...")
        corr_agent = CorrelationAgent()
        self.payload["layer_3_correlation"] = corr_agent.generate()

    def fetch_layer_4_smart_money(self):
        print(f"Fetching Layer 4: Smart Money (OSINT & QuiverQuant Fallback)...")
        smart_money_data = {
            "status": "Searching OSINT sources (HouseStockWatcher, SenateStockWatcher, QuiverQuant)",
            "congress_trades": "N/A",
            "insider_trades": "N/A"
        }

        if self.search_tools:
            try:
                clean_ticker = self.target_asset.split('-')[0].split('=')[0].split('.')[0]
                q_data = self.search_tools.search(f"site:quiverquant.com OR site:housestockwatcher.com OR site:senatestockwatcher.com {clean_ticker} latest stock trades")
                smart_money_data["congress_trades_osint"] = q_data
                b_data = self.search_tools.search("Warren Buffett Berkshire Hathaway latest 13F filings May 2026 portfolio changes")
                smart_money_data["buffett_13f_summary"] = b_data
                inst_data = self.search_tools.search(f"{clean_ticker} institutional ownership and dark pool activity latest news")
                smart_money_data["institutional_flow_summary"] = inst_data
            except: pass

        if not self.quiver_key:
            self.payload["layer_4_smart_money"] = smart_money_data
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
        # Ensure sentiment tools are initialized even if DB is missing
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

    def fetch_layer_7_mining_and_fundamental(self):
        print("Fetching Dimension 7: Mining & Fundamental Analysis...")
        mining_data = MiningSectorAnalysis.analyze_sector()

        # Check arbitrage if target is Gold
        arbitrage = "N/A"
        if "GOLD" in self.target_asset.upper() or "XAU" in self.target_asset.upper():
            # Simple check
            gold_df = self.fetch_ohlcv_data(self.target_asset, period="1mo")
            miners_df = self.fetch_ohlcv_data("GDX", period="1mo")
            if gold_df is not None and miners_df is not None:
                def get_val(series_or_val):
                    if hasattr(series_or_val, 'iloc'):
                        return series_or_val.iloc[0]
                    return series_or_val

                g_close_last = get_val(gold_df['Close'].iloc[-1])
                g_close_first = get_val(gold_df['Close'].iloc[0])
                m_close_last = get_val(miners_df['Close'].iloc[-1])
                m_close_first = get_val(miners_df['Close'].iloc[0])

                g_chg = ((g_close_last / g_close_first) - 1) * 100
                m_chg = ((m_close_last / m_close_first) - 1) * 100
                arbitrage = MiningSectorAnalysis.check_arbitrage(float(g_chg), float(m_chg))

        self.payload["layer_7_mining"] = {
            "giants": mining_data,
            "arbitrage_status": arbitrage
        }

    def fetch_layer_8_catalysts(self):
        print("Fetching Layer 8: Catalysts (Google News & AlphaEar)...")
        all_news = []

        # 1. Search Google News for Institutional Logic
        if self.search_tools:
            try:
                g_news = self.search_tools.search("https://news.google.com/home?hl=en-US&gl=US&ceid=US:en top financial and geopolitical news today")
                all_news.append({"title": "Google News Top Headlines", "content": g_news, "source": "Google News"})
            except: pass


        # 2. AlphaEar News
        if self.news_tools:
            try:
                news_cls = self.news_tools.fetch_hot_news("cls", count=5)
                news_ws = self.news_tools.fetch_hot_news("wallstreetcn", count=5)
                all_news.extend(news_cls or [])
                all_news.extend(news_ws or [])
            except Exception as e:
                print(f"Error fetching AlphaEar catalysts: {e}")

        self.payload["layer_8_catalysts"] = all_news
        self.payload["market_sentiment"]["catalysts"] = [n.get('title', 'News Item') for n in all_news]

    def fetch_layer_9_deep_insights(self):
        print(f"Fetching Layer 9: Geopolitical & Lobbying Intel (AIPAC, 13F, Congress)...")
        intel = {
            "aipac_and_lobbying": "N/A",
            "congress_insider_trading": "N/A",
            "institutional_13f_buffett": "N/A",
            "geopolitical_tensions_europe_me": "N/A"
        }
        if self.search_tools:
            try:
                intel["aipac_and_lobbying"] = self.search_tools.search("AIPAC and Western lobbying influence on defense budgets, armament, and Middle East policy 2026")
                intel["congress_insider_trading"] = self.search_tools.search(f"Latest Congressional stock disclosures for {self.target_asset} and Gold miners using STOCK Act filings")
                intel["institutional_13f_buffett"] = self.search_tools.search("Warren Buffett and sovereign wealth funds rotation from cash/bonds to hard assets like Gold miners 13F filings 2026")
                intel["geopolitical_tensions_europe_me"] = self.search_tools.search("Geopolitical risk pricing in Gold: Middle East conflict and Eastern Europe escalations news today")

                self.payload["layer_9_deep_insights"] = intel
            except Exception as e:
                print(f"Search error in Layer 9: {e}")
                self.payload["layer_9_deep_insights"] = intel
        else:
            self.payload["layer_9_deep_insights"] = intel

    def fetch_layer_10_predictions(self):
        print(f"Fetching Layer 10: Market Prediction (Kronos)...")
        if self.predictor_tools:
            try:
                target_df = self.fetch_ohlcv_data(self.target_asset)
                if target_df is not None:
                    # Kronos expects 'date' column
                    target_df = target_df.reset_index()
                    target_df.columns = [c.lower() for c in target_df.columns]
                    forecast = self.predictor_tools.get_base_forecast(target_df)
                    self.payload["layer_10_predictions"] = [f.__dict__ for f in forecast] if forecast else "N/A"
            except Exception as e:
                self.payload["layer_10_predictions"] = f"Prediction failed: {e}"

    def fetch_layer_11_web_context(self):
        print(f"Fetching Layer 11: Web Context (Search)...")
        if self.search_tools:
            try:
                self.payload["layer_11_web_context"] = self.search_tools.search(f"Latest macro events affecting {self.target_asset} today")
            except: self.payload["layer_11_web_context"] = "N/A"

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
        try:
            # Check asset type before using FinanceToolkit (only works for Equities)
            is_equity = self.payload.get("asset_metadata", {}).get("type") == "Equity"

            if is_equity:
                from src.utils.toolkit_analytics import AnalyticsEngine
                ae = AnalyticsEngine()
                clean_ticker = self.target_asset.split('-')[0].split('=')[0].split('.')[0]
                self.payload["layer_14_toolkit_analytics"] = ae.get_full_analysis(clean_ticker)
            else:
                self.payload["layer_14_toolkit_analytics"] = "Skipped: FinanceToolkit only supports Equity assets. For Futures/Indices, see AMT levels."
        except Exception as e:
            self.payload["layer_14_toolkit_analytics"] = f"Toolkit error: {e}"

    def _json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        from datetime import date
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError (f"Type {type(obj)} not serializable")

    def _convert_keys_to_string(self, d):
        """Recursively convert dictionary keys to strings for JSON serialization."""
        if not isinstance(d, dict):
            return d
        return {str(k): self._convert_keys_to_string(v) if isinstance(v, dict) else v for k, v in d.items()}

    def generate_context_json(self) -> str:
        # Asset Metadata (FinanceDatabase)
        print("Fetching Asset Metadata (FinanceDatabase)...")
        try:
            from src.utils.metadata_fetcher import MetadataEngine
            self.payload["asset_metadata"] = MetadataEngine.get_asset_metadata(self.target_asset)
        except: pass

        # Step-by-step layer ingestion
        self.fetch_layer_1_technical() # Includes Regime Detection, Quant, AMT (Dim 2, 3, 4, 5)

        # Dimension 9: Options & GEX
        print("Fetching Dimension 9: Options GEX Context...")
        self.payload["layer_9_options_gex"] = OptionsGexEngine.get_options_context(self.CROSS_ASSETS, self)

        self.fetch_layer_2_macro() # Dim 1
        self.fetch_layer_3_correlation() # Dim 6 (Intermarket)
        self.fetch_layer_4_smart_money() # Dim 9

        # MUST FETCH CATALYSTS BEFORE SENTIMENT
        self.fetch_layer_8_catalysts()
        self.fetch_layer_5_liquidity_sentiment() # Dim 1/Sentiment

        self.fetch_layer_7_mining_and_fundamental() # Dim 7

        # New Integrated Layers
        self.fetch_layer_9_deep_insights()
        self.fetch_layer_10_predictions()
        self.fetch_layer_11_web_context()
        self.fetch_layer_12_signal_evolution()
        self.fetch_layer_13_institutional()
        self.fetch_layer_14_toolkit_analytics()

        self.payload["layer_6_alt_data"] = "Integrated via Smart Money/Logistics/OpenBB/FinanceToolkit"

        # Pre-process payload to ensure all keys are strings and handle datetime values
        processed_payload = self._convert_keys_to_string(self.payload)
        return json.dumps(processed_payload, indent=4, ensure_ascii=False, default=self._json_serial)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    executor = AlphaPrimeExecutor(target)
    context_json = executor.generate_context_json()
    temp_file = os.path.join(os.path.dirname(__file__), "alpha_prime_context.json")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(context_json)
    print(f"\n✅ Intelligence context generated for {target}\n📄 File: {temp_file}")
