"""
Alpha Prime - Quick Start Example
This script demonstrates how to initialize the orchestrator and generate a summary for Gold.
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.orchestrator import AlphaPrimeExecutor

def main():
    print("🚀 Initializing Alpha Prime Quick Start...")
    asset = "GC=F" # Gold Futures

    # Initialize Orchestrator
    executor = AlphaPrimeExecutor(asset)

    # Fetch Data and Run Analysis
    print(f"📊 Analyzing {asset} across 9 dimensions...")
    context_json = executor.generate_context_json()

    # Simple Output
    import json
    data = json.loads(context_json)

    print("\n" + "="*40)
    print(f"SUMMARY FOR {asset} - {datetime.now().strftime('%Y-%m-%d')}")
    print("="*40)
    print(f"Regime: {data.get('market_regime', {}).get('regime_name')}")
    print(f"DXY Impact: {data.get('intelligence_ratios', {}).get('dxy_gold_impact')}")

    amt = data.get('layer_1_technical', {}).get('amt_structure', {})
    if amt:
        print(f"AMT POC: {amt.get('POC')}")
        print(f"Profile Shape: {amt.get('profile_shape')}")

    print("\n✅ Intelligence gathering complete. Check data/ folder for full JSON.")

if __name__ == "__main__":
    main()
