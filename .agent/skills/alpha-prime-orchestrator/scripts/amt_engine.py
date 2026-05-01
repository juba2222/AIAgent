import pandas as pd
import numpy as np

class AMTEngine:
    """
    محرك نظرية المزاد (Auction Market Theory).
    يحسب مستويات القيمة (Value Area) بناءً على توزيع حجم التداول السعري (Volume Profile).
    """

    @staticmethod
    def calculate_value_area(df, value_area_pct=0.70):
        """
        حساب POC, VAH, VAL.
        df يجب أن يحتوي على أعمدة: ['Close', 'Volume']
        """
        if df is None or df.empty:
            return None

        # 1. تحديد نطاق السعر (Price Bins)
        # نستخدم أسعار الإغلاق كمبسّط للبروفايل السعري
        df = df.copy()
        min_p = df['Close'].min()
        max_p = df['Close'].max()
        
        if min_p == max_p:
            return {
                "POC": round(min_p, 4),
                "VAH": round(min_p, 4),
                "VAL": round(min_p, 4)
            }

        # تقسيم النطاق إلى 50 مستوى (Bin)
        bins = np.linspace(min_p, max_p, 50)
        df.loc[:, 'bin'] = pd.cut(df['Close'], bins=bins)
        
        # 2. حساب حجم التداول لكل مستوى
        volume_profile = df.groupby('bin', observed=True)['Volume'].sum()
        
        if volume_profile.empty or volume_profile.sum() == 0:
            return None

        # 3. تحديد POC (نقطة التحكم - السعر صاحب أعلى حجم)
        poc_bin = volume_profile.idxmax()
        poc = (poc_bin.left + poc_bin.right) / 2
        
        # 4. حساب Value Area (VAH & VAL)
        total_volume = volume_profile.sum()
        target_va_volume = total_volume * value_area_pct
        
        # ترتيب المستويات حسب المسافة من الـ POC
        sorted_bins = volume_profile.sort_values(ascending=False)
        
        cumulative_vol = 0
        va_bins = []
        
        for idx, vol in sorted_bins.items():
            cumulative_vol += vol
            va_bins.append(idx)
            if cumulative_vol >= target_va_volume:
                break
        
        # استخراج VAH و VAL من المستويات المختارة
        va_prices = []
        for b in va_bins:
            va_prices.append(b.left)
            va_prices.append(b.right)
            
        vah = max(va_prices)
        val = min(va_prices)
        
        return {
            "POC": round(float(poc), 4),
            "VAH": round(float(vah), 4),
            "VAL": round(float(val), 4)
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
        
        # 1. اليوم الحالي (آخر شمعة يومية أو بيانات اليوم)
        results['current_day'] = AMTEngine.calculate_value_area(df[df.index.date == now.date()])
        
        # 2. اليوم السابق
        unique_dates = sorted(list(set(df.index.date)))
        if len(unique_dates) > 1:
            prev_date = unique_dates[-2]
            results['previous_day'] = AMTEngine.calculate_value_area(df[df.index.date == prev_date])
            
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
