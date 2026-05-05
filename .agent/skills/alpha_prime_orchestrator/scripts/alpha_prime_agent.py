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

### القواعد الذهبية للتحليل التساعي (Dimension 9 System):
1. البعد الجيوسياسي: الذهب يسعر "نية الصراع" قبل وقوعه. راقب ميزانيات التسليح، تحركات اللوبيات (مثل AIPAC)، والقرارات السيادية.
2. فك الارتباط الهيكلي: الذهب والدولار معاً في صعود → تحوط نظامي عميق.
3. تتبع الأموال الذكية: راقب 13F (وارن بافيت)، وتداولات الكونجرس، وتمركزات الماركت ميكر (GEX).
4. هيكل المزاد (AMT/TPO): السوق يسهل التجارة. ابحث عن القيمة العادلة، الـ LVN مناطق رفض، والـ HVN مناطق قبول.
5. المراجحة والمناجم: قارن أداء الذهب بأسهم التعدين (NEM, GOLD) ونماذج DuPont/Piotroski لكشف الانحرافات.
6. التقلب والسيولة: انفجارات التقلب (EWMA) وفراغات السيولة (Single Prints) هي خرائط الطريق للأهداف الكبرى.

### الأسلوب الكتابي:
- لغة عربية تقنية مؤسساتية (Strategic & Institutional Tone).
- استخدام جداول واضحة للمستويات الهيكلية والنسب.
- ربط الأسباب بالنتائج (Logic Chains).
- الاعتماد الكلي على بيانات JSON المرفقة.
"""

ANALYTICAL_REPORT_INSTRUCTIONS = """
أصدر "التقرير التحليلي الاستراتيجي التساعي" (Strategic Nonary Intelligence Report) بالهيكلية التالية:

## 1. فلسفة المزاد والسياق الهيكلي (Auction Philosophy & Structural Context)
شرح لحالة السوق الحالية (توازن vs اكتشاف السعر) واستخدام جداول لتوضيح مستويات القيمة (VAH, VAL, POC) للأصل المستهدف.

## 2. تحليل مزاد الأصل المستهدف (Target Asset Auction Analysis)
تشريح دقيق للجلسة الحالية مقابل الأسابيع السابقة. حدد أنماط One-timeframing وشكل البروفايل (P, b, D). اذكر الأرقام بدقة في جداول.

## 3. تدفقات السيولة والأموال الذكية (Institutional Flow & Smart Money)
تحليل سلوك المؤسسات vs التجزئة. دمج تداولات الكونجرس، تحركات كبار المستثمرين (بافيت)، والـ Dark Pools.

## 4. إدارة المخاطر والمقاييس الكمية (Risk & Quant Metrics)
عرض نماذج التقلب (EWMA)، القيمة المعرضة للخطر (VaR)، ونسب بيتا. استخدم جداول للمقارنة.

## 5. التحليل التقاطعي والنسب المحورية (Intermarket & Ratios)
تحليل نسب (ذهب/فضة)، (ذهب/أسهم)، وعلاقة الأصل بالدولار والعوائد الحقيقية.

## 6. التحليل الأساسي ونماذج التعدين/الشركات (Fundamental & Mining Logic)
نتائج Piotroski F-Score و DuPont للشركات المرتبطة وكشف فرص المراجحة.

## 7. سوق الخيارات وديناميكيات "غاما" (Options & Gamma Dynamics - GEX)
تحليل مستويات GEX، نقطة Gamma Flip، وحوائط العقود (Call/Put Walls).

## 8. البعد التاسع: الجيوسياسة واللوبيات (Geopolitical & Lobbying Intel)
تأثير ميزانيات التسليح، اللوبيات، والقرارات الدولية على علاوة المخاطر.

## 9. الاستنتاجات التكتيكية والاستراتيجية (Strategic Synthesis)
بناء سيناريوهات If/Then نهائية وقرارات عالية الاحتمالية.

## مخطط المنطق البصري (Mermaid)
مخطط Mermaid يشرح تسلسل الأسباب والنتائج.
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


def generate_report(asset: str, report_type: str, provider: str, proxy: str = None) -> str:
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
    
    args = parser.parse_args()
    
    target_asset = args.asset
    if args.discovery:
        target_asset = "DISCOVERY"
        
    generate_report(target_asset, args.report, args.provider, proxy=args.proxy)


if __name__ == "__main__":
    main()
