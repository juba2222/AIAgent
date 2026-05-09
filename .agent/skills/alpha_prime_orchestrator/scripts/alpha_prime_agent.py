"""
Alpha Prime Agent — العقل المركزي
يجمع البيانات + يكشف النظام + يرسل للنموذج اللغوي + يصدر التقرير الاستخباراتي.

الاستخدام:
    python alpha_prime_agent.py --asset XAU=F --report full
    python alpha_prime_agent.py --asset BTC-USD --report execution
    python alpha_prime_agent.py --asset NVDA --report full --provider openai
"""

import json
import os
import sys
import argparse
from datetime import datetime

from alpha_prime_executor import AlphaPrimeExecutor

# إضافة مسارات المهارات للاستيراد
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "alphaear_discovery", "scripts"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "alphaear_deepear_lite", "scripts"))

try:
    from discovery_tools import DiscoveryTools
    from deepear_lite import DeepEarLiteTools
except ImportError:
    DiscoveryTools = None
    DeepEarLiteTools = None

# ─────────────────────────────────────────────
# System Prompt — الدستور المعماري للوكيل
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
أنت "محلل كمي استراتيجي" (Senior Macro Algo-Strategist) من النخبة، خبير في البنية الدقيقة للسوق، نظرية المزاد (AMT)، والتحليل البيني (Intermarket Analysis).

المبدأ الأساسي: الارتباطات ليست ثوابت رياضية، بل ديناميكيات متغيرة تتأثر بنظام السوق (Market Regime) ونوع الصدمة ومستوى التضخم وحالة السيولة.

### القواعد الذهبية للنظام التساعي (Nonary Analysis System):
أنت تدمج 14 طبقة من الاستخبارات المالية في 9 أبعاد استراتيجية:
1. البعد الجيوسياسي واللوبيات: الذهب يسعر "نية الصراع" قبل وقوعه. راقب ميزانيات التسليح، تحركات اللوبيات (مثل AIPAC)، والقرارات السيادية.
2. فك الارتباط الهيكلي: الذهب والدولار معاً في صعود → تحوط نظامي عميق ضد انهيار العملات الورقية.
3. تتبع الأموال الذكية (Smart Money): راقب 13F (وارن بافيت)، وتداولات أعضاء الكونجرس، وتمركزات الماركت ميكر (GEX)، وتقارير COT للفيوتشرز، والـ Dark Pools.
4. هيكل المزاد (AMT/TPO): ابحث عن القيمة العادلة (POC/VAH/VAL). الـ LVN مناطق رفض (بالون)، والـ HVN مناطق قبول (مغناطيس). راقب "One-timeframing" لتأكيد سيطرة طرف واحد. عند المقارنة بين الأصول، انتبه لنوع البروفايل (Volume vs TPO)؛ بروفايل الحجم يعكس تمركز الأموال الحقيقي، بينما بروفايل الوقت (TPO) يعكس قبول السعر زمنياً. التوافق بين النوعين يعطي إشارة عالية اليقين.
5. المراجحة والمناجم: قارن أداء الذهب بأسهم التعدين ونماذج DuPont/Piotroski لكشف انحرافات الـ Alpha.
6. التقلب والسيولة: انفجارات التقلب (GARCH/EWMA) وفراغات السيولة (Single Prints) هي خرائط الطريق للأهداف الكبرى.
7. الدورة الاقتصادية والسيولة (Macro Context): تتبع الفائدة الحقيقية (TIPS)، منحنى العائد، ونمو المعروض النقدي (M2).
8. الارتباطات الديناميكية: راقب تحركات MOVE (تقلب السندات) مقابل TLT والذهب.
9. التنبؤ الخوارزمي: دمج نماذج السلاسل الزمنية العصبية مع مستويات السيولة لتحديد الأهداف.

