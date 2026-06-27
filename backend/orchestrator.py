"""
MaiDeal Orchestrator — Multi-Agent 编排引擎（投放前）
=====================================================
Orchestrator 是唯一面向用户的 Agent。它通过 tool calling 逐步提取 Brief、
调度 Planning Agent 生成三案，并通过 workbench_patch SSE 事件驱动前端画布。

Planning Agent 当前为 mock 实现，后续替换为独立 tool。
"""

import json
import os
import re
import time
from copy import deepcopy
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

try:
    from agent_mode_store import (
        get_brief_completion,
        patch_workbench,
        read_workbench,
    )
except ImportError:
    from backend.agent_mode_store import (
        get_brief_completion,
        patch_workbench,
        read_workbench,
    )

# ---------------------------------------------------------------------------
# LLM config (reuse from api.py pattern)
# ---------------------------------------------------------------------------

QIJI_DEFAULT_BASE_URL = "https://api.openai-next.com/v1"
QIJI_DEFAULT_MODEL = "gpt-5"


def _get_llm_config() -> Dict[str, str]:
    return {
        "api_base": os.getenv("QIJI_BASE_URL") or QIJI_DEFAULT_BASE_URL,
        "api_key": os.getenv("QIJI_API_KEY") or os.getenv("LLM_API_KEY") or "",
        "model": os.getenv("QIJI_MODEL") or QIJI_DEFAULT_MODEL,
    }


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse(event: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


# ---------------------------------------------------------------------------
# Orchestrator system prompt
# ---------------------------------------------------------------------------

ORCHESTRATOR_SYSTEM_PROMPT = """你是 MaiDeal 出海直播投放调度中心。你是用户唯一的入口 Agent，负责：
1. 通过自然语言对话理解用户的经营目标
2. 逐步提取投放项目 Brief 所需的关键字段
3. 当信息齐全时，调度 Planning Agent 生成保守/均衡/进取三套方案
4. 帮助用户修改方案参数
5. 确认方案并授权上线
6. 投放中持续执行策略闭环：Analysis 识别变化并归因 → Planning 生成预算/人群调整策略 → Orchestrator 校验护栏 → Delivery 执行或等待审批 → Analysis 验证效果

## Brief 必需字段
- budget: 投放总预算（美元）
- target_roas: 目标 ROAS
- products: 投放商品名称
- market: 目标市场（如"美国 / USD"）
- channels: 投放渠道（如"TikTok + Meta"）
- live_window: 直播时间窗口（如"20:00-23:00"）
- inventory: 库存数量
- margin: 毛利率

## 工作流程
1. 用户每说一段话，立即调用 extract_brief 提取其中包含的字段
2. 检查还缺哪些字段，用自然、友好的方式追问
3. 当核心字段（budget, target_roas, products, market, channels）齐全时，调用 generate_plans
4. 用户要求修改方案时，调用 update_plan
5. 用户确认方案时，调用 confirm_and_launch
6. 用户要求切换视图时，调用 switch_view
7. 当前阶段为 live，用户说"巡检一下""跑一轮投中优化""持续策略闭环"时调用 run_live_iteration
8. 用户说"模拟高风险""超过审批阈值"时调用 run_live_iteration，并传 scenario=high_risk
9. live_loop 存在 pending_action 时，用户说"批准""执行"调用 approve_live_action；用户说"拒绝""重算"调用 reject_live_action

## 回复规范
- 使用中文
- 简洁专业，不要冗长
- 提取到信息后用简短确认（如"✓ 已记录预算 $5,000 和目标 ROAS 3.0"）
- 追问时一次不超过 2-3 个字段，优先问最关键的"""


# ---------------------------------------------------------------------------
# Orchestrator tools (OpenAI function-calling format)
# ---------------------------------------------------------------------------

ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extract_brief",
            "description": "从用户对话中提取项目 Brief 字段。每当用户提供了预算、目标、渠道等经营信息时调用。只传入用户本轮提到的字段，未提及的不传。",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget": {"type": "number", "description": "投放总预算（美元）"},
                    "target_roas": {"type": "number", "description": "目标 ROAS"},
                    "channels": {"type": "string", "description": "投放渠道，如 'TikTok + Meta'"},
                    "products": {"type": "string", "description": "投放商品名称"},
                    "market": {"type": "string", "description": "目标市场，如 '美国 / USD'"},
                    "live_window": {"type": "string", "description": "直播时间窗口，如 '20:00-23:00'"},
                    "inventory": {"type": "string", "description": "库存数量，如 '1200 件'"},
                    "margin": {"type": "string", "description": "毛利率，如 '55%'"},
                    "constraints": {"type": "string", "description": "其他约束条件"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_plans",
            "description": "当 Brief 核心字段（budget, target_roas, products, market, channels）齐全时调用，生成保守/均衡/进取三套投放方案。",
            "parameters": {
                "type": "object",
                "properties": {
                    "brief_summary": {
                        "type": "string",
                        "description": "已收集的完整 Brief 摘要，包含所有已知字段",
                    },
                },
                "required": ["brief_summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_plan",
            "description": "用户通过对话要求修改方案参数时调用（如调整渠道比例、预算分配）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "modification": {"type": "string", "description": "用户的修改要求"},
                    "affected_plan": {
                        "type": "string",
                        "description": "受影响的方案 ID (steady/balanced/aggressive) 或 'all'",
                    },
                },
                "required": ["modification"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_and_launch",
            "description": "用户确认方案并授权上线时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "selected_plan": {
                        "type": "string",
                        "enum": ["steady", "balanced", "aggressive"],
                        "description": "用户选择的方案",
                    },
                    "guard_limit": {
                        "type": "number",
                        "description": "自动调仓上限百分比，默认 15",
                    },
                    "approval_threshold": {
                        "type": "number",
                        "description": "审批金额阈值（美元），默认 800",
                    },
                },
                "required": ["selected_plan"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "switch_view",
            "description": "切换中央工作台视图。当用户说'调出托管后台''查看线索''查看复盘'时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "view": {
                        "type": "string",
                        "enum": ["plan", "live", "leads", "review"],
                        "description": "目标视图",
                    },
                },
                "required": ["view"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_live_iteration",
            "description": "投放中运行一轮持续策略与执行闭环：识别变化、归因、生成预算/人群调整、校验护栏，并自动执行或生成待审批动作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "string",
                        "enum": ["auto", "high_risk"],
                        "description": "auto 表示护栏内自动执行；high_risk 表示模拟超过护栏或审批阈值的动作。",
                    },
                    "observation_window": {
                        "type": "string",
                        "description": "观察窗口，如最近 10 分钟。",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approve_live_action",
            "description": "用户批准当前待审批投中动作后调用，Delivery 执行并进入效果验证。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_id": {"type": "string", "description": "待审批动作 ID，可省略以使用当前 pending_action。"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reject_live_action",
            "description": "用户拒绝当前待审批投中动作后调用，回写约束并让 Planning 生成保守替代策略。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_id": {"type": "string", "description": "待审批动作 ID，可省略以使用当前 pending_action。"},
                    "reason": {"type": "string", "description": "用户拒绝原因或新增约束。"},
                },
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

BRIEF_FIELD_LABELS = {
    "budget": "投放总预算",
    "target_roas": "目标 ROAS",
    "channels": "投放渠道",
    "products": "投放商品",
    "market": "目标市场",
    "live_window": "直播时间",
    "inventory": "库存",
    "margin": "毛利率",
    "constraints": "约束条件",
}

CORE_FIELDS = {"budget", "target_roas", "products", "market", "channels"}
BRIEF_ALL_FIELDS = CORE_FIELDS | {"live_window", "inventory", "margin", "constraints"}


def _handle_extract_brief(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Process extract_brief tool call. Returns (tool_result, sse_events)."""
    events = []

    extracted = {k: v for k, v in arguments.items() if v is not None}
    if not extracted:
        return {"success": True, "message": "没有新字段被提取"}, events

    brief_patch = {}
    project_patch = {}
    for key, value in extracted.items():
        brief_patch[key] = value
        if key == "budget":
            project_patch["totalBudget"] = f"${value:,.0f}"
            project_patch["totalBudgetValue"] = value
        elif key == "target_roas":
            project_patch["targetRoas"] = str(value)
        elif key == "channels":
            project_patch["channels"] = value
        elif key == "products":
            project_patch["product"] = value
        elif key == "market":
            project_patch["market"] = value
        elif key == "live_window":
            project_patch["liveWindow"] = value
        elif key == "inventory":
            project_patch["inventory"] = value
        elif key == "margin":
            project_patch["margin"] = value

    wb_patch: Dict[str, Any] = {"brief_fields": brief_patch}
    if project_patch:
        wb_patch["project"] = project_patch

    patch_workbench(wb_patch)

    events.append({"type": "workbench_patch", "patch": wb_patch})

    filled_labels = [BRIEF_FIELD_LABELS.get(k, k) for k in extracted]
    action_text = f"已收集：{'、'.join(filled_labels)}"
    agent_event = {"role": "调度中心", "content": action_text, "agent": True}
    events.append({"type": "agent_action", "event": agent_event})
    patch_workbench({"left_timeline": read_workbench().get("left_timeline", []) + [agent_event]})

    roster_patch = _roster_patch("orchestrator", "提取中")
    patch_workbench({"agent_roster": roster_patch})
    events.append({"type": "workbench_patch", "patch": {"agent_roster": roster_patch}})

    completion = get_brief_completion()
    result = {
        "success": True,
        "extracted": extracted,
        "brief_status": completion,
    }
    if completion["complete"]:
        result["hint"] = "所有核心字段已齐全，请立即调用 generate_plans 生成三套方案。"
        result["message"] = "核心字段已齐全，我将生成三套投放方案。"
    else:
        missing_labels = [BRIEF_FIELD_LABELS.get(f, f) for f in completion["missing"] if f in CORE_FIELDS]
        if missing_labels:
            result["hint"] = f"还缺少核心字段：{'、'.join(missing_labels)}，请继续追问用户。"
            result["message"] = _brief_followup_message(completion)
    return result, events


def _handle_generate_plans(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Generate 3 plans (mock). Returns (tool_result, sse_events)."""
    events = []
    wb = read_workbench()
    brief = wb.get("brief_fields", {})
    budget = _as_float(brief.get("budget"), 5000)
    target_roas = _as_float(brief.get("target_roas"), 3.0)
    channels = brief.get("channels", "TikTok + Meta")
    products = brief.get("products", "商品")
    market = brief.get("market", "美国 / USD")
    inventory = brief.get("inventory", "1000 件")
    margin = brief.get("margin", "50%")
    live_window = brief.get("live_window", "20:00-23:00")
    meta_cap = _extract_meta_cap(brief.get("constraints"))
    steady_meta = min(30, meta_cap) if meta_cap else 30
    balanced_meta = min(50, meta_cap) if meta_cap else 50
    aggressive_meta = min(60, meta_cap) if meta_cap else 60
    steady_tiktok = 100 - steady_meta
    balanced_tiktok = 100 - balanced_meta
    aggressive_tiktok = 100 - aggressive_meta

    plan_options = [
        {
            "id": "steady",
            "title": "保守",
            "lines": [
                f"TikTok {steady_tiktok}% / Meta {steady_meta}%",
                "节奏：匀速投放，优先稳定消耗",
                f"预期 ROAS {target_roas * 0.85:.1f}-{target_roas * 0.95:.1f}",
                "回撤风险低，增长偏慢",
            ],
            "channels_split": {"tiktok": steady_tiktok, "meta": steady_meta},
            "budget": budget,
            "expected_roas": f"{target_roas * 0.85:.1f}-{target_roas * 0.95:.1f}",
            "rhythm": "匀速投放",
            "risks": "增长偏慢，可能消耗不完预算",
        },
        {
            "id": "balanced",
            "title": "均衡",
            "recommended": True,
            "lines": [
                f"TikTok {balanced_tiktok}% / Meta {balanced_meta}%",
                "节奏：前段试探后段加码",
                f"预期 ROAS {target_roas * 0.95:.1f}-{target_roas * 1.1:.1f}",
                "风险中等，推荐" if not meta_cap else f"风险中等，Meta 遵守 ≤{meta_cap}% 上限",
            ],
            "channels_split": {"tiktok": balanced_tiktok, "meta": balanced_meta},
            "budget": budget,
            "expected_roas": f"{target_roas * 0.95:.1f}-{target_roas * 1.1:.1f}",
            "rhythm": "前段试探后段加码",
            "risks": "风险中等",
        },
        {
            "id": "aggressive",
            "title": "进取",
            "lines": [
                f"TikTok {aggressive_tiktok}% / Meta {aggressive_meta}%",
                "节奏：高峰激进抢量",
                f"预期 ROAS {target_roas * 1.0:.1f}-{target_roas * 1.3:.1f}",
                "波动较大，可能超 CPA" if not meta_cap else f"受 Meta ≤{meta_cap}% 护栏约束，进取幅度下调",
            ],
            "channels_split": {"tiktok": aggressive_tiktok, "meta": aggressive_meta},
            "budget": budget,
            "expected_roas": f"{target_roas * 1.0:.1f}-{target_roas * 1.3:.1f}",
            "rhythm": "高峰激进抢量",
            "risks": "波动较大，可能超 CPA 约束",
        },
    ]

    live_rooms = _generate_live_rooms(budget, channels, products, market, meta_cap)
    plan_versions = _append_plan_version(
        wb.get("plan_versions", []),
        products=products,
        market=market,
        budget=budget,
        target_roas=target_roas,
        meta_cap=meta_cap,
    )

    wb_patch = {
        "phase": "planning",
        "plan_options": plan_options,
        "plan_versions": plan_versions,
        "live_rooms": live_rooms,
        "brief_complete": True,
        "project": {
            "name": f"{products} · {market.split('/')[0].strip()}直播",
        },
    }
    patch_workbench(wb_patch)

    events.append({"type": "workbench_patch", "patch": wb_patch})
    events.append({"type": "phase_change", "phase": "planning"})

    agent_event = {"role": "方案规划", "content": "已生成保守、均衡、进取三套方案，请选择或修改。", "agent": True}
    events.append({"type": "agent_action", "event": agent_event})
    patch_workbench({"left_timeline": read_workbench().get("left_timeline", []) + [agent_event]})

    roster_patch = _roster_patch("planning", "方案已生成")
    roster_patch.update(_roster_patch("orchestrator", "等待选择"))
    patch_workbench({"agent_roster": roster_patch})
    events.append({"type": "workbench_patch", "patch": {"agent_roster": roster_patch}})

    return {
        "success": True,
        "plans_count": 3,
        "message": "三套方案已生成。请向用户展示方案概要，并询问选择哪套或是否需要调整。",
    }, events


def _handle_update_plan(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Handle plan modification request (mock). Returns (tool_result, sse_events)."""
    events = []
    modification = arguments.get("modification", "")
    affected = arguments.get("affected_plan", "all")
    wb = read_workbench()
    current_plans = wb.get("plan_options", [])

    agent_event = {"role": "方案规划", "content": f"正在根据要求调整方案：{modification}", "agent": True}
    events.append({"type": "agent_action", "event": agent_event})
    patch_workbench({"left_timeline": wb.get("left_timeline", []) + [agent_event]})

    return {
        "success": True,
        "message": f"方案调整已应用：{modification}。当前为 mock 实现，后续接入真实模型 tool。",
        "affected_plan": affected,
    }, events


def _handle_confirm_and_launch(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Confirm plan and switch to live phase. Returns (tool_result, sse_events)."""
    events = []
    selected = arguments.get("selected_plan", "balanced")
    guard_limit = arguments.get("guard_limit", 15)
    approval_threshold = arguments.get("approval_threshold", 800)

    wb_patch = {
        "phase": "live",
        "selected_plan": selected,
        "guard_limit": str(guard_limit),
        "approval_threshold": str(approval_threshold),
    }
    patch_workbench(wb_patch)

    events.append({"type": "workbench_patch", "patch": wb_patch})
    events.append({"type": "phase_change", "phase": "live"})
    events.append({"type": "view_switch", "view": "live"})

    agent_event = {
        "role": "调度中心",
        "content": f"已确认「{_plan_title(selected)}」方案并上线，护栏：自动调仓 ≤{guard_limit}%，审批阈值 ${approval_threshold}。",
        "agent": True,
    }
    events.append({"type": "agent_action", "event": agent_event})
    patch_workbench({"left_timeline": read_workbench().get("left_timeline", []) + [agent_event]})

    roster_patch = _roster_patch("orchestrator", "托管中")
    roster_patch.update(_roster_patch("delivery", "执行中"))
    roster_patch.update(_roster_patch("analysis", "监控中"))
    roster_patch.update(_roster_patch("signal", "采集中"))
    patch_workbench({"agent_roster": roster_patch})
    events.append({"type": "workbench_patch", "patch": {"agent_roster": roster_patch}})

    return {
        "success": True,
        "selected_plan": selected,
        "guard_limit": guard_limit,
        "approval_threshold": approval_threshold,
        "message": "方案已上线。告知用户已进入直播托管阶段。",
    }, events


def _handle_switch_view(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Switch center view. Returns (tool_result, sse_events)."""
    view = arguments.get("view", "plan")
    return (
        {"success": True, "view": view},
        [{"type": "view_switch", "view": view}],
    )


def _handle_extract_and_generate_plans(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Deterministically update brief fields and generate plans when possible."""
    text = arguments.get("text") or ""
    wb = read_workbench()
    extracted = _extract_brief_from_text(text, wb)
    effective = _effective_brief_fields(wb)
    merged = {**effective, **extracted}
    fields_to_patch = {
        key: value
        for key, value in merged.items()
        if key in BRIEF_ALL_FIELDS and value not in (None, "")
    }

    events: List[Dict[str, Any]] = []
    extract_result: Dict[str, Any] = {
        "success": True,
        "extracted": {},
        "brief_status": get_brief_completion(),
    }
    if fields_to_patch:
        extract_result, extract_events = _handle_extract_brief(fields_to_patch)
        events.extend(extract_events)

    completion = get_brief_completion()
    if completion.get("complete"):
        plan_result, plan_events = _handle_generate_plans({
            "brief_summary": _brief_summary(read_workbench()),
        })
        events.extend(plan_events)
        return {
            "success": True,
            "mode": "generated",
            "extracted": extracted,
            "message": "已根据最新预算和约束重新生成三套方案。",
            "plan_result": plan_result,
        }, events

    message = _brief_followup_message(completion)
    return {
        "success": True,
        "mode": "awaiting_fields",
        "extracted": extract_result.get("extracted", extracted),
        "brief_status": completion,
        "message": message,
    }, events


def _handle_run_live_iteration(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Run one simulated live-loop iteration."""
    scenario = arguments.get("scenario") or "auto"
    observation_window = arguments.get("observation_window") or "最近 10 分钟"
    wb = read_workbench()
    action = _build_live_action(wb, scenario, observation_window)
    requires_approval = action["requires_approval"]
    status = "pending_approval" if requires_approval else "completed"
    mode = "pending_approval" if requires_approval else "auto_executed"

    live_loop = {
        "status": status,
        "steps": _live_loop_steps(action, mode),
        "pending_action": action if requires_approval else None,
        "last_action": None if requires_approval else {**action, "status": "executed"},
        "verification": None if requires_approval else _verification_result(action),
    }

    managed_events = wb.get("managed_events", []) + _live_iteration_events(action, mode)
    wb_patch: Dict[str, Any] = {
        "phase": "live",
        "live_loop": live_loop,
        "managed_events": managed_events,
    }
    if not requires_approval:
        wb_patch["live_rooms"] = _apply_live_action_to_rooms(wb.get("live_rooms", []), action)

    roster_patch = _live_roster_patch(mode)
    wb_patch["agent_roster"] = roster_patch
    patch_workbench(wb_patch)

    events = [
        {"type": "workbench_patch", "patch": wb_patch},
        {"type": "phase_change", "phase": "live"},
        {"type": "view_switch", "view": "live"},
    ]
    agent_event = {
        "role": "调度中心",
        "content": "投中巡检已完成：动作已进入审批。" if requires_approval else "投中巡检已完成：护栏内动作已自动执行并开始验证。",
        "agent": True,
    }
    events.append({"type": "agent_action", "event": agent_event})
    patch_workbench({"left_timeline": read_workbench().get("left_timeline", []) + [agent_event]})

    return {
        "success": True,
        "mode": mode,
        "live_loop_status": status,
        "pending_action": action if requires_approval else None,
        "message": "已完成一轮投中持续策略闭环。",
    }, events


def _handle_approve_live_action(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Approve and execute the current pending live action."""
    wb = read_workbench()
    live_loop = deepcopy(wb.get("live_loop") or {})
    pending = live_loop.get("pending_action")
    if not pending:
        return {"success": False, "error": "当前没有待审批动作。"}, []

    action_id = arguments.get("action_id")
    if action_id and action_id != pending.get("id"):
        return {"success": False, "error": "待审批动作 ID 不匹配。"}, []

    action = {**pending, "status": "executed"}
    next_loop = {
        **live_loop,
        "status": "completed",
        "steps": _live_loop_steps(action, "approved_executed"),
        "pending_action": None,
        "last_action": action,
        "verification": _verification_result(action, approved=True),
    }
    managed_events = wb.get("managed_events", []) + [
        _managed_event("投放执行", f"用户批准执行：${action['amount']} {action['source']} → {action['target']}。", "violet"),
        _managed_event("效果分析", "验证窗口回写：转化率改善，动作保留并写入经验。", "emerald"),
    ]
    wb_patch = {
        "phase": "live",
        "live_loop": next_loop,
        "live_rooms": _apply_live_action_to_rooms(wb.get("live_rooms", []), action),
        "managed_events": managed_events,
        "agent_roster": _live_roster_patch("approved_executed"),
    }
    patch_workbench(wb_patch)

    agent_event = {
        "role": "调度中心",
        "content": "已批准并执行待审批动作，Analysis 正在验证效果。",
        "agent": True,
    }
    patch_workbench({"left_timeline": read_workbench().get("left_timeline", []) + [agent_event]})

    return {
        "success": True,
        "status": "completed",
        "message": "待审批动作已执行并完成效果验证。",
    }, [
        {"type": "workbench_patch", "patch": wb_patch},
        {"type": "view_switch", "view": "live"},
        {"type": "agent_action", "event": agent_event},
    ]


def _handle_reject_live_action(arguments: Dict[str, Any]) -> tuple[Dict, list]:
    """Reject the current pending live action and record a conservative replan."""
    wb = read_workbench()
    live_loop = deepcopy(wb.get("live_loop") or {})
    pending = live_loop.get("pending_action")
    if not pending:
        return {"success": False, "error": "当前没有待审批动作。"}, []

    action_id = arguments.get("action_id")
    if action_id and action_id != pending.get("id"):
        return {"success": False, "error": "待审批动作 ID 不匹配。"}, []

    reason = arguments.get("reason") or "用户拒绝高风险动作"
    action = {**pending, "status": "rejected", "rejection_reason": reason}
    next_loop = {
        **live_loop,
        "status": "rejected",
        "steps": _rejected_live_loop_steps(action),
        "pending_action": None,
        "last_action": action,
        "verification": None,
    }
    managed_events = wb.get("managed_events", []) + [
        _managed_event("调度中心", f"已拒绝：${action['amount']} {action['source']} → {action['target']}。原因：{reason}", "amber"),
        _managed_event("方案规划", "已生成保守替代策略：仅暂停低效素材，不追加预算。", "indigo"),
    ]
    wb_patch = {
        "phase": "live",
        "live_loop": next_loop,
        "managed_events": managed_events,
        "agent_roster": _live_roster_patch("rejected"),
    }
    patch_workbench(wb_patch)

    agent_event = {
        "role": "方案规划",
        "content": "高风险动作已拒绝，已回写约束并生成保守替代策略。",
        "agent": True,
    }
    patch_workbench({"left_timeline": read_workbench().get("left_timeline", []) + [agent_event]})

    return {
        "success": True,
        "status": "rejected",
        "message": "动作已拒绝，Planning 已生成保守替代策略。",
    }, [
        {"type": "workbench_patch", "patch": wb_patch},
        {"type": "view_switch", "view": "live"},
        {"type": "agent_action", "event": agent_event},
    ]


TOOL_HANDLERS = {
    "extract_brief": _handle_extract_brief,
    "generate_plans": _handle_generate_plans,
    "update_plan": _handle_update_plan,
    "confirm_and_launch": _handle_confirm_and_launch,
    "switch_view": _handle_switch_view,
    "extract_and_generate_plans": _handle_extract_and_generate_plans,
    "run_live_iteration": _handle_run_live_iteration,
    "approve_live_action": _handle_approve_live_action,
    "reject_live_action": _handle_reject_live_action,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plan_title(plan_id: str) -> str:
    return {"steady": "保守", "balanced": "均衡", "aggressive": "进取"}.get(plan_id, plan_id)


def _roster_patch(agent_id: str, status: str) -> Dict:
    """Build a minimal roster patch keyed by agent_id."""
    return {agent_id: {"status": status}}


def _generate_live_rooms(budget: float, channels: str, products: str, market: str, meta_cap: Optional[int] = None) -> list:
    b1 = round(budget * 0.35)
    b2 = round(budget * 0.40)
    b3 = budget - b1 - b2
    creator_meta = min(30, meta_cap) if meta_cap else 30
    brand_meta = min(50, meta_cap) if meta_cap else 50
    clearance_meta = min(60, meta_cap) if meta_cap else 60
    return [
        {
            "id": "creator",
            "name": "直播间 A · 达人实测",
            "market": "TikTok Shop " + market.split("/")[0].strip(),
            "role": "前段种草与人群蓄水",
            "budget": b1,
            "spent": 0,
            "roas": "待启动",
            "channel": f"TikTok {100 - creator_meta}% / Meta {creator_meta}%",
            "risk": "低风险",
            "status": "待启动",
        },
        {
            "id": "brand",
            "name": "直播间 B · 品牌自播",
            "market": channels,
            "role": "高峰成交主承接",
            "budget": b2,
            "spent": 0,
            "roas": "待启动",
            "channel": f"TikTok {100 - brand_meta}% / Meta {brand_meta}%",
            "risk": "推荐均衡",
            "status": "待启动",
            "recommended": True,
        },
        {
            "id": "clearance",
            "name": "直播间 C · 清仓冲量",
            "market": "Meta Reels",
            "role": "库存释放与尾场冲量",
            "budget": b3,
            "spent": 0,
            "roas": "待启动",
            "channel": f"TikTok {100 - clearance_meta}% / Meta {clearance_meta}%",
            "risk": "高波动",
            "status": "待启动",
        },
    ]


def _append_plan_version(
    existing_versions: List[Dict[str, Any]],
    *,
    products: str,
    market: str,
    budget: float,
    target_roas: float,
    meta_cap: Optional[int],
) -> List[Dict[str, Any]]:
    """Create a new immutable plan version and mark older versions inactive."""
    next_index = len(existing_versions or []) + 1
    summary_parts = [
        f"{products} · {market}",
        f"预算 ${budget:,.0f}",
        f"目标 ROAS {target_roas:g}",
    ]
    if meta_cap:
        summary_parts.append(f"Meta ≤{meta_cap}%")
    inactive_versions = [{**version, "active": False} for version in (existing_versions or [])]
    return inactive_versions + [{
        "id": f"plan-v{next_index}-{int(time.time() * 1000)}",
        "label": f"Plan v{next_index}",
        "created_at": _clock_label(),
        "summary": "，".join(summary_parts),
        "plan_ids": ["steady", "balanced", "aggressive"],
        "active": True,
    }]


def _parse_number(raw: str) -> Optional[float]:
    try:
        return float(str(raw).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _extract_meta_cap(text: Any) -> Optional[int]:
    match = re.search(r"Meta\s*(?:最多|最高|上限|不超过|<=|≤)?\s*(?:占)?\s*(\d{1,3})\s*%", str(text or ""), re.I)
    if not match:
        return None
    value = int(match.group(1))
    return value if 0 < value <= 100 else None


def _extract_brief_from_text(text: str, workbench: Dict[str, Any]) -> Dict[str, Any]:
    """Small deterministic extractor for common workbench commands."""
    source = text or ""
    extracted: Dict[str, Any] = {}

    budget_match = re.search(r"(?:预算|总预算|budget)[^\d]{0,12}([\d,]+(?:\.\d+)?)", source, re.I)
    if not budget_match:
        budget_match = re.search(r"([\d,]+(?:\.\d+)?)\s*(?:美元|美金|USD|usd|\$)", source)
    if budget_match:
        budget = _parse_number(budget_match.group(1))
        if budget is not None:
            extracted["budget"] = int(budget) if budget.is_integer() else budget

    roas_match = re.search(r"ROAS[^\d]{0,8}(\d+(?:\.\d+)?)", source, re.I)
    if roas_match:
        roas = _parse_number(roas_match.group(1))
        if roas is not None:
            extracted["target_roas"] = roas

    product_match = re.search(r"给\s*([^，,。]{1,30}?)\s*(?:做|投放|推广)", source)
    if product_match:
        product = product_match.group(1).strip("「」[] ")
        if product and "直播" not in product:
            extracted["products"] = product

    if "美国" in source or re.search(r"\bUS\b|\bUSA\b", source, re.I):
        extracted["market"] = "美国 / USD"

    meta_cap = _extract_meta_cap(source)
    if meta_cap:
        extracted["constraints"] = f"Meta 最多占 {meta_cap}%"
        extracted["channels"] = "TikTok + Meta"
    elif "TikTok" in source and "Meta" in source:
        extracted["channels"] = "TikTok + Meta"
    elif "Meta" in source:
        extracted["channels"] = _effective_brief_fields(workbench).get("channels") or "TikTok + Meta"

    return extracted


def _effective_brief_fields(workbench: Dict[str, Any]) -> Dict[str, Any]:
    project = workbench.get("project") or {}
    brief = {k: v for k, v in (workbench.get("brief_fields") or {}).items() if v not in (None, "")}
    project_map = {
        "budget": project.get("totalBudgetValue") or project.get("totalBudget"),
        "target_roas": project.get("targetRoas"),
        "products": project.get("product"),
        "market": project.get("market"),
        "channels": project.get("channels"),
        "live_window": project.get("liveWindow"),
        "inventory": project.get("inventory"),
        "margin": project.get("margin"),
    }
    for key, value in project_map.items():
        if key not in brief and value not in (None, ""):
            brief[key] = value
    return brief


def _brief_summary(workbench: Dict[str, Any]) -> str:
    effective = _effective_brief_fields(workbench)
    return "，".join(
        f"{BRIEF_FIELD_LABELS.get(key, key)}={value}"
        for key, value in effective.items()
        if value not in (None, "")
    )


def _brief_followup_message(completion: Dict[str, Any]) -> str:
    missing_labels = [BRIEF_FIELD_LABELS.get(f, f) for f in completion.get("core_missing", [])]
    if not missing_labels:
        return "核心字段已齐全，我会继续生成方案。"
    return f"已记录当前信息。还缺少：{'、'.join(missing_labels)}。请补充后我就能生成三套方案。"


def _as_float(value: Any, fallback: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        cleaned = "".join(ch for ch in str(value or "") if ch.isdigit() or ch in ".-")
        return float(cleaned) if cleaned else fallback
    except (TypeError, ValueError):
        return fallback


def _clock_label() -> str:
    return datetime.utcnow().strftime("%H:%M")


def _managed_event(agent: str, text: str, tone: str) -> Dict[str, Any]:
    return {"time": _clock_label(), "agent": agent, "text": text, "tone": tone}


def _build_live_action(wb: Dict[str, Any], scenario: str, observation_window: str) -> Dict[str, Any]:
    total_budget = _as_float(wb.get("project", {}).get("totalBudgetValue") or wb.get("project", {}).get("totalBudget"), 5000)
    approval_threshold = _as_float(wb.get("approval_threshold"), 800)
    guard_limit = _as_float(wb.get("guard_limit"), 15)
    is_high_risk = scenario == "high_risk"
    amount = 900 if is_high_risk else 600
    ratio = round((amount / max(total_budget, 1)) * 100, 1)
    return {
        "id": f"live-action-{int(time.time() * 1000)}",
        "type": "budget_shift",
        "source": "TikTok Ads",
        "target": "Meta Ads",
        "amount": amount,
        "ratio": ratio,
        "reason": "Meta 高意向评论和加购信号上升，TikTok 边际 ROAS 低于目标。",
        "expected_impact": "+$210 增量毛利" if not is_high_risk else "+$300 增量毛利",
        "risk": "低于自动调仓护栏" if not is_high_risk else "超过单次审批阈值与调仓比例护栏",
        "observation_window": observation_window,
        "approval_threshold": approval_threshold,
        "guard_limit": guard_limit,
        "requires_approval": amount > approval_threshold or ratio > guard_limit,
        "over_guardrail": ratio > guard_limit,
        "created_at": _clock_label(),
        "status": "pending",
    }


def _live_loop_steps(action: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
    pending = mode == "pending_approval"
    approved = mode == "approved_executed"
    return [
        {
            "id": "signal",
            "agent": "经营信号",
            "status": "done",
            "summary": f"{action['observation_window']}：评论、咨询、加购信号向 Meta 集中。",
        },
        {
            "id": "analysis",
            "agent": "效果分析",
            "status": "done",
            "summary": "识别到 TikTok 边际 ROAS 低于目标，Meta 转化窗口更稳定。",
        },
        {
            "id": "planning",
            "agent": "方案规划",
            "status": "done",
            "summary": f"生成策略：${action['amount']} {action['source']} → {action['target']}，预期 {action['expected_impact']}。",
        },
        {
            "id": "orchestrator",
            "agent": "调度中心",
            "status": "waiting" if pending else "done",
            "summary": "超过护栏，需要人工确认。" if pending else "护栏校验通过，可授权自动执行。",
        },
        {
            "id": "delivery",
            "agent": "投放执行",
            "status": "waiting" if pending else "done",
            "summary": "等待用户批准后执行。" if pending else ("用户批准执行并已写入预算。" if approved else "已自动写入预算分配。"),
        },
        {
            "id": "verification",
            "agent": "效果验证",
            "status": "pending" if pending else "done",
            "summary": "等待执行后进入验证。" if pending else "验证窗口确认动作有效，保留当前策略。",
        },
    ]


def _rejected_live_loop_steps(action: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = _live_loop_steps(action, "pending_approval")
    steps[3] = {
        "id": "orchestrator",
        "agent": "调度中心",
        "status": "done",
        "summary": "用户拒绝高风险动作，约束已回写。",
    }
    steps[4] = {
        "id": "delivery",
        "agent": "投放执行",
        "status": "skipped",
        "summary": "原动作未执行。",
    }
    steps[5] = {
        "id": "verification",
        "agent": "效果验证",
        "status": "skipped",
        "summary": "保守替代策略生成后等待下一轮验证。",
    }
    steps.append({
        "id": "replan",
        "agent": "方案规划",
        "status": "done",
        "summary": "保守替代策略：暂停低效素材并延长观察窗口，不追加预算。",
    })
    return steps


def _verification_result(action: Dict[str, Any], approved: bool = False) -> Dict[str, Any]:
    return {
        "status": "verified",
        "summary": "验证窗口确认动作有效：Meta ROAS 提升，增量毛利已回写。" if approved else "验证窗口确认动作有效：自动调仓后收益指标改善。",
        "roas_delta": "+0.4",
        "profit_delta": action.get("expected_impact", "+$210 增量毛利"),
        "next_step": "继续观察 10 分钟，若 Meta 边际 ROAS 保持达标则沉淀为下一场策略记忆。",
    }


def _live_iteration_events(action: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
    if mode == "pending_approval":
        return [
            _managed_event("经营信号", "评论/咨询/加购信号集中到 Meta。", "cyan"),
            _managed_event("效果分析", "归因：TikTok 边际 ROAS 下滑，Meta 转化窗口更短。", "amber"),
            _managed_event("方案规划", f"提出高风险动作：${action['amount']} {action['source']} → {action['target']}。", "indigo"),
            _managed_event("调度中心", "动作超过护栏，等待用户审批。", "amber"),
        ]
    return [
        _managed_event("经营信号", "评论/咨询/加购信号集中到 Meta。", "cyan"),
        _managed_event("效果分析", "归因：TikTok 边际 ROAS 下滑，Meta 转化窗口更短。", "amber"),
        _managed_event("方案规划", f"建议调仓：${action['amount']} {action['source']} → {action['target']}。", "indigo"),
        _managed_event("投放执行", f"护栏内自动执行：${action['amount']} {action['source']} → {action['target']}。", "violet"),
        _managed_event("效果分析", "验证窗口回写：增量毛利转正，动作保留。", "emerald"),
    ]


def _apply_live_action_to_rooms(live_rooms: List[Dict[str, Any]], action: Dict[str, Any]) -> List[Dict[str, Any]]:
    amount = _as_float(action.get("amount"), 0)
    updated = []
    for room in live_rooms:
        next_room = deepcopy(room)
        room_id = next_room.get("id")
        if room_id == "creator":
            next_room["budget"] = max(_as_float(next_room.get("spent"), 0), _as_float(next_room.get("budget"), 0) - amount)
            next_room["status"] = "已降预算"
        elif room_id == "brand":
            next_room["budget"] = _as_float(next_room.get("budget"), 0) + amount
            next_room["status"] = "已加码"
            next_room["roas"] = "3.4"
        updated.append(next_room)
    return updated


def _live_roster_patch(mode: str) -> Dict[str, Dict[str, str]]:
    if mode == "pending_approval":
        return {
            "signal": {"status": "采集完成"},
            "analysis": {"status": "已归因"},
            "planning": {"status": "策略待审"},
            "orchestrator": {"status": "等待审批"},
            "delivery": {"status": "待批准"},
        }
    if mode == "rejected":
        return {
            "planning": {"status": "保守重算"},
            "orchestrator": {"status": "约束已回写"},
            "delivery": {"status": "未执行"},
            "analysis": {"status": "观察中"},
        }
    return {
        "signal": {"status": "采集完成"},
        "analysis": {"status": "验证完成"},
        "planning": {"status": "策略已生成"},
        "orchestrator": {"status": "护栏通过"},
        "delivery": {"status": "已执行"},
    }


def _build_orchestrator_context(workbench: Dict) -> str:
    """Build a context summary injected into the system prompt."""
    phase = workbench.get("phase", "briefing")
    brief = workbench.get("brief_fields", {})
    completion = get_brief_completion()

    lines = [f"\n## 当前状态\n- 阶段: {phase}"]

    if brief:
        filled = {k: v for k, v in brief.items() if v is not None}
        if filled:
            lines.append("- 已收集字段: " + ", ".join(f"{BRIEF_FIELD_LABELS.get(k,k)}={v}" for k, v in filled.items()))
        if completion["missing"]:
            labels = [BRIEF_FIELD_LABELS.get(f, f) for f in completion["missing"] if f in CORE_FIELDS]
            if labels:
                lines.append("- 缺少核心字段: " + ", ".join(labels))

    if phase == "planning":
        plans = workbench.get("plan_options", [])
        if plans:
            lines.append(f"- 已生成 {len(plans)} 套方案: " + ", ".join(p.get("title", "") for p in plans))
        selected = workbench.get("selected_plan")
        if selected:
            lines.append(f"- 用户选择: {_plan_title(selected)}")

    if phase == "live":
        live_loop = workbench.get("live_loop") or {}
        lines.append(f"- 投中闭环状态: {live_loop.get('status', 'idle')}")
        pending = live_loop.get("pending_action")
        if pending:
            lines.append(
                f"- 待审批动作: {pending.get('id')} ${pending.get('amount')} "
                f"{pending.get('source')} → {pending.get('target')}, "
                f"原因: {pending.get('reason')}"
            )

    return "\n".join(lines)


def _latest_user_text(messages: List[Dict[str, Any]]) -> str:
    for message in reversed(messages or []):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


def _match_direct_live_command(text: str, workbench: Dict[str, Any]) -> Optional[tuple[str, Dict[str, Any]]]:
    """Route deterministic workbench commands before involving the LLM."""
    normalized = (text or "").strip()
    if not normalized:
        return None

    live_loop = workbench.get("live_loop") or {}
    pending = live_loop.get("pending_action")

    if pending and any(word in normalized for word in ["拒绝", "不批准", "重算"]):
        return "reject_live_action", {"action_id": pending.get("id"), "reason": normalized}
    if pending and any(word in normalized for word in ["批准", "同意", "执行"]):
        return "approve_live_action", {"action_id": pending.get("id")}
    if "高风险" in normalized or "审批阈值" in normalized or "超护栏" in normalized:
        return "run_live_iteration", {"scenario": "high_risk"}
    if "巡检" in normalized or "投中" in normalized or "闭环" in normalized:
        return "run_live_iteration", {"scenario": "auto"}
    return None


def _match_direct_plan_command(text: str, workbench: Dict[str, Any]) -> Optional[tuple[str, Dict[str, Any]]]:
    normalized = (text or "").strip()
    if not normalized:
        return None
    wants_plan = "方案" in normalized and any(word in normalized for word in ["生成", "重新", "三套", "规划", "计划"])
    has_brief_signal = any(word in normalized for word in ["预算", "ROAS", "市场", "商品", "Meta", "TikTok"])
    if wants_plan or (has_brief_signal and "重新" in normalized):
        return "extract_and_generate_plans", {"text": normalized}
    return None


# ---------------------------------------------------------------------------
# Main orchestrator chat (SSE generator)
# ---------------------------------------------------------------------------

async def orchestrator_chat(messages: List[Dict], workbench: Dict) -> AsyncGenerator[str, None]:
    """Main entry. Yields SSE event strings."""
    latest_user_text = _latest_user_text(messages)
    direct_command = (
        _match_direct_live_command(latest_user_text, workbench)
        or _match_direct_plan_command(latest_user_text, workbench)
    )
    if direct_command:
        tool_name, tool_args = direct_command
        yield _sse({"type": "model", "model": "orchestrator-state-machine"})
        yield _sse({"type": "tool_call", "tool": tool_name, "arguments": tool_args})
        handler = TOOL_HANDLERS.get(tool_name)
        if handler:
            tool_result, extra_events = handler(tool_args)
            for ev in extra_events:
                yield _sse(ev)
        else:
            tool_result = {"success": False, "error": f"未知工具: {tool_name}"}
        yield _sse({"type": "tool_result", "tool": tool_name, "result": tool_result})
        if tool_result.get("success"):
            yield _sse({"type": "content", "content": tool_result.get("message", "已完成。")})
        else:
            yield _sse({"type": "error", "content": tool_result.get("error", "操作失败。")})
        yield _sse({"type": "done"})
        return

    try:
        from openai import AsyncOpenAI
    except ImportError:
        yield _sse({"type": "error", "content": "后端缺少 openai Python SDK。"})
        yield _sse({"type": "done"})
        return

    config = _get_llm_config()
    if not config["api_key"]:
        yield _sse({"type": "error", "content": "LLM API Key 未配置。请在 .env.hackathon 中填写 QIJI_API_KEY。"})
        yield _sse({"type": "done"})
        return

    model = config["model"]
    yield _sse({"type": "model", "model": model})

    context = _build_orchestrator_context(workbench)
    system_msg = ORCHESTRATOR_SYSTEM_PROMPT + context

    api_messages = [{"role": "system", "content": system_msg}]
    api_messages.extend(messages)

    client = AsyncOpenAI(
        api_key=config["api_key"],
        base_url=config["api_base"],
        default_headers={"User-Agent": "curl/8.5.0"},
        timeout=120.0,
    )

    MAX_TOOL_ROUNDS = 5
    for _round in range(MAX_TOOL_ROUNDS):
        try:
            completion = await client.chat.completions.create(
                model=model,
                messages=api_messages,
                tools=ORCHESTRATOR_TOOLS,
                stream=False,
                max_completion_tokens=1200,
            )
        except Exception as exc:
            yield _sse({"type": "error", "content": f"LLM 调用失败: {exc}"})
            yield _sse({"type": "done"})
            return

        choice = completion.choices[0] if completion.choices else None
        assistant_msg = choice.message if choice else None
        tool_calls = assistant_msg.tool_calls if assistant_msg else []

        if not tool_calls:
            if not assistant_msg or not assistant_msg.content:
                finish = choice.finish_reason if choice else "unknown"
                yield _sse({"type": "error", "content": f"模型返回空响应 (finish_reason={finish}, round={_round})"})
            break

        api_messages.append(assistant_msg.model_dump(exclude_none=True))
        tool_results_this_round: List[tuple[str, Dict[str, Any]]] = []

        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                tool_args = {}

            yield _sse({"type": "tool_call", "tool": tool_name, "arguments": tool_args})

            handler = TOOL_HANDLERS.get(tool_name)
            if handler:
                tool_result, extra_events = handler(tool_args)
                for ev in extra_events:
                    yield _sse(ev)
            else:
                tool_result = {"success": False, "error": f"未知工具: {tool_name}"}

            yield _sse({"type": "tool_result", "tool": tool_name, "result": tool_result})
            tool_results_this_round.append((tool_name, tool_result))

            api_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_result, ensure_ascii=False),
            })

        called_tool_names = [name for name, _result in tool_results_this_round]
        extract_result = next((result for name, result in tool_results_this_round if name == "extract_brief"), None)
        if extract_result and "generate_plans" not in called_tool_names:
            completion = extract_result.get("brief_status") or {}
            if completion.get("complete"):
                gen_args = {"brief_summary": _brief_summary(read_workbench())}
                yield _sse({"type": "tool_call", "tool": "generate_plans", "arguments": gen_args})
                gen_result, gen_events = _handle_generate_plans(gen_args)
                for ev in gen_events:
                    yield _sse(ev)
                yield _sse({"type": "tool_result", "tool": "generate_plans", "result": gen_result})
                yield _sse({"type": "content", "content": "核心字段已齐全，我已生成三套投放方案，请在中间画布查看并选择。"})
                yield _sse({"type": "done"})
                return
            yield _sse({"type": "content", "content": extract_result.get("message") or _brief_followup_message(completion)})
            yield _sse({"type": "done"})
            return

    if assistant_msg and assistant_msg.content:
        yield _sse({"type": "content", "content": assistant_msg.content})
    else:
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=api_messages,
                stream=True,
                max_completion_tokens=1200,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", "") or ""
                if content:
                    yield _sse({"type": "content", "content": content})
        except Exception as exc:
            yield _sse({"type": "error", "content": f"LLM 流式响应失败: {exc}"})

    yield _sse({"type": "done"})
