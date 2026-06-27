---
name: live-simulator
description: Generate deterministic demo data for livestream ad planning and execution when real media or commerce data is unavailable.
---

# Live Simulator

Use this skill when a budget project has enough brief fields but no real channel data.

## Workflow

1. Require budget, target ROAS, product, market, and channels.
2. Call `simulate_live_workbench`.
3. Use returned SKU catalog, channel pools, live frames, events, actions, and review as one consistent data graph.
4. Do not mix hardcoded frontend data with simulator frames.

## Data Relationships

- `GMV = sum(sku.gmv)`
- `ROAS = GMV / spend`
- `profit = GMV - spend`
- `inventory = initial_inventory - units_sold`
