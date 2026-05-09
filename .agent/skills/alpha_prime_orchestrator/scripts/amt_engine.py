import pandas as pd
import numpy as np

class AMTEngine:
    """
    محرك نظرية المزاد (Auction Market Theory).
    يحسب مستويات القيمة (Value Area) بناءً على توزيع حجم التداول السعري (Volume Profile).
    """

    @staticmethod
    def calculate_value_area(df, value_area_pct=0.70, use_tpo=False):
        """
        حساب POC, VAH, VAL.
        إذا كان use_tpo=True، يتم استخدام الوقت المقضي عند السعر بدلاً من الحجم.
        """
        if df is None or df.empty:
            return None

        df = df.copy()
        
        if 'Close' in df.columns:
            close_series = df['Close']
            if isinstance(close_series, pd.DataFrame):
                close_series = close_series.iloc[:, 0]
        else:
            return None

        min_p = close_series.min()
        max_p = close_series.max()
        
        if hasattr(min_p, 'item'): min_p = min_p.item()
        if hasattr(max_p, 'item'): max_p = max_p.item()
        
        if float(min_p) == float(max_p):
            # محاكاة التوزيع في حال توفر نقطة سعرية واحدة (للمحافظة على منطق المزاد)
            volatility_proxy = float(min_p) * 0.001 # 0.1% Range estimation
            return {
                "POC": round(float(min_p), 4),
                "VAH": round(float(min_p + volatility_proxy), 4),
                "VAL": round(float(min_p - volatility_proxy), 4),
                "HVNs": [round(float(min_p), 4)],
                "LVNs": [round(float(min_p + 2 * volatility_proxy), 4)],
                "type": "Simulated/Single-Point"
            }

        bins = np.linspace(min_p, max_p, 50)
        df.loc[:, 'bin'] = pd.cut(close_series, bins=bins)
        
        # Ensure use_tpo is a boolean
        if isinstance(use_tpo, (pd.Series, pd.DataFrame)):
            use_tpo = use_tpo.any()

        # Ensure we have a scalar for volume sum
        vol_sum = df['Volume'].sum() if 'Volume' in df.columns else 0
        if isinstance(vol_sum, (pd.Series, pd.DataFrame)):
            vol_sum = vol_sum.sum() # Sum it up if it's a series

        if use_tpo or 'Volume' not in df.columns or float(vol_sum) == 0:
            # TPO Logic: Count occurrences of price in bins
            profile = df.groupby('bin', observed=True).size()
            profile_type = "TPO"
        else:
            # Volume Logic
            volume_series = df['Volume']
            if isinstance(volume_series, pd.DataFrame):
                volume_series = volume_series.iloc[:, 0]
            profile = df.groupby('bin', observed=True).apply(lambda x: volume_series.loc[x.index].sum())
            profile_type = "Volume"
        
        if profile.empty or profile.sum() == 0:
            return None

        poc_bin = profile.idxmax()
        poc = (poc_bin.left + poc_bin.right) / 2
        
        total_metric = profile.sum()
        target_va_metric = total_metric * value_area_pct
        
        sorted_bins = profile.sort_values(ascending=False)
        
        cumulative_m = 0
        va_bins = []
        
        for idx, val in sorted_bins.items():
            cumulative_m += val
            va_bins.append(idx)
            if cumulative_m >= target_va_metric:
                break
        
        va_prices = []
        for b in va_bins:
            va_prices.append(b.left)
            va_prices.append(b.right)
            
        vah = max(va_prices)
        val = min(va_prices)
        
        # Identify HVNs (top peaks including POC)
        # We ensure they are distinct price levels
        hvn_prices = []
        for idx in sorted_bins.index:
            price = round(float((idx.left + idx.right) / 2), 4)
            if price not in hvn_prices:
                hvn_prices.append(price)
            if len(hvn_prices) >= 3:
                break

        # Identify LVNs (True gaps within the trading range)
        # Filter out bins that are part of HVNs
        lvn_candidates = profile[profile < profile.mean() * 0.5]
        lvn_prices = []
        if not lvn_candidates.empty:
            sorted_lvns = lvn_candidates.sort_values(ascending=True)
            for idx in sorted_lvns.index:
                price = round(float((idx.left + idx.right) / 2), 4)
                if price not in hvn_prices and price not in lvn_prices:
                    lvn_prices.append(price)
                if len(lvn_prices) >= 3:
                    break

        # Fallback if no clear LVNs found
        if not lvn_prices:
            lvn_prices = [round(float((idx.left + idx.right) / 2), 4) for idx in profile.sort_values(ascending=True).index[:3]]

        # Identify Single Prints (Empty bins with 0 volume/time within the distribution)
        single_prints = [round(float((idx.left + idx.right) / 2), 4) for idx in profile[profile == 0].index]

        return {
            "POC": round(float(poc), 4),
            "VAH": round(float(vah), 4),
            "VAL": round(float(val), 4),
            "HVNs": hvn_prices,
            "LVNs": lvn_prices,
            "single_prints": single_prints[:5], # Top 5 voids
            "profile_shape": AMTEngine._detect_profile_shape(profile, poc_bin),
            "type": profile_type
        }

    @staticmethod
    def _detect_profile_shape(profile, poc_bin):
        """
        تحديد شكل البروفايل (P, b, D).
        P-shape: POC in upper half (Short covering)
        b-shape: POC in lower half (Long liquidation)
        D-shape: POC in middle (Balanced)
        """
        try:
            bins = list(profile.index)
            poc_idx = bins.index(poc_bin)
            total_bins = len(bins)

            if poc_idx > total_bins * 0.6:
                return "P-Shape (Bullish/Short Covering)"
            elif poc_idx < total_bins * 0.4:
                return "b-Shape (Bearish/Long Liquidation)"
            else:
                return "D-Shape (Balanced)"
        except:
            return "Indeterminate"

    @staticmethod
    def diagnose_order_flow_patterns(df):
        """
        تشخيص أنماط تدفق الأوامر (محاكاة):
        - Absorption: السعر يتحرك بصعوبة عند مستويات القيمة رغم زيادة التقلب.
        - Aggressive Bubbles: تمدد سعري سريع بعيداً عن القيمة.
        """
        if len(df) < 5:
            return []

        df = df.tail(20).copy()

        # Ensure we work with 1D series
        close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
        high = df['High'].iloc[:, 0] if isinstance(df['High'], pd.DataFrame) else df['High']
        low = df['Low'].iloc[:, 0] if isinstance(df['Low'], pd.DataFrame) else df['Low']
        volume = df['Volume'].iloc[:, 0] if isinstance(df['Volume'], pd.DataFrame) else df['Volume']

        # حساب التذبذب (ATR-like)
        ranges = (high - low).abs()
        avg_range = ranges.mean()
        last_range = ranges.iloc[-1]

        patterns = []

        # 1. Aggressive Bubble detection (Price snap-back risk)
        if last_range > avg_range * 2.5:
            patterns.append("AGGRESSIVE_BUBBLE_DETECTED")

        # 2. Absorption detection (Price stalling at value area)
        # We check if volume is high but range is small (simulated)
        if 'Volume' in df.columns and volume.sum() > 0:
            vol_efficiency = ranges / volume.replace(0, np.nan)
            avg_efficiency = vol_efficiency.iloc[:-1].mean()
            last_efficiency = vol_efficiency.iloc[-1]

            if last_efficiency < avg_efficiency * 0.4:
                patterns.append("ABSORPTION_LIKELY")

        return patterns

    @staticmethod
    def calculate_temporal_nuances(current_day_df, prev_day_levels):
        """
        حساب المستويات الزمنية الحاسمة (Dimension 2):
        - Initial Balance (IB): أول ساعة تداول.
        - Opening Range (OR) Relationship: علاقة الافتتاح بقيمة أمس.
        - Day Type: تشخيص نوع اليوم (Trend/Range).
        """
        if current_day_df.empty:
            return {}

        # 1. Initial Balance (IB) - First 1 hour of the session
        ib_df = current_day_df.iloc[:1] # Since we use 1h data
        if ib_df.empty:
            return {}

        ib_high = float(ib_df['High'].max())
        ib_low = float(ib_df['Low'].min())

        # 2. Opening Range Relationship
        open_price = float(current_day_df.iloc[0]['Open'])
        va_relationship = "Inside Value"
        if prev_day_levels:
            vah = prev_day_levels.get('VAH')
            val = prev_day_levels.get('VAL')
            if vah and val:
                if open_price > vah: va_relationship = "Above Value (Bullish)"
                elif open_price < val: va_relationship = "Below Value (Bearish)"

        # 3. Day Type Diagnosis
        last_close = float(current_day_df.iloc[-1]['Close'])
        day_type = "Normal Variation / Range"
        if last_close > ib_high: day_type = "Potential Trend Day (Up)"
        elif last_close < ib_low: day_type = "Potential Trend Day (Down)"

        return {
            "initial_balance": {"high": ib_high, "low": ib_low, "range": round(ib_high - ib_low, 4)},
            "opening_relationship": va_relationship,
            "day_diagnosis": day_type
        }

    @staticmethod
    def get_timeframe_levels(df):
        """
        تقسيم البيانات وحساب المستويات لـ:
        (اليوم الحالي، الأسبوع الحالي، الشهر الحالي)
        (اليوم السابق، الأسبوع السابق، الشهر السابق)
        """
        if df is None or df.empty:
            return {}

        now = df.index[-1]
        
        # تعريف الفترات
        results = {}
        
        # 1. اليوم السابق (نحتاجه أولاً للمقارنة)
        unique_dates = sorted(list(set(df.index.date)))
        prev_day_levels = None
        if len(unique_dates) > 1:
            prev_date = unique_dates[-2]
            prev_day_levels = AMTEngine.calculate_value_area(df[df.index.date == prev_date])
            results['previous_day'] = prev_day_levels

        # 2. اليوم الحالي
        current_day_df = df[df.index.date == now.date()]
        results['current_day'] = AMTEngine.calculate_value_area(current_day_df)

        # إضافة المستويات الزمنية الحاسمة
        results['temporal_nuances'] = AMTEngine.calculate_temporal_nuances(current_day_df, prev_day_levels)
            
        # 3. الأسبوع الحالي
        current_week_start = now - pd.Timedelta(days=now.weekday())
        results['current_week'] = AMTEngine.calculate_value_area(df[df.index >= current_week_start.normalize()])
        
        # 4. الأسبوع السابق
        prev_week_start = current_week_start - pd.Timedelta(days=7)
        results['previous_week'] = AMTEngine.calculate_value_area(
            df[(df.index >= prev_week_start.normalize()) & (df.index < current_week_start.normalize())]
        )
        
        # 5. الشهر الحالي
        current_month_start = now.replace(day=1)
        results['current_month'] = AMTEngine.calculate_value_area(df[df.index >= current_month_start.normalize()])
        
        # 6. الشهر السابق
        prev_month_end = current_month_start - pd.Timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        results['previous_month'] = AMTEngine.calculate_value_area(
            df[(df.index >= prev_month_start.normalize()) & (df.index < current_month_start.normalize())]
        )
        
        return results

    @staticmethod
    def detect_divergence(asset_a_prices, asset_b_prices):
        """
        كشف الانحراف السعري (Divergence) بين أصلين.
        مثلاً: الذهب يرتفع والدولار يرتفع (انحراف كلاسيكي).
        """
        # سيتم تطوير منطق مقارنة معامل الارتباط والتباعد هنا لاحقاً
        pass