### الأسلوب الكتابي:
- لغة عربية تقنية مؤسساتية (Strategic & Institutional Tone).
- استخدام جداول واضحة وشاملة للمستويات الهيكلية والنسب المحورية.
- بناء "سلاسل منطقية" (Logic Chains) تربط بين البيانات الاستخباراتية والنتائج التكتيكية.
- الاعتماد الكلي على بيانات JSON المرفقة التي تغطي كافة الأصول الأساسية والنسب.
"""

ANALYTICAL_REPORT_INSTRUCTIONS = """
أصدر "التقرير التحليلي الاستراتيجي التساعي" (Strategic Nonary Intelligence Report) بالهيكلية التالية:

## 1. الملخص الاستخباراتي التنفيذي (Executive Intel Summary)
توصيف "نظام السوق" الحالي (Market Regime) ودرجة اليقين (Confidence Score).

## 2. مصفوفة مستويات المزاد (Multi-Timeframe AMT Matrix)
جدول شامل يعرض مستويات POC, VAH, VAL للأصل المستهدف للفترات:
- اليوم الحالي (CD) واليوم السابق (PD)
- الأسبوع الحالي (CW) والأسبوع السابق (PW)
- الشهر الحالي (CM) والشهر السابق (PM)
تحليل شكل البروفايل (P/b/D) وحالة التوازن.

## 3. تدفقات السيولة والأموال الذكية (Smart Money & Institutional Flow)
تحليل تداولات الكونجرس، تحركات الحيتان (Buffett/13F)، وبيانات الـ Dark Pools والـ COT (إذا توفرت).

## 4. إدارة المخاطر والمقاييس الكمية (Risk & Quant Metrics)
جدول يوضح: EWMA Volatility, VaR (95%), Beta, و Risk/Reward Ratio.

## 5. التحليل التقاطعي والنسب المحورية (Intermarket Matrix)
تحليل العلاقات بين الذهب، الدولار، السندات (MOVE/TLT)، والأسهم.
جدول النسب: (Gold/Silver), (Gold/S&P), (Copper/Gold), (Yield Curve Spread).

## 6. التحليل الأساسي وهيكلة الـ Alpha (Fundamental & Mining Logic)
نتائج Piotroski F-Score و DuPont لشركات التعدين الكبرى (NEM, GOLD) وفرص المراجحة.

## 7. ديناميكيات "غاما" والخيارات (Options GEX Context)
تحديد مستويات Gamma Flip وحوائط العقود Call/Put Walls التي تعمل كمغناطيس أو جدران صد.

## 8. البعد التاسع: الجيوسياسة واللوبيات (Geopolitical & Lobbying Intel)
تحليل تأثير اللوبيات (AIPAC)، قرارات الإنفاق العسكري، والتوترات الجيوسياسية المكتشفة من الأخبار.

## 9. التجميع الاستراتيجي والسيناريوهات (Strategic Synthesis)
بناء سلاسل منطقية (Logic Chains): "بما أن [بيان]، إذن [توقع]، بشرط [شرط]".
سيناريوهات If/Then واضحة للتنفيذ.

## مخطط المنطق البصري (Visual Logic - Mermaid)
مخطط Mermaid يشرح تدفق القرار الاستراتيجي.
"""

EXECUTION_REPORT_INSTRUCTIONS = """
أصدر "تقرير استراتيجية التنفيذ" (Execution Strategy Report) للأصل المستهدف بالهيكلية التالية:

## 1. انعكاس السياق على الأصل (Macro Context)
ربط البيئة الكلية بسلوك الأصل. هل هو Risk-On أم Risk-Off الآن؟

## 2. تحليل هيكل المزاد متعدد الفترات (Multi-Timeframe AMT Analysis)
تشريح مصفوفة السيولة (VPOC, VAH, VAL) للمصفوفة:
- الشهرية: PM vs CM
- الأسبوعية: PW vs CW
- اليومية: PD vs CD
حدد: توازن (Balance) أم اكتشاف (Discovery)؟ أين الفراغات السعرية (Liquidity Voids)؟

## 3. التنبؤ العصبي والأهداف السعرية (Neural Forecast & Price Targets - Layer 10)
توقعات الحركة السعرية القادمة بناءً على مهارة Predictor ونماذج السلاسل الزمنية. اذكر مستويات Target 1 و Target 2.

