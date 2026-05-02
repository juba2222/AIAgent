---
name: alpha-prime-orchestrator
description: The master orchestrator skill that gathers 7-layers of data (Technical, AMT, Macro, Smart Money, Sentiment, Alt Data, Logistics) and generates a unified JSON payload for the Alpha Prime Intelligence Agent.
---

# Alpha Prime Orchestrator Skill

## Overview
This skill acts as the data aggregator and context injector for the Alpha Prime Agent. It calls other sub-skills (like `alphaear-news`, `alphaear-stock`, `alphaear-sentiment`) and dedicated Python fetchers to collect 7 layers of financial intelligence. It then merges them into a standardized JSON format.

## Capabilities

### 1. Data Aggregation (`alpha_prime_executor.py`)
- Fetches prices and OHLCV for 6 core assets.
- Calculates AMT values (POC, VAH, VAL).
- Fetches Macro/Logistics/Smart Money layers.
- Outputs `alpha_prime_context.json`.

### 2. Prompt Injection
- This skill prepares the data to be injected seamlessly alongside the `agent_system_prompt.md` framework.

## How to use
When asked to perform a full alpha prime analysis on a target asset, the agent should first call this skill's executor script to generate the context JSON, read it, and then apply the analyzing logic mapped out in its system instructions.
