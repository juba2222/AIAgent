---
description: تشغيل وكيل الاستخبارات المالية Alpha Prime لتحليل السوق بالأبعاد السبعة
---
# تشغيل Alpha Prime Intelligence Agent

هذا المسار يقوم بتفعيل الوكيل الاستخباراتي المالي (Alpha Prime) بالكامل: جلب البيانات، تحليل الأنظمة، وتوليد التقرير الاستخباراتي باستخدام Gemini.

// turbo
1. **تشغيل الوكيل المركزي**
   شغل الأمر التالي لتحليل الأصل المطلوب (افتراضياً الذهب XAU=F):
   ```bash
   python c:\Users\Islam\Desktop\Trad\.agent\skills\alpha_prime_orchestrator\scripts\alpha_prime_agent.py --asset XAU=F --report both
   ```

2. **تحليل النتائج**
   الوكيل سيقوم آلياً بـ:
   - جلب OHLCV لـ 16+ أصل.
   - حساب نسب منحنى العائد، النحاس/الذهب، وفارق الائتمان.
   - كشف نظام السوق (Goldilocks/Stagflation/etc).
   - جلب الأخبار (AlphaEar News) وتحليل المشاعر (AlphaEar Sentiment).
   - إرسال البيانات لـ Gemini وإصدار تقرير شامل (.md) في مجلد `/reports`.

---
💡 **نصيحة:** يمكنك تغيير الأصل بإضافة `--asset BTC-USD` أو `--asset NVDA` للأمر أعلاه.
