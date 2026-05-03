---
name: alphaear-discovery
description: Discover financial symbols (Equities, ETFs, Crypto) by sector, industry, country, or category. Use when the user asks for "top stocks in X industry", "competitors of Y", or "ETFs related to Z".
---

# AlphaEar Discovery Skill

## Overview

A skill for discovering financial assets using the `FinanceDatabase` library. It allows filtering over 300,000 symbols by qualitative criteria.

## Capabilities

### 1. Symbol Discovery
Use `scripts/discovery_tools.py` via `DiscoveryTools`.

-   **Search Equities**: `search_equities(country, sector, industry, query)`
    -   Find stocks by geographic or business segment.
    -   Returns list of `{ticker, name, sector, industry, country}`.
-   **Search ETFs**: `search_etfs(category, family, query)`
    -   Find ETFs by investment theme or provider.
-   **List Options**: `list_options(asset_type, field)`
    -   Find valid names for sectors, industries, etc.

## Usage Examples

- "Find all US semiconductor stocks."
- "What are some clean energy ETFs?"
- "List all industries available in the UK market."

## Dependencies

- `financedatabase`
- `pandas`
- `loguru`
