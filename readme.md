# 🤖 Alpha Prime: Senior Macro Algo-Strategist

وكيل ذكاء اصطناعي يعالج **12 طبقة** من البيانات الاستخباراتية (من الماكرو إلى التنبؤات العصبية) لإنتاج تقارير تداول قائمة على **الإطار الديناميكي للارتباطات**، نظرية المزاد (AMT)، وتتبع السيولة الذكية.

---

## 🧠 الهوية
**محلل كمي استراتيجي (Senior Macro Algo-Strategist)** — يصدر تقارير فنية دقيقة قابلة للترجمة إلى خوارزميات تداول (Pine Script / MQL5 / Python).

> **المبدأ الأساسي:** الارتباطات ليست ثوابت رياضية، بل ديناميكيات متغيرة تتأثر بنظام السوق ونوع الصدمة ومستوى التضخم وحالة السيولة.

---

## 🛡️ القواعد الذهبية (Golden Rules)
| # | القاعدة | التطبيق |
|:--|:---|:---|
| 1 | **الارتباط التربيعي** | أسهم-سندات: سلبي عند تضخم 2%، إيجابي عند الانحراف |
| 2 | **فك ارتباط الذهب/الدولار** | ارتفاعهما معاً = جيوسياسي/هيكلي، وليس نقدياً |
| 3 | **القيادة الزمنية** | السندات تسعر الركود قبل الأسهم بـ 3-6 أشهر |
| 4 | **العوائد الحقيقية** | TIPS > 2% → رياح معاكسة للذهب وأسهم النمو |
| 5 | **أزمة السيولة** | VIX+MOVE مرتفعان → كل شيء يهبط → الدولار فقط ينجو |
| 6 | **عملات السلع** | حلل المنطقة الجغرافية للطلب، وليس سعر السلعة فقط |

---

## 📊 نظم الأسواق الأربعة (Market Regimes)
| النظام | الأصول المتفوقة | ارتباط أسهم/سندات |
|:---|:---|:---|
| النمو المستقر (Goldilocks) | أسهم + سندات | سلبي (تنويع يعمل) |
| التضخم الركودي (Stagflation) | ذهب + سلع + نقد | **إيجابي (تنويع يفشل)** |
| الركود الانكماشي | سندات حكومية + ذهب | سلبي قوي |
| الانتعاش التضخمي | سلع + أسهم دورية | إيجابي متوسط |

---

## 📈 النسب الاستخباراتية (Intelligence Ratios)
*   **ماكرو:** US10Y/US02Y، Copper/Gold، Global Liquidity/SPX
*   **هيكل السوق:** HYG/TLT، XLY/XLP، NDX/RUT
*   **أموال ذكية:** Congress Trading (Quiver API)، Insider Activity
*   **تنبؤات:** Neural Price Targets (Layer 10)، Signal Evolution (Layer 12)
*   **كريبتو:** BTC/XAU، MVRV، NVT

---

## 📝 هيكلية التقارير
### التقرير التحليلي (Global Intel):
1. Macro Regime Assessment → 2. Liquidity Map → 3. Structural Risk → 4. XAU Deep-Dive → 5. Crypto Structure → 6. Algo Output

### تقرير التنفيذ (Execution Strategy):
1. Macro Context → 2. Multi-TF AMT (PM/CM, PW/CW, PD/CD) → 3. Algo-Trade Setups (If/Then) → 4. Conviction Score + R:R

---

## 🚀 الفلاتر الخوارزمية
```
# كشف النظام
IF 2s10s < 0 AND CPI > 3.5% → STAGFLATION
IF 2s10s > 50bps AND CPI < 2.5% → GOLDILOCKS

# إيقاف الطوارئ
IF VIX > 35 AND MOVE > 150 → HALT ALL

# التحقق من الارتباط
IF Gold↑ AND DXY↑ → لا تبيع الذهب (جيوسياسي)
IF TIPS > 2.0% → قلل الذهب + النمو
```

---

## ⚡ التشغيل السريع (Quick Start)
# 1. اضبط مفتاح Gemini 
$env:GEMINI_API_KEY="your-key-here"

# 2. شغّل التقرير الاستخباراتي الشامل (12 طبقة)
cd .agent\skills\alpha_prime_orchestrator\scripts
python alpha_prime_agent.py --asset NVDA --report both
```
📖 [دليل التشغيل الكامل](docs/QUICKSTART.md)

---

## 📂 الوثائق التفصيلية
*   [🚀 دليل التشغيل السريع](docs/QUICKSTART.md) — كيف تشغّل الوكيل خطوة بخطوة
*   [🩺 تشخيص حالة المشروع](docs/PROJECT_DIAGNOSIS.md) — التقرير الفني للجاهزية
*   [🔬 الإطار الديناميكي للارتباطات](docs/DYNAMIC_CORRELATION_FRAMEWORK.md) — المرجع الأساسي الشامل
*   [🏆 الإنجازات والأهداف](docs/ACHIEVEMENTS_AND_GOALS.md)
*   [🛠️ القدرات التقنية](docs/TECHNICAL_CAPABILITIES.md)
*   [📈 منهجية AMT](docs/AMT_METHODOLOGY.md)
