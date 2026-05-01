import json
from datetime import datetime, timedelta
import os
import sys
import yfinance as yf
import pandas as pd
from amt_engine import AMTEngine
from regime_detector import RegimeDetector

# Import Macro Agent and Correlation Agent
from alpha_prime_macro import MacroAgent
from correlation_agent import CorrelationAgent

# Path for skills
SKILLS_PATH = r"c:\Users\Islam\Desktop\Trad\.agent\skills"
sys.path.append(SKILLS_PATH)

class AlphaPrimeExecutor:
    """
    المنسق الشامل لوكيل Alpha Prime.
    يقوم أولاً بجلب OHLCV لـ 6 أصول ومؤشرات لقياس الارتباط والانحراف السعري.
    ثم يجلب بقية البيانات لتكوين سياق متكامل للوكيل.
    """

    CROSS_ASSETS = {
        # أولاً: مؤشرات الأسهم (شهية المخاطرة)
        "SPX": "^GSPC",
        "NDX": "^NDX",
        "RUT": "^RUT",
        "EEM": "EEM",
        
        # ثانياً: أسواق الدخل الثابت (تكلفة الأموال)
        "US10Y": "^TNX",
        "US02Y": "^IRX",   # Use 13-week T-Bill as proxy for short-term if 2Y is unavailable, or ^ZT=F
        "HY_SPREAD": "HYG", # High Yield Corporate Bond ETF
        
        # ثالثاً: العملات (السيولة والتوترات)
        "DXY": "DX-Y.NYB",
        "EURUSD": "EURUSD=X",
        "USDJPY": "JPY=X",
        
        # رابعاً: السلع (التضخم والإنتاج)
        "GOLD": "GC=F",
        "OIL": "CL=F",
        "COPPER": "HG=F",
        
        # خامساً: مقاييس التقلب (الخوف)
        "VIX": "^VIX",
        
        # سادساً: الأصول الرقمية (السيولة البديلة)
        "BTC": "BTC-USD",
        
        # إضافات للنسب الاستخباراتية (Intelligence Ratios)
        "XLY": "XLY", # Consumer Discretionary
        "XLP": "XLP", # Consumer Staples
        "TLT": "TLT", # 20+ Year Treasury Bond
    }

    def __init__(self, target_asset: str):
        self.target_asset = target_asset
        self.payload = {
            "timestamp": datetime.now().isoformat(),
            "target_asset": self.target_asset,
            "layer_1_technical": {},
            "intelligence_ratios": {}, # الطبقة الجديدة للنسب الاستخباراتية
            "correlation_context": {}
        }

    def fetch_ohlcv_data(self, ticker: str, period="3mo", interval="1d"):
        """جلب بيانات OHLCV باستخدام yfinance (3 أشهر لتغطية الفترات السابقة)"""
        try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period=period, interval=interval)
            if data.empty:
                return None
            return data
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def calculate_intelligence_ratios(self):
        """حساب النسب الماكرو والاستخباراتية لتحديد بيئة السوق"""
        print("Calculating Intelligence Ratios (Macro & Sentiment)...")
        ctx = self.payload["correlation_context"]
        ratios = {}

        try:
            # 1. منحنى العائد (Yield Curve) — الفارق الفعلي
            if "US10Y" in ctx and "US02Y" in ctx:
                us10y = ctx["US10Y"]["close"]
                us02y = ctx["US02Y"]["close"]
                # تحويل عوائد yfinance (تكون عادة بـ 10x) إذا لزم الأمر، لكن ^TNX و ^IRX في نفس النطاق تقريباً
                spread = round(us10y - us02y, 4)
                ratios["yield_curve_spread"] = spread
                if spread < 0:
                    ratios["yield_curve_status"] = f"Inverted ({spread:.2f}) - ركود قادم"
                elif spread < 0.5:
                    ratios["yield_curve_status"] = f"Flat ({spread:.2f}) - ضغط سيولة"
                else:
                    ratios["yield_curve_status"] = f"Normal ({spread:.2f}) - نمو"
            
            # 2. النحاس إلى الذهب (Copper / Gold) - نمو vs خوف
            if "COPPER" in ctx and "GOLD" in ctx:
                ratios["copper_gold_ratio"] = round(ctx["COPPER"]["close"] / ctx["GOLD"]["close"], 6)
            
            # 3. الفارق الائتماني (Credit Spread Proxy: HYG / TLT)
            if "HY_SPREAD" in ctx and "TLT" in ctx:
                ratios["credit_stress_ratio"] = round(ctx["HY_SPREAD"]["close"] / ctx["TLT"]["close"], 4)
            
            # 4. الكماليات مقابل الأساسيات (XLY / XLP) - قوة المستهلك
            if "XLY" in ctx and "XLP" in ctx:
                ratios["consumer_strength_ratio"] = round(ctx["XLY"]["close"] / ctx["XLP"]["close"], 4)
            
            # 5. النمو مقابل القيمة (NDX / RUT) - تركز السيولة
            if "NDX" in ctx and "RUT" in ctx:
                ratios["liquidity_concentration_ratio"] = round(ctx["NDX"]["close"] / ctx["RUT"]["close"], 4)
            
            # 6. البيتكوين إلى الذهب (BTC / Gold) - أقصى مخاطرة vs أقصى تحوط
            if "BTC" in ctx and "GOLD" in ctx:
                ratios["digital_liquidity_proxy"] = round(ctx["BTC"]["close"] / ctx["GOLD"]["close"], 4)

            self.payload["intelligence_ratios"] = ratios
        except Exception as e:
            print(f"Error calculating ratios: {e}")

    def fetch_layer_1_technical(self):
        """جلب البيانات الفنية للأصل المستهدف والأصول المرجعية مع حساب مستويات AMT الزمنية الستة"""
        print("Fetching Layer 1: Technical & Correlation Data (Multi-Timeframe)...")
        
        # 1. جلب بيانات السلة المرجعية وحساب مستوياتها الزمنية
        asset_summary = {}
        for name, ticker in self.CROSS_ASSETS.items():
            df = self.fetch_ohlcv_data(ticker)
            if df is not None:
                last_row = df.iloc[-1]
                asset_summary[name] = {
                    "close": round(float(last_row['Close']), 4),
                    "volume": int(last_row['Volume']) if 'Volume' in last_row else 0,
                    "AMT_Temporal_Levels": AMTEngine.get_timeframe_levels(df)
                }
        
        self.payload["correlation_context"] = asset_summary
        
        # حساب النسب الاستخباراتية بعد توفر بيانات الأصول
        self.calculate_intelligence_ratios()
        
        # تشغيل محرك كشف النظام الاقتصادي
        print("Running Regime Detection Engine...")
        regime_result = RegimeDetector.detect(
            self.payload["intelligence_ratios"],
            self.payload["correlation_context"]
        )
        self.payload["market_regime"] = regime_result
        print(f"  → النظام: {regime_result['regime_name']} (ثقة: {regime_result['confidence']}%)")
        if regime_result['halt_algorithms']:
            print("  🔴 تحذير: يُنصح بإيقاف الخوارزميات!")
        
        # 2. جلب بيانات الأصل المستهدف وحساب مستوياته الزمنية
        target_df = self.fetch_ohlcv_data(self.target_asset)
        if target_df is not None:
            last_row = target_df.iloc[-1]
            self.payload["layer_1_technical"]["target_asset_data"] = {
                "close": round(float(last_row['Close']), 4),
                "volume": int(last_row['Volume']) if 'Volume' in last_row else 0
            }
            
            # حساب مستويات نظرية المزاد الزمنية الستة (D/W/M - Current/Prev)
            print(f"Calculating Multi-Timeframe AMT levels for {self.target_asset}...")
            temporal_levels = AMTEngine.get_timeframe_levels(target_df)
            self.payload["layer_1_technical"]["AMT_Temporal_Levels"] = temporal_levels
            
            # تحديد الحالة النسبية للسعر (بناءً على اليوم الحالي)
            if temporal_levels.get('current_day'):
                curr_day = temporal_levels['current_day']
                current_price = float(last_row['Close'])
                if current_price > curr_day['VAH']:
                    status = "Above Current Day Value Area"
                elif current_price < curr_day['VAL']:
                    status = "Below Current Day Value Area"
                else:
                    status = "Inside Current Day Value Area"
                self.payload["layer_1_technical"]["AMT_Status"] = status
        else:
             self.payload["layer_1_technical"]["target_asset_data"] = "Failed to fetch"

    def fetch_layer_2_macro(self):
        print("Fetching Layer 2: Macro...")
        macro_agent = MacroAgent()
        self.payload["layer_2_macro"] = macro_agent.generate()

    def fetch_layer_3_correlation(self):
        print("Fetching Layer 3: Correlation (Alpha Prime Correlation Agent)...")
        corr_agent = CorrelationAgent()
        self.payload["layer_3_correlation"] = corr_agent.generate()

    def fetch_layer_4_smart_money(self):
        print("Fetching Layer 4: Smart Money (Mock)...")
        self.payload["layer_4_smart_money"] = "Pending Quiver/OpenSecrets Integration"

    def fetch_layer_5_liquidity_sentiment(self):
        print("Fetching Layer 5: Liquidity & Sentiment (Mock)...")
        self.payload["layer_5_liquidity"] = "Pending alphaear-sentiment Integration"

    def fetch_layer_6_alt_data(self):
         print("Fetching Layer 6: Alt Data (Mock)...")
         self.payload["layer_6_alt_data"] = "Pending Alt Data plugins"

    def fetch_layer_7_logistics(self):
         print("Fetching Layer 7: Logistics (Mock)...")
         self.payload["layer_7_logistics"] = "Pending TradingEconomics / BDI Integration"

    def fetch_layer_8_catalysts(self):
        print("Fetching Layer 8: Catalysts (Mock)...")
        self.payload["layer_8_catalysts"] = "Pending alphaear-news Integration"

    def generate_context_json(self) -> str:
        self.fetch_layer_1_technical()
        self.fetch_layer_2_macro()
        self.fetch_layer_3_correlation()
        self.fetch_layer_4_smart_money()
        self.fetch_layer_5_liquidity_sentiment()
        self.fetch_layer_6_alt_data()
        self.fetch_layer_7_logistics()
        self.fetch_layer_8_catalysts()

        return json.dumps(self.payload, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    executor = AlphaPrimeExecutor(target)
    context_json = executor.generate_context_json()

    temp_file = os.path.join(os.path.dirname(__file__), "alpha_prime_context.json")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(context_json)

    print(f"\n✅ تم جلب السياق الاستخباراتي لـ {target}\n📄 الملف: {temp_file}")
