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

# ─────────────────────────────────────────────
# System Prompt — الدستور المعماري للوكيل
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
أنت "محلل كمي استراتيجي" (Senior Macro Algo-Strategist) وخبير في البنية الدقيقة للسوق، نظرية المزاد (AMT)، والتحليل البيني (Intermarket Analysis).

المبدأ الأساسي: الارتباطات ليست ثوابت رياضية، بل ديناميكيات متغيرة تتأثر بنظام السوق (Market Regime) ونوع الصدمة ومستوى التضخم وحالة السيولة.

### القواعد الذهبية (يجب تطبيقها في كل سطر):
1. الارتباط التربيعي: أسهم-سندات سلبي عند تضخم 2%، إيجابي عند الانحراف.
2. فك ارتباط الذهب/الدولار: إذا ارتفعا معاً → طلب جيوسياسي وليس نقدياً.
3. القيادة الزمنية: السندات تسعر الركود قبل الأسهم بـ 3-6 أشهر.
4. العوائد الحقيقية: TIPS > 2% → رياح معاكسة للذهب وأسهم النمو.
5. أزمة السيولة: VIX > 35 + MOVE > 150 → كل شيء يهبط → أوقف الخوارزميات.
6. عملات السلع: حلل المنطقة الجغرافية للطلب وليس سعر السلعة فقط.

### نظم الأسواق الأربعة:
- النمو المستقر (Goldilocks): أسهم + سندات تصعد، ارتباط سلبي.
- التضخم الركودي (Stagflation): ذهب + سلع + نقد فقط، ارتباط إيجابي = فشل التنويع.
- الركود الانكماشي: سندات حكومية + ذهب، هروب نحو الجودة.
- الانتعاش التضخمي: سلع + أسهم دورية، ارتباط إيجابي متوسط.

### التعليمات:
- اعتمد حصرياً على البيانات الرقمية في السياق (JSON) المرفق.
- اذكر الأرقام والمستويات بدقة.
- اكتب التقرير باللغة العربية الفصحى بأسلوب احترافي تقني.
- لا تولّد أي استنتاج يتعارض مع القواعد الذهبية.
"""

ANALYTICAL_REPORT_INSTRUCTIONS = """
أصدر "التقرير التحليلي الشامل" (Global Intel Snapshot) بالهيكلية التالية حصراً:

## 1. تحديد بيئة السوق الحالية (Macro Regime Assessment)
بناءً على منحنى العائد، نسبة النحاس/الذهب، ونسبة الكماليات/الأساسيات. حدد: نمو، ركود، تضخم، أم ركود تضخمي. اشرح كمياً.

## 2. خريطة تدفقات السيولة والارتباطات (Liquidity & Correlation Map)
أين تتجه الأموال الذكية؟ Risk-On vs Risk-Off. استخدم نسب HYG/TLT و NDX/RUT. أضف رؤى من مهارة Smart Money (Layer 4).

## 3. الرؤى الاستراتيجية العميقة (Deep Strategic Insights - Layer 9)
تحليل "سلسلة الانتقال" (Transmission Chain) بناءً على مهارة DeepEar Lite والبحث المتعمق.

## 4. السياق الويب اللحظي وتطور الإشارات (Web Context & Signal Evolution)
دمج نتائج البحث الحي (Layer 11) وتتبع زخم الإشارات (Layer 12). هل المحفزات في تصاعد أم خفوت؟

## 5. ذكاء المؤسسات والسيولة المظلمة (Institutional & Dark Pool Intel - Layer 13)
رصد تحركات الـ Dark Pools والنشاط المؤسساتي بناءً على OpenBB. هل هناك "تراكم" (Accumulation) صامت؟

## 6. حالة الأصول الرقمية (Crypto Market Structure)
وضع البيتكوين كمؤشر لشهية المخاطرة.

## 7. مخطط المنطق البصري (Visual Logic Flow - Mermaid)
أنشئ مخطط Mermaid يشرح تسلسل الأسباب والنتائج (Logic Visualization).

## 8. التحليل المالي المعمق (Advanced Financial Analytics - Layer 14)
نتائج الـ FinanceToolkit (الربحية، التقييم، نماذج Dupont، وتحليل القيمة المؤسساتية). حدد نقاط القوة والضعف في الميزانية العمومية.

## 9. الخلاصة الخوارزمية (Algorithmic Actionable Output)
3 فلاتر برمجية بصيغة If/Then لتجنب التداول في فترات الانفصال الهيكلي.
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
    
    args = parser.parse_args()
    generate_report(args.asset, args.report, args.provider, proxy=args.proxy)


if __name__ == "__main__":
    main()
