import financedatabase as fd
import pandas as pd

class MetadataEngine:
    """
    محرك استخراج البيانات التعريفية للأصول (FinanceDatabase).
    """

    @staticmethod
    def get_asset_metadata(symbol):
        """
        جلب تصنيف الأصل، القطاع، الصناعة، والدولة.
        """
        try:
            clean_ticker = symbol.upper()

            # محاولة البحث في الأسهم (الفهرس هو الرمز)
            equities = fd.Equities().select()
            if clean_ticker in equities.index:
                info = equities.loc[clean_ticker]
                return {
                    "name": info.get('name', 'N/A'),
                    "sector": info.get('sector', 'N/A'),
                    "industry": info.get('industry', 'N/A'),
                    "country": info.get('country', 'N/A'),
                    "exchange": info.get('exchange', 'N/A'),
                    "type": "Equity"
                }

            # البحث عن أقرب تطابق إذا لم يكن الرمز دقيقاً (بدون لاحقة البورصة)
            matches = equities[equities.index.str.startswith(clean_ticker)]
            if not matches.empty:
                info = matches.iloc[0]
                return {
                    "name": info.get('name', 'N/A'),
                    "sector": info.get('sector', 'N/A'),
                    "industry": info.get('industry', 'N/A'),
                    "country": info.get('country', 'N/A'),
                    "exchange": info.get('exchange', 'N/A'),
                    "type": "Equity"
                }

            return {"symbol": symbol, "type": "Other/Global"}
        except Exception as e:
            return {"error": str(e), "type": "N/A"}

if __name__ == "__main__":
    print(MetadataEngine.get_asset_metadata("NVDA"))
    print(MetadataEngine.get_asset_metadata("MSFT"))
