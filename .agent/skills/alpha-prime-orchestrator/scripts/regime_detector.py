"""
محرك كشف النظام الاقتصادي (Regime Detection Engine)
يطبّق الإطار الديناميكي للارتباطات لتصنيف بيئة السوق الحالية.
"""

class RegimeDetector:
    """
    يحدد نظام السوق الحالي بناءً على النسب الاستخباراتية:
    - Goldilocks (نمو مستقر)
    - Stagflation (تضخم ركودي)
    - Recession (ركود انكماشي)
    - Reflation (انتعاش تضخمي)
    """

    @staticmethod
    def detect(intelligence_ratios: dict, correlation_context: dict) -> dict:
        """
        تحديد نظام السوق بناءً على البيانات الفعلية.
        
        Returns:
            dict with: regime, confidence, signals, warnings
        """
        signals = []
        warnings = []
        scores = {
            "goldilocks": 0,
            "stagflation": 0,
            "recession": 0,
            "reflation": 0
        }

        # === 1. تحليل منحنى العائد (Yield Curve) ===
        yield_curve = intelligence_ratios.get("yield_curve_spread")
        if yield_curve is not None:
            if yield_curve < 0:
                scores["recession"] += 3
                scores["stagflation"] += 2
                signals.append(f"⚠️ منحنى العائد منعكس ({yield_curve:.1f} bps) → إشارة ركود")
            elif yield_curve < 50:
                scores["recession"] += 1
                scores["stagflation"] += 1
                signals.append(f"📉 منحنى العائد مسطّح ({yield_curve:.1f} bps) → ضغط على البنوك")
            elif yield_curve > 100:
                scores["goldilocks"] += 2
                scores["reflation"] += 1
                signals.append(f"📈 منحنى العائد طبيعي ({yield_curve:.1f} bps) → نمو صحي")
            else:
                scores["goldilocks"] += 1
                scores["reflation"] += 1

        # === 2. تحليل النحاس/الذهب (Copper/Gold) ===
        copper_gold = intelligence_ratios.get("copper_gold_ratio")
        if copper_gold is not None:
            if copper_gold > 0.0018:
                scores["reflation"] += 2
                scores["goldilocks"] += 1
                signals.append(f"🏭 النحاس/الذهب مرتفع ({copper_gold:.4f}) → توسع صناعي")
            elif copper_gold < 0.0012:
                scores["recession"] += 2
                scores["stagflation"] += 1
                signals.append(f"🛡️ النحاس/الذهب منخفض ({copper_gold:.4f}) → هروب للملاذات")
            else:
                scores["goldilocks"] += 1

        # === 3. تحليل الفارق الائتماني (HYG/TLT) ===
        credit_stress = intelligence_ratios.get("credit_stress_ratio")
        if credit_stress is not None:
            if credit_stress < 0.85:
                scores["recession"] += 3
                scores["stagflation"] += 2
                signals.append(f"🚨 ضغط ائتماني حاد (HYG/TLT={credit_stress:.3f}) → خوف من الإفلاس")
                warnings.append("CREDIT_STRESS_HIGH")
            elif credit_stress > 1.0:
                scores["goldilocks"] += 2
                scores["reflation"] += 1
                signals.append(f"✅ أسواق الائتمان مستقرة (HYG/TLT={credit_stress:.3f})")

        # === 4. تحليل الكماليات/الأساسيات (XLY/XLP) ===
        consumer = intelligence_ratios.get("consumer_strength_ratio")
        if consumer is not None:
            if consumer > 1.5:
                scores["goldilocks"] += 2
                scores["reflation"] += 2
                signals.append(f"🛒 المستهلك قوي (XLY/XLP={consumer:.3f}) → Bullish")
            elif consumer < 1.2:
                scores["recession"] += 2
                scores["stagflation"] += 1
                signals.append(f"💰 المستهلك يشد الحزام (XLY/XLP={consumer:.3f}) → تباطؤ")

        # === 5. تحليل تركز السيولة (NDX/RUT) ===
        concentration = intelligence_ratios.get("liquidity_concentration_ratio")
        if concentration is not None:
            if concentration > 10.0:
                warnings.append("FRAGILE_RALLY")
                signals.append(f"⚡ صعود هش (NDX/RUT={concentration:.2f}) → سيولة مركزة في التكنولوجيا")
            elif concentration < 8.0:
                scores["goldilocks"] += 1
                signals.append(f"✅ صعود صحي (NDX/RUT={concentration:.2f}) → سيولة موزعة")

        # === 6. فحص VIX و MOVE (إنذار أزمة السيولة) ===
        vix_close = None
        if "VIX" in correlation_context:
            vix_close = correlation_context["VIX"].get("close")
        
        if vix_close is not None:
            if vix_close > 35:
                warnings.append("CORRELATION_COLLAPSE_RISK")
                signals.append(f"🔴 VIX={vix_close:.1f} → خطر انهيار الارتباطات → أوقف الخوارزميات")
                scores["recession"] += 2
            elif vix_close > 25:
                signals.append(f"🟡 VIX={vix_close:.1f} → خوف مرتفع")
                scores["recession"] += 1
            elif vix_close < 15:
                scores["goldilocks"] += 1
                signals.append(f"🟢 VIX={vix_close:.1f} → هدوء (Complacency risk)")

        # === 7. فحص فك ارتباط الذهب/الدولار ===
        gold_data = correlation_context.get("GOLD", {})
        dxy_data = correlation_context.get("DXY", {})
        if gold_data and dxy_data:
            gold_close = gold_data.get("close")
            dxy_close = dxy_data.get("close")
            if gold_close and dxy_close:
                # إذا كلاهما فوق المتوسط → فك ارتباط جيوسياسي
                if gold_close > 3000 and dxy_close > 104:
                    warnings.append("GOLD_DXY_DECOUPLING")
                    signals.append("🔔 الذهب والدولار يرتفعان معاً → طلب جيوسياسي/هيكلي")

        # === تحديد النظام الفائز ===
        regime = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = round(scores[regime] / max(total_score, 1) * 100, 1)

        regime_names = {
            "goldilocks": "النمو المستقر (Goldilocks)",
            "stagflation": "التضخم الركودي (Stagflation) ⚠️",
            "recession": "الركود الانكماشي (Recession)",
            "reflation": "الانتعاش التضخمي (Reflation)"
        }

        return {
            "regime": regime,
            "regime_name": regime_names[regime],
            "confidence": confidence,
            "scores": scores,
            "signals": signals,
            "warnings": warnings,
            "halt_algorithms": "CORRELATION_COLLAPSE_RISK" in warnings
        }
