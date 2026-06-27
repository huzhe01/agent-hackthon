---
name: business-knowledge
description: Search external business information and news through Xiaosu/Cloudsway SmartSearch, store raw knowledge locally, and summarize reusable memory for future agent decisions.
---

# Business Knowledge

Use this skill when the agent needs market context, competitor news, platform trend signals, or historical business memory.

## Workflow

1. Build a precise query from the product, market, platform, and time window.
2. Call `refresh_business_knowledge`.
3. Read `memory.summary` and `memory.signals` before making strategy recommendations.
4. Cite the stored knowledge path when explaining where evidence came from.

## Storage

- Raw results are JSONL files in `backend/agent/knowledge`.
- Condensed memories are JSON files in `backend/agent/memory`.
