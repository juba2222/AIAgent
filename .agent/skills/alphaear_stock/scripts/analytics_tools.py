from financetoolkit import Toolkit
import pandas as pd
from typing import Dict, List, Optional, Union
from loguru import logger
import os

class AnalyticsTools:
    """
    Advanced financial analytics using FinanceToolkit.
    Provides deep insights into fundamentals, risk, and performance.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        self.source = "FinancialModelingPrep" if self.api_key else "YahooFinance"
        if not self.api_key:
            logger.warning("⚠️ No FMP_API_KEY found. Falling back to YahooFinance. Some advanced features may be limited.")

    def _make_json_serializable(self, obj):
        """Recursively convert complex types to strings for JSON serialization."""
        if isinstance(obj, dict):
            return {str(k): self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(i) for i in obj]
        elif hasattr(obj, 'strftime'): # Timestamps
            return obj.strftime('%Y-%m-%d')
        elif hasattr(obj, 'to_timestamp'): # Periods
            return obj.to_timestamp().strftime('%Y-%m-%d')
        elif pd.isna(obj):
            return None
        return obj

    def get_full_analysis(self, ticker: str) -> Dict:
        """
        Perform a comprehensive multi-layered analysis for a ticker.
        """
        try:
            # Initialize Toolkit
            toolkit = Toolkit(
                tickers=[ticker],
                api_key=self.api_key,
                start_date=(pd.Timestamp.now() - pd.DateOffset(years=5)).strftime('%Y-%m-%d')
            )
            
            analysis = {}
            
            # 1. Fundamental Ratios
            logger.info(f"📊 Fetching ratios for {ticker}...")
            analysis['profitability'] = toolkit.ratios.collect_profitability_ratios().tail(1).to_dict()
            analysis['valuation'] = toolkit.ratios.collect_valuation_ratios().tail(1).to_dict()
            analysis['solvency'] = toolkit.ratios.collect_solvency_ratios().tail(1).to_dict()
            
            # 2. Advanced Models
            logger.info(f"🧠 Running models for {ticker}...")
            try:
                analysis['dupont'] = toolkit.models.get_extended_dupont_analysis().tail(1).to_dict()
            except:
                analysis['dupont'] = "N/A"
                
            try:
                analysis['enterprise_value'] = toolkit.models.get_enterprise_value_breakdown().tail(1).to_dict()
            except:
                analysis['enterprise_value'] = "N/A"

            # 3. Risk & Performance
            logger.info(f"⚖️ Calculating risk metrics for {ticker}...")
            try:
                analysis['risk_var'] = toolkit.risk.get_value_at_risk().tail(1).to_dict()
                analysis['sharpe_ratio'] = toolkit.performance.get_sharpe_ratio().tail(1).to_dict()
            except:
                analysis['risk_metrics'] = "N/A"

            # 4. Standardized Financials
            logger.info(f"📑 Fetching standardized financials for {ticker}...")
            analysis['income_statement'] = toolkit.get_income_statement().tail(1).to_dict()
            
            # CRITICAL: Convert to JSON serializable
            return self._make_json_serializable(analysis)
            
        except Exception as e:
            logger.error(f"❌ Error in FinanceToolkit analysis for {ticker}: {e}")
            return {"error": str(e)}

    def get_global_economics(self) -> Dict:
        """
        Fetch global economic indicators (Macro Layer).
        """
        from financetoolkit import Economics
        try:
            economics = Economics(api_key=self.api_key)
            indicators = {
                "cpi": economics.get_consumer_price_index().tail(1).to_dict(),
                "gdp": economics.get_real_gdp_growth().tail(1).to_dict(),
                "unemployment": economics.get_unemployment_rate().tail(1).to_dict()
            }
            return indicators
        except Exception as e:
            logger.error(f"❌ Error fetching economic indicators: {e}")
            return {"error": str(e)}