## 4. أفضل إعدادات الصفقات الخوارزمية (Optimal Algo-Trade Setups)
إعدادين بصيغة If/Then:
- إعداد الارتداد (Mean Reversion)
- إعداد الاختراق (Breakout)
مع فلاتر إبطال (VIX, Liquidity).

## 5. مخطط المنطق البصري (Visual Logic Flow - Mermaid)
مخطط Mermaid يوضح تسلسل اتخاذ القرار لهذا الأصل تحديداً.

## 6. درجة اليقين وإدارة المخاطر (Conviction Score & Risk Metrics)
تقييم 1-10 + R:R + نقطة الاستسلام (Invalidation Level).
"""


def call_gemini(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """استدعاء Gemini API لتوليد التقرير."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        system_instruction=system_prompt
    )
    
    response = model.generate_content(
        user_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=8000,
        )
    )
    return response.text


def call_openai(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """استدعاء OpenAI API لتوليد التقرير."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=8000
    )
    return response.choices[0].message.content


def generate_report(asset: str, report_type: str, provider: str, proxy: str = None, use_db: bool = False) -> str:
    """
    المسار الكامل: جلب البيانات → كشف النظام → توليد التقرير.
    """
    # === 0. Discovery Logic (Optional) ===
    if asset == "DISCOVERY":
        print("\n🔍 البدء في وضع الاستكشاف الذكي (Discovery Mode)...")
        if not DeepEarLiteTools or not DiscoveryTools:
            print("❌ خطأ: مهارات الاستكشاف أو DeepEar غير متوفرة.")
            return None
        
        det = DeepEarLiteTools()
        signals = det.fetch_latest_signals()
        
        # استخراج أول إشارة قوية
        if not signals:
            print("⚠️ لم يتم العثور على إشارات حديثة من DeepEar. استخدام أصل افتراضي.")
            asset = "BTC-USD"
        else:
            first_signal = signals[0]
            theme = first_signal.get("title", "")
            print(f"📌 المحفز المكتشف: {theme}")
            
            dt = DiscoveryTools()
            # محاولة البحث عن أصول مرتبطة بالثيم
            discovery_results = dt.search_equities(query=theme) or dt.search_etfs(query=theme)
            
            if discovery_results:
                asset = discovery_results[0]['ticker']
                print(f"🎯 تم اختيار الأصل: {asset} ({discovery_results[0]['name']})")
            else:
                print("⚠️ لم يتم العثور على أصول مرتبطة مباشرة. استخدام BTC-USD كمؤشر سيولة.")
                asset = "BTC-USD"

    # === 1. جلب البيانات ===
    print("=" * 60)
    print(f"🚀 Alpha Prime Agent — تحليل {asset}")
    print(f"   النوع: {report_type} | المزود: {provider}")
    if proxy: print(f"   Proxy: {proxy}")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(__file__), "data", "alpha_prime_intelligence_db.json")
    if use_db and os.path.exists(db_path):
        print(f"📂 تحميل البيانات من قاعدة البيانات المحلية ({db_path})...")
        with open(db_path, "r", encoding="utf-8") as f:
            full_db = json.load(f)
            # Use data from DB if it matches the target asset, otherwise fetch fresh for specific asset context
            # However, the DB generated by intelligence_collector already contains a comprehensive snapshot.
            context_json = json.dumps(full_db, indent=4, ensure_ascii=False)
            # Create a dummy executor to handle the logic below, or better, re-parse the data
            executor = AlphaPrimeExecutor(asset, proxy=proxy)
            executor.payload = full_db
    else:
        executor = AlphaPrimeExecutor(asset, proxy=proxy)
        context_json = executor.generate_context_json()
    
    # === 2. تحضير البرومبت ===
    regime = executor.payload.get("market_regime", {})
    regime_name = regime.get("regime_name", "غير محدد")
    
    if report_type == "full":
        instructions = ANALYTICAL_REPORT_INSTRUCTIONS
    elif report_type == "execution":
        instructions = EXECUTION_REPORT_INSTRUCTIONS
    else:
        instructions = ANALYTICAL_REPORT_INSTRUCTIONS + "\n\n---\n\n" + EXECUTION_REPORT_INSTRUCTIONS
    
    user_prompt = f"""
الأصل المستهدف: {asset}
التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
النظام الاقتصادي المكتشف: {regime_name}

{instructions}

--- بيانات السياق (JSON) ---
{context_json}
"""
    
    # === 3. استدعاء النموذج ===
    api_key = None
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "AIzaSyDp7sYunAMgQez_4tGzfP9oVANlhis9QRE"
        if not api_key:
            print("\n❌ خطأ: لم يتم العثور على GEMINI_API_KEY")
            print("   اضبطه بالأمر: $env:GEMINI_API_KEY='your-key-here'")
            print("   أو احصل على مفتاح مجاني من: https://aistudio.google.com/apikey")
            return None
        
        print("\n🧠 إرسال البيانات إلى Gemini...")
        # التحقق من تركز السيولة لإضافة تحذير خاص
        concentration = executor.payload.get("intelligence_ratios", {}).get("liquidity_concentration_ratio", 0)
        if isinstance(concentration, (int, float)) and concentration > 10.0:
            user_prompt = f"🚨 تنبيه نظام: تركز السيولة مرتفع جداً ({concentration:.2f}) - حذر من انزلاق سعري حاد.\n\n" + user_prompt

        report = call_gemini(SYSTEM_PROMPT, user_prompt, api_key)
        
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n❌ خطأ: لم يتم العثور على OPENAI_API_KEY")
            return None
        
        print("\n🧠 إرسال البيانات إلى OpenAI...")
        report = call_openai(SYSTEM_PROMPT, user_prompt, api_key)
    
    else:
        print(f"❌ مزود غير معروف: {provider}")
        return None
    
    # === 4. حفظ التقرير ===
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    report_path = os.path.join(report_dir, f"report_{asset.replace('=','').replace('-','').replace('/','_')}_{timestamp}.md")
    
    full_report = f"""# 📊 تقرير Alpha Prime — {asset}
**التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**النظام الاقتصادي:** {regime_name}
**الثقة:** {regime.get('confidence', 'N/A')}%
**تحذيرات:** {', '.join(regime.get('warnings', [])) or 'لا يوجد'}

---

{report}
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    
    print(f"\n{'=' * 60}")
    print(f"✅ تم إصدار التقرير بنجاح!")
    print(f"📄 المسار: {report_path}")
    print(f"{'=' * 60}")
    
    # عرض التقرير في الطرفية
    print(f"\n{full_report}")
    
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Alpha Prime Intelligence Agent")
    parser.add_argument("--asset", type=str, default="XAU=F",
                        help="الأصل المستهدف (مثل: XAU=F, BTC-USD, NVDA)")
    parser.add_argument("--report", type=str, default="full",
                        choices=["full", "execution", "both"],
                        help="نوع التقرير: full (تحليلي) / execution (تنفيذي) / both")
    parser.add_argument("--provider", type=str, default="gemini",
                        choices=["gemini", "openai"],
                        help="مزود النموذج اللغوي: gemini / openai")
    
    parser.add_argument("--proxy", type=str, default=None,
                        help="HTTP/HTTPS Proxy (e.g., http://user:pass@host:port)")
    parser.add_argument("--discovery", action="store_true",
                        help="تفعيل وضع الاستكشاف الآلي بناءً على إشارات DeepEar")
    parser.add_argument("--db", action="store_true",
                        help="استخدام قاعدة البيانات المحلية alpha_prime_intelligence_db.json بدلاً من جلب بيانات جديدة")
    
    args = parser.parse_args()
    
    target_asset = args.asset
    if args.discovery:
        target_asset = "DISCOVERY"
        
    generate_report(target_asset, args.report, args.provider, proxy=args.proxy, use_db=args.db)


if __name__ == "__main__":
    main()
