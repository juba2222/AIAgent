import financedatabase as fd
import pandas as pd
from loguru import logger

class DiscoveryTools:
    """
    Tools for discovering financial assets using FinanceDatabase.
    """
    def __init__(self):
        self.equities = fd.Equities()
        self.etfs = fd.ETFs()
        self.cryptos = fd.Cryptos()
        self.currencies = fd.Currencies()

    def list_options(self, asset_type='equities', field='sector', country=None):
        """
        List available options for a field (sector, industry, etc.)
        """
        try:
            if asset_type.lower() == 'equities':
                return list(self.equities.options(field, country=country))
            elif asset_type.lower() == 'etfs':
                return list(self.etfs.options(field))
            return []
        except Exception as e:
            logger.error(f"Error listing options: {e}")
            return []

    def search_equities(self, country=None, sector=None, industry=None, query=None):
        """
        Filter equities by country, sector, industry, or search query.
        """
        try:
            if query:
                results = self.equities.search(country=country, sector=sector, industry=industry, summary=query)
            else:
                results = self.equities.select(country=country, sector=sector, industry=industry)
            
            if results.empty:
                return []
            
            # Format results for the agent
            formatted = []
            for ticker, row in results.iterrows():
                formatted.append({
                    "ticker": ticker,
                    "name": row.get('name', 'N/A'),
                    "sector": row.get('sector', 'N/A'),
                    "industry": row.get('industry', 'N/A'),
                    "country": row.get('country', 'N/A')
                })
            return formatted
        except Exception as e:
            logger.error(f"Error searching equities: {e}")
            return []

    def search_etfs(self, category=None, family=None, query=None):
        """
        Filter ETFs by category, family, or search query.
        """
        try:
            if query:
                results = self.etfs.search(category=category, family=family, summary=query)
            else:
                results = self.etfs.select(category=category, family=family)
            
            if results.empty:
                return []
            
            formatted = []
            for ticker, row in results.iterrows():
                formatted.append({
                    "ticker": ticker,
                    "name": row.get('name', 'N/A'),
                    "family": row.get('family', 'N/A'),
                    "category": row.get('category', 'N/A')
                })
            return formatted
        except Exception as e:
            logger.error(f"Error searching ETFs: {e}")
            return []

if __name__ == "__main__":
    # Simple CLI test
    discovery = DiscoveryTools()
    print("Example: US Semiconductors")
    print(discovery.search_equities(country="United States", industry="Semiconductors")[:5])
