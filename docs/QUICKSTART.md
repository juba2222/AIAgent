# 🚀 دليل التشغيل السريع (Quick Start Guide)

## المتطلبات المسبقة

### 1. تثبيت المكتبات
```powershell
cd c:\Users\Islam\Desktop\Trad
pip install -r requirements.txt
```

### 2. ضبط مفاتيح API (إلزامي)

#### مفتاح Gemini (مجاني — الأهم)
1. اذهب إلى: https://aistudio.google.com/apikey
2. اضغط "Create API Key"
3. اضبطه:
```powershell
$env:GEMINI_API_KEY="your-key-here"
```

#### مفتاح FRED (مجاني — اختياري لتعزيز البيانات الماكرو)
1. اذهب إلى: https://fred.stlouisfed.org/docs/api/api_key.html
2. سجّل واحصل على المفتاح
3. اضبطه:
```powershell
$env:FRED_API_KEY="your-key-here"
```

#### مفتاح Quiver Quantitative (اختياري - لمراقبة الأموال الذكية)
1. اذهب إلى: https://www.quiverquant.com/api/
2. احصل على مفتاح مجاني (Free Tier)
3. اضبطه:
```powershell
$env:QUIVER_API_KEY="your-key-here"
```

> **لجعل المفاتيح دائمة** (لا تضيع عند إغلاق الطرفية):
> ```powershell
> [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key", "User")
> [System.Environment]::SetEnvironmentVariable("FRED_API_KEY", "your-key", "User")
> ```

---

## طرق التشغيل

### التقرير التحليلي الشامل (6 أقسام)
```powershell
cd c:\Users\Islam\Desktop\Trad\.agent\skills\alpha_prime_orchestrator\scripts
python alpha_prime_agent.py --asset XAU=F --report full
```

### تقرير استراتيجية التنفيذ (4 أقسام — لأصل محدد)
```powershell
python alpha_prime_agent.py --asset BTC-USD --report execution
```

### التقريران معاً
```powershell
python alpha_prime_agent.py --asset NVDA --report both
```

### استخدام OpenAI بدل Gemini
```powershell
$env:OPENAI_API_KEY="sk-..."
python alpha_prime_agent.py --asset XAU=F --report full --provider openai
```

---

## أمثلة على الأصول المدعومة

| الأصل | الرمز |
|:---|:---|
| الذهب | `XAU=F` أو `GC=F` |
| البيتكوين | `BTC-USD` |
| النفط | `CL=F` |
| إنفيديا | `NVDA` |
| S&P 500 | `^GSPC` |
| الدولار | `DX-Y.NYB` |

---

## مسار الملفات الناتجة
- **البيانات الخام:** `scripts/alpha_prime_context.json` (يتم تحديثه عند كل تشغيل)
- **التقارير:** مجلد `reports/` يحتوي على تقارير بصيغة Markdown.
- **الأخبار:** يتم حفظ الأخبار في قاعدة بيانات محلية في مجلد مهارة `alphaear_news`.

---

## استكشاف الأخطاء

| المشكلة | الحل |
|:---|:---|
| `❌ لم يتم العثور على GEMINI_API_KEY` | اضبط المفتاح: `$env:GEMINI_API_KEY="..."` |
| `Error fetching FRED series` | اضبط مفتاح FRED أو تجاهل (اختياري) |
| `SettingWithCopyWarning` | تم إصلاحه — تأكد من آخر نسخة |
| التقرير فارغ | تحقق من اتصال الإنترنت (yfinance يحتاج اتصال) |
