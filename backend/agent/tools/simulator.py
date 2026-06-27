"""Tool wrapper around the Agent Mode deterministic simulator."""

from __future__ import annotations

from typing import Any, Dict

try:
    from agent_mode_simulator import build_simulation_bundle, validate_simulation_brief
except ImportError:  # pragma: no cover
    from backend.agent_mode_simulator import build_simulation_bundle, validate_simulation_brief


def simulate_live_workbench(arguments: Dict[str, Any]) -> Dict[str, Any]:
    brief = arguments.get("brief") or {}
    version_number = int(arguments.get("version_number") or 1)
    validation = validate_simulation_brief(brief)
    if not validation["complete"]:
        return {
            "success": False,
            "error": "brief 核心字段不足，无法生成投放模拟。",
            "missing": validation["missing"],
        }
    bundle = build_simulation_bundle(brief, version_number=version_number)
    frames = bundle.get("live_demo", {}).get("frames", [])
    return {
        "success": True,
        "simulator_seed": bundle.get("simulator_seed"),
        "brief": bundle.get("brief"),
        "product_catalog": bundle.get("product_catalog", []),
        "channel_pools": bundle.get("channel_pools", []),
        "plan_options": bundle.get("plan_options", []),
        "frames_count": len(frames),
        "first_frame": frames[0] if frames else None,
        "final_frame": frames[-1] if frames else None,
        "events": bundle.get("managed_events", []),
        "review": bundle.get("review", {}),
    }
