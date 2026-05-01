---
description: تشغيل وكيل الاستخبارات المالية Alpha Prime لتحليل السوق بالأبعاد السبعة
---
# تشغيل Alpha Prime Intelligence Agent

هذا المسار يقوم بتفعيل الوكيل الاستخباراتي المالي (Alpha Prime) على أصل معين (مثلاً الذهب أو SPY).

1. **الخطوة الأولى: جلب السياق وتوليد الـ JSON**
   استخدم أمر تشغيل السكريبت المنسق لجلب طبقات البيانات السبعة.
   ```bash
   python c:\Users\Islam\Desktop\Trad\.agent\skills\alpha-prime-orchestrator\scripts\alpha_prime_executor.py
   ```
   (ملاحظة: هذا السكريبت سيستدعي المهارات ويحفظ البيانات في ملف `alpha_prime_context.json`).

2. **الخطوة الثانية: قراءة البيانات**
   اطلب من الوكيل (أنا) أن أقرأ مخرجات ملف `alpha_prime_context.json`.

3. **الخطوة الثالثة: تطبيق الموجه (System Prompt Injection)**
   الآن اطلب من الوكيل تطبيق تعليمات `agent_system_prompt.md` (برومبت نظرية المزاد والطبقات السبعة) على هذا الـ JSON لإصدار التقارير النهائية كما هو موضح في الموجه:
   - التقرير الأول: Global Intel Snapshot.
   - التقرير الثاني: Execution Strategy للأصل المستهدف بناءً على خطوط الـ AMT.
