import os
import sys
from loguru import logger

# Add paths for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "alphaear_discovery", "scripts"))

from alpha_prime_executor import AlphaPrimeExecutor
from discovery_tools import DiscoveryTools

REGIME_SECTORS = {
    "Goldilocks": ["Technology", "Consumer Cyclical", "Financial Services"],
    "Stagflation": ["Energy", "Basic Materials", "Utilities"],
    "Recession": ["Healthcare", "Consumer Defensive", "Utilities"],
    "Reflation": ["Energy", "Financial Services", "Industrials"]
}

def run_discovery_workflow():
    print("=" * 60)
    print("🌟 Alpha Prime: Macro-to-Asset Discovery Workflow")
    print("=" * 60)

    # 1. Detect Current Regime (using SPY as proxy)
    print("\n[1] Detecting Current Market Regime...")
    executor = AlphaPrimeExecutor("SPY")
    payload = executor.generate_context_json() # This triggers calculation
    regime_data = executor.payload.get("market_regime", {})
    regime_name = regime_data.get("regime_name", "Unknown")
    confidence = regime_data.get("confidence", 0)

    print(f"✅ Current Regime: {regime_name} (Confidence: {confidence}%)")

    # 2. Identify Target Sectors
    target_sectors = REGIME_SECTORS.get(regime_name, ["Technology"]) # Default to Tech
    print(f"\n[2] Target Sectors for {regime_name}: {', '.join(target_sectors)}")

    # 3. Discover Assets
    print(f"\n[3] Discovering Top Assets in {target_sectors[0]}...")
    dt = DiscoveryTools()
    discovered_assets = []
    try:
        discovered_assets = dt.search_equities(country="United States", sector=target_sectors[0])
    except Exception as e:
        print(f"⚠️ Sector search failed: {e}")
        # Try a more generic query
        discovered_assets = dt.search_equities(query=target_sectors[0])
    
    if not discovered_assets:
        print("⚠️ No assets found. Falling back to default list.")
        discovered_assets = [
            {"ticker": "NVDA", "name": "NVIDIA Corporation"},
            {"ticker": "AAPL", "name": "Apple Inc."},
            {"ticker": "MSFT", "name": "Microsoft Corporation"}
        ]

    print(f"🎯 Top Discovered Assets:")
    for asset in discovered_assets[:5]:
        ticker = asset.get('ticker', 'Unknown')
        name = asset.get('name', 'Unknown')
        print(f"   - {ticker}: {name}")

    # 4. Recommendation
    print("\n" + "=" * 60)
    print("💡 Recommended Action:")
    print(f"Run analysis for the top asset: python alpha_prime_agent.py --asset {discovered_assets[0]['ticker']}")
    print("=" * 60)

if __name__ == "__main__":
    run_discovery_workflow()
