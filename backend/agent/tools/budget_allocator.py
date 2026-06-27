"""Linear budget allocation tool.

The objective is linear: maximize sum(roi_i * allocation_i), subject to
total budget and per-channel min/max constraints. With only box constraints,
the optimum is found by allocating minimums first, then filling channels by
descending ROI until each cap is reached.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List


def allocate_budget(arguments: Dict[str, Any]) -> Dict[str, Any]:
    total_budget = round(float(arguments.get("total_budget") or 0))
    channels = arguments.get("channels") or []
    reserve_ratio = max(0.0, min(0.9, float(arguments.get("reserve_ratio") or 0)))
    if total_budget <= 0:
        return {"success": False, "error": "total_budget 必须大于 0"}
    if not channels:
        return {"success": False, "error": "channels 不能为空"}

    spendable_budget = round(total_budget * (1 - reserve_ratio))
    rows = [_normalize_channel(channel, total_budget) for channel in channels]
    minimum_sum = sum(row["min_budget"] for row in rows)
    if minimum_sum > spendable_budget:
        return {
            "success": False,
            "error": "渠道最低预算之和超过可分配预算",
            "minimum_sum": minimum_sum,
            "spendable_budget": spendable_budget,
        }

    allocations = {row["id"]: row["min_budget"] for row in rows}
    remaining = spendable_budget - minimum_sum
    for row in sorted(rows, key=lambda item: item["roi"], reverse=True):
        room = max(0, row["max_budget"] - allocations[row["id"]])
        add = min(remaining, room)
        allocations[row["id"]] += add
        remaining -= add
        if remaining <= 0:
            break

    if remaining > 0:
        # All explicit caps were hit. Put the leftover into the highest-ROI row
        # rather than dropping budget, and mark it as a cap overflow.
        best = max(rows, key=lambda item: item["roi"])
        allocations[best["id"]] += remaining
        remaining = 0

    allocation_rows = []
    expected_gmv = 0.0
    for row in rows:
        amount = round(allocations[row["id"]])
        expected_gmv += amount * row["roi"]
        allocation_rows.append({
            "id": row["id"],
            "label": row["label"],
            "roi": row["roi"],
            "allocated_budget": amount,
            "expected_gmv": round(amount * row["roi"], 2),
            "min_budget": row["min_budget"],
            "max_budget": row["max_budget"],
        })

    # Correct any rounding drift.
    drift = spendable_budget - sum(row["allocated_budget"] for row in allocation_rows)
    if drift:
        best = max(allocation_rows, key=lambda item: item["roi"])
        best["allocated_budget"] += drift
        best["expected_gmv"] = round(best["allocated_budget"] * best["roi"], 2)
        expected_gmv += drift * best["roi"]

    return {
        "success": True,
        "method": "linear_programming_box_constraints_greedy_optimum",
        "objective": "maximize sum(channel_roi * allocated_budget)",
        "total_budget": total_budget,
        "reserve_budget": total_budget - spendable_budget,
        "allocated_budget": spendable_budget,
        "expected_gmv": round(expected_gmv, 2),
        "expected_roas": round(expected_gmv / max(spendable_budget, 1), 2),
        "allocations": allocation_rows,
        "constraints": {
            "total_budget": total_budget,
            "reserve_ratio": reserve_ratio,
            "per_channel_bounds": [
                {"id": row["id"], "min": row["min_budget"], "max": row["max_budget"]}
                for row in rows
            ],
        },
    }


def _normalize_channel(channel: Dict[str, Any], total_budget: int) -> Dict[str, Any]:
    channel_id = str(channel.get("id") or channel.get("label") or "channel").strip()
    roi = max(0.0, float(channel.get("roi") or channel.get("expected_roi") or 0))
    min_budget = round(float(channel.get("min_budget") or 0))
    max_budget = channel.get("max_budget")
    if max_budget is None:
        max_budget = total_budget
    max_budget = max(min_budget, round(float(max_budget)))
    return {
        "id": channel_id,
        "label": str(channel.get("label") or channel_id),
        "roi": roi,
        "min_budget": min_budget,
        "max_budget": max_budget,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Allocate media budget under linear ROI constraints.")
    parser.add_argument("--input", required=True, help="JSON string or path containing total_budget and channels")
    args = parser.parse_args()
    raw = args.input
    try:
        with open(raw, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except OSError:
        payload = json.loads(raw)
    print(json.dumps(allocate_budget(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
