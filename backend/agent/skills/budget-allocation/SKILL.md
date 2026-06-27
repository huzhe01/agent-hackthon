---
name: budget-allocation
description: Allocate livestream advertising budget under total budget, channel ROI estimates, and min/max guardrails using a deterministic linear programming tool.
---

# Budget Allocation

Use this skill when the agent needs to split one budget across channels, live rooms, or SKU groups.

## Workflow

1. Collect `total_budget`, candidate channels, ROI estimates, and min/max guardrails.
2. Call `allocate_budget`.
3. Explain the result in business terms:
   - why high ROI channels receive more budget
   - which caps or minimums are binding
   - expected GMV and ROAS
4. If ROI inputs are missing, call `estimate_ad_performance` first or ask the user for assumptions.

## Notes

- The tool solves a linear objective with box constraints.
- It is deterministic and suitable for demo or planning flows.
