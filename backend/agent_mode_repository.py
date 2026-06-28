"""Supabase-backed persistence for the Agent Mode workbench."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import os
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

import httpx

try:
    from agent_mode_simulator import build_simulation_bundle, normalize_brief
except ImportError:  # pragma: no cover - used when imported as backend package
    from backend.agent_mode_simulator import build_simulation_bundle, normalize_brief


AGENT_TABLES = {
    "projects": "agent_budget_projects",
    "versions": "agent_plan_versions",
    "skus": "agent_project_skus",
    "frames": "agent_live_frames",
    "events": "agent_events",
    "actions": "agent_live_actions",
    "reviews": "agent_reviews",
}


class SupabaseRestTransport:
    """Tiny PostgREST client using the server-side Supabase secret key."""

    def __init__(self, supabase_url: str, secret_key: str, timeout: float = 20.0):
        self.supabase_url = supabase_url.rstrip("/")
        self.secret_key = secret_key
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        prefer: Optional[str] = None,
    ) -> Any:
        table = path.strip("/")
        url = f"{self.supabase_url}/rest/v1/{table}"
        headers = {
            "apikey": self.secret_key,
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer

        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
            )
        if response.status_code >= 400:
            raise RuntimeError(f"Supabase request failed: {method} {table} -> {response.status_code} {response.text[:240]}")
        if not response.text:
            return []
        return response.json()


class DisabledAgentModeRepository:
    enabled = False

    def build_workbench(self, project_id: Optional[str] = None) -> Dict[str, Any]:  # pragma: no cover - defensive
        raise RuntimeError("Supabase is not configured for Agent Mode persistence.")

    def save_generated_plan(self, brief: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        raise RuntimeError("Supabase is not configured for Agent Mode persistence.")


class AgentModeRepository:
    """Read/write Agent Mode snapshots using Supabase tables."""

    enabled = True

    def __init__(self, transport: Any, tenant_key: str = "demo"):
        self.transport = transport
        self.tenant_key = tenant_key
        self.active_project_id: Optional[str] = None

    def save_generated_plan(self, brief: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
        normalized = normalize_brief(brief)
        now = _now()
        project = self._find_project(normalized)
        version_number = 1
        if project:
            project_id = project["id"]
            existing_versions = self._rows(
                "versions",
                {
                    "project_id": f"eq.{project_id}",
                    "tenant_key": f"eq.{self.tenant_key}",
                    "order": "version_number.asc",
                },
            )
            version_number = _next_version_number(existing_versions)
        else:
            project_id = _id()

        plan_version_id = _id()
        bundle = deepcopy(bundle)
        if int(bundle.get("version_number") or version_number) != version_number:
            bundle["version_number"] = version_number

        if not project:
            project = {
                "id": project_id,
                "tenant_key": self.tenant_key,
                "name": _project_name(normalized),
                "product": normalized["products"],
                "market": normalized["market"],
                "currency": normalized["currency"],
                "budget": normalized["budget"],
                "target_roas": normalized["target_roas"],
                "channels": normalized["channels"],
                "brief": normalized,
                "status": "draft",
                "active_plan_version_id": plan_version_id,
                "created_at": now,
                "updated_at": now,
            }
            self._insert("projects", project)
        else:
            project = {
                **project,
                "product": normalized["products"],
                "market": normalized["market"],
                "currency": normalized["currency"],
                "budget": normalized["budget"],
                "target_roas": normalized["target_roas"],
                "channels": normalized["channels"],
                "brief": normalized,
                "status": "draft",
                "active_plan_version_id": plan_version_id,
                "updated_at": now,
            }
            self._patch("projects", {"id": f"eq.{project_id}"}, project)

        version = {
            "id": plan_version_id,
            "tenant_key": self.tenant_key,
            "project_id": project_id,
            "version_number": version_number,
            "selected_mode": "balanced",
            "recommended_mode": "balanced",
            "brief_snapshot": normalized,
            "plan_options": bundle.get("plan_options", []),
            "channel_pools": bundle.get("channel_pools", []),
            "guardrails": _guardrails(normalized),
            "live_rooms": bundle.get("live_rooms", []),
            "simulator_seed": bundle.get("simulator_seed"),
            "created_at": now,
        }
        self._insert("versions", version)

        self._insert_many("skus", [
            {
                "id": _id(),
                "tenant_key": self.tenant_key,
                "project_id": project_id,
                "plan_version_id": plan_version_id,
                "sku_code": sku["sku_code"],
                "name": sku["name"],
                "category": sku["category"],
                "price": sku["price"],
                "base_inventory": sku["base_inventory"],
                "margin_rate": sku["margin_rate"],
                "attributes": sku.get("attributes", {}),
            }
            for sku in bundle.get("product_catalog", [])
        ])

        frames = bundle.get("live_demo", {}).get("frames", [])
        self._insert_many("frames", [
            {
                "id": _id(),
                "tenant_key": self.tenant_key,
                "project_id": project_id,
                "plan_version_id": plan_version_id,
                "frame_index": index,
                "frame_time": frame.get("time"),
                "elapsed_seconds": frame.get("elapsed_seconds") or index * 60,
                "metrics": frame.get("metrics", {}),
                "budget_pool": frame.get("budget_pool", []),
                "sku_ads": frame.get("sku_ads", []),
                "steps": frame.get("steps", []),
                "alerts": frame.get("alerts", []),
                "created_at": now,
            }
            for index, frame in enumerate(frames)
        ])

        events = bundle.get("managed_events", [])
        self._insert_many("events", [
            {
                "id": _id(),
                "tenant_key": self.tenant_key,
                "project_id": project_id,
                "plan_version_id": plan_version_id,
                "frame_index": event.get("frame_index"),
                "agent": event.get("agent"),
                "event_type": event.get("event_type") or "signal",
                "text": event.get("text"),
                "tone": event.get("tone"),
                "action_id": event.get("action_id"),
                "created_at": now,
            }
            for event in events
        ])

        self._insert_many("actions", _actions_from_frames(project_id, plan_version_id, self.tenant_key, frames, now))

        review = bundle.get("review", {})
        if review:
            self._insert("reviews", {
                "id": _id(),
                "tenant_key": self.tenant_key,
                "project_id": project_id,
                "plan_version_id": plan_version_id,
                "expected_roas": review.get("expected_roas"),
                "actual_roas": review.get("actual_roas"),
                "baseline_roas": review.get("baseline_roas"),
                "incremental_profit": review.get("incremental_profit"),
                "key_actions": review.get("key_actions", []),
                "lead_assets": review.get("lead_assets", []),
                "strategy_notes": review.get("strategy_notes", []),
                "api_trace": review.get("api_trace", []),
                "created_at": now,
            })

        self.active_project_id = project_id
        return {"project": project, "plan_version": version}

    def build_workbench(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        projects = self._list_projects()
        if not projects:
            self._seed_demo_projects()
            projects = self._list_projects()

        selected = _pick_project(projects, project_id or self.active_project_id)
        if not selected:
            return _empty_workbench()

        self.active_project_id = selected["id"]
        return self._workbench_for_project(selected, projects)

    def _workbench_for_project(self, project: Dict[str, Any], all_projects: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        version = self._active_version(project)
        versions = self._rows("versions", {
            "tenant_key": f"eq.{self.tenant_key}",
            "project_id": f"eq.{project['id']}",
            "order": "version_number.asc",
        })
        frames = self._rows("frames", {
            "tenant_key": f"eq.{self.tenant_key}",
            "project_id": f"eq.{project['id']}",
            "plan_version_id": f"eq.{version['id']}" if version else None,
            "order": "frame_index.asc",
        }) if version else []
        events = self._rows("events", {
            "tenant_key": f"eq.{self.tenant_key}",
            "project_id": f"eq.{project['id']}",
            "plan_version_id": f"eq.{version['id']}" if version else None,
            "order": "created_at.asc",
        }) if version else []
        review = self._first("reviews", {
            "tenant_key": f"eq.{self.tenant_key}",
            "project_id": f"eq.{project['id']}",
            "plan_version_id": f"eq.{version['id']}" if version else None,
        }) if version else None

        workbench = {
            "phase": "plan" if project.get("status") != "completed" else "review",
            "active_project_id": project["id"],
            "brief_complete": True,
            "brief_fields": project.get("brief") or {},
            "project": _project_workbench(project),
            "budget_projects": _budget_project_list(all_projects or [project]),
            "selected_room_id": "brand",
            "selected_plan": (version or {}).get("selected_mode") or "balanced",
            "guard_limit": str((version or {}).get("guardrails", {}).get("guard_limit", 15)),
            "approval_threshold": str((version or {}).get("guardrails", {}).get("approval_threshold", 800)),
            "plan_options": (version or {}).get("plan_options", []),
            "plan_versions": [_plan_version_summary(item, version) for item in versions],
            "live_rooms": (version or {}).get("live_rooms", []),
            "live_demo": {
                "enabled": True,
                "tick_interval_ms": 10000,
                "frames": [_frame_workbench(row) for row in frames],
            },
            "managed_events": [_event_workbench(row) for row in events],
            "lead_rows": (review or {}).get("lead_assets", []),
            "review_benchmarks": _review_benchmarks(review),
            "review_actions": (review or {}).get("key_actions", []),
            "strategy_notes": (review or {}).get("strategy_notes", []),
            "api_trace": (review or {}).get("api_trace", []),
            "fallback_campaigns": _campaigns_from_frames(frames),
        }
        return workbench

    def _seed_demo_projects(self) -> None:
        demos = [
            {
                "budget": 5000,
                "target_roas": 3.0,
                "products": "便携榨汁杯",
                "market": "美国 / USD",
                "channels": "TikTok Ads, Meta Ads",
                "inventory": "1200 件",
                "margin": "55%",
            },
            {
                "budget": 3200,
                "target_roas": 2.8,
                "products": "磁吸手机壳",
                "market": "东南亚 / SGD",
                "channels": "TikTok Ads, Shopee Ads",
                "inventory": "2600 件",
                "margin": "45%",
            },
        ]
        for index, brief in enumerate(demos, start=1):
            bundle = build_simulation_bundle(brief, version_number=index)
            self.save_generated_plan(brief, bundle)

    def _find_project(self, brief: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        name = _project_name(brief)
        return self._first("projects", {"tenant_key": f"eq.{self.tenant_key}", "name": f"eq.{name}"})

    def _active_version(self, project: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        active_id = project.get("active_plan_version_id")
        rows = self._rows("versions", {
            "tenant_key": f"eq.{self.tenant_key}",
            "project_id": f"eq.{project['id']}",
            "order": "version_number.desc",
        })
        if active_id:
            for row in rows:
                if row.get("id") == active_id:
                    return row
        return rows[0] if rows else None

    def _list_projects(self) -> List[Dict[str, Any]]:
        return self._rows("projects", {"tenant_key": f"eq.{self.tenant_key}", "order": "created_at.asc"})

    def _rows(self, logical_table: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        rows = self.transport.request("GET", AGENT_TABLES[logical_table], params=clean_params)
        return rows if isinstance(rows, list) else []

    def _first(self, logical_table: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        rows = self._rows(logical_table, params)
        return rows[0] if rows else None

    def _insert(self, logical_table: str, row: Dict[str, Any]) -> None:
        self.transport.request("POST", AGENT_TABLES[logical_table], json_body=row, prefer="return=representation")

    def _insert_many(self, logical_table: str, rows: Iterable[Dict[str, Any]]) -> None:
        rows = list(rows)
        if rows:
            self.transport.request("POST", AGENT_TABLES[logical_table], json_body=rows, prefer="return=representation")

    def _patch(self, logical_table: str, params: Dict[str, Any], row: Dict[str, Any]) -> None:
        self.transport.request("PATCH", AGENT_TABLES[logical_table], params=params, json_body=row, prefer="return=representation")


def create_agent_mode_repository(env: Optional[Dict[str, str]] = None) -> Any:
    env = env if env is not None else os.environ
    secret = env.get("SUPABASE_SECRET_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not secret:
        return DisabledAgentModeRepository()

    project_id = env.get("SUPABASE_PROJECT_ID")
    supabase_url = env.get("SUPABASE_URL")
    if not supabase_url and project_id:
        supabase_url = f"https://{project_id}.supabase.co"
    if not supabase_url:
        return DisabledAgentModeRepository()

    tenant_key = env.get("AGENT_MODE_TENANT_KEY") or "demo"
    return AgentModeRepository(SupabaseRestTransport(supabase_url, secret), tenant_key=tenant_key)


def _project_workbench(project: Dict[str, Any]) -> Dict[str, Any]:
    brief = project.get("brief") or {}
    return {
        "name": project.get("name") or "",
        "product": project.get("product") or "",
        "market": project.get("market") or "",
        "totalBudget": _money(project.get("budget")),
        "totalBudgetValue": project.get("budget") or 0,
        "liveWindow": brief.get("live_window") or "",
        "inventory": str(brief.get("inventory") or ""),
        "margin": _percent(brief.get("margin_rate")),
        "targetRoas": str(project.get("target_roas") or ""),
        "channels": " + ".join(project.get("channels") or []),
    }


def _budget_project_list(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = []
    for project in projects:
        brief = project.get("brief") or {}
        items.append({
            "id": project["id"],
            "name": project.get("name"),
            "market": project.get("market"),
            "status": _status_label(project.get("status")),
            "budget": _money(project.get("budget")),
            "spent": "$0",
            "roas": str(project.get("target_roas") or ""),
            "updated_at": "当前" if project.get("status") != "completed" else "已复盘",
            "workbench": {
                "active_project_id": project["id"],
                "brief_fields": brief,
                "project": _project_workbench(project),
            },
        })
    return items


def _frame_workbench(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": f"frame-{row.get('frame_index', 0):02d}",
        "time": row.get("frame_time"),
        "elapsed": _elapsed(row.get("elapsed_seconds") or 0),
        "elapsed_seconds": row.get("elapsed_seconds") or 0,
        "state_label": _state_label(row.get("alerts") or []),
        "metrics": row.get("metrics") or {},
        "budget_pool": row.get("budget_pool") or [],
        "sku_ads": row.get("sku_ads") or [],
        "steps": row.get("steps") or [],
        "alerts": row.get("alerts") or [],
        "events": [],
    }


def _event_workbench(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "time": _time_from_created(row.get("created_at")),
        "agent": row.get("agent"),
        "text": row.get("text"),
        "tone": row.get("tone") or "cyan",
        "event_type": row.get("event_type") or "signal",
        "action_id": row.get("action_id"),
    }


def _review_benchmarks(review: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not review:
        return []
    actual_roas = review.get("actual_roas") or 0
    baseline_roas = review.get("baseline_roas") or 0
    incremental = review.get("incremental_profit") or 0
    return [
        {"title": "固定预算基线", "line1": f"ROAS {baseline_roas}", "line2": "历史参照", "line3": "固定预算", "highlight": False},
        {"title": "MaiDeal 托管实际", "line1": f"ROAS {actual_roas}", "line2": "最终帧回算", "line3": f"{_signed_money(incremental)} 增量毛利", "highlight": True},
        {"title": "增量贡献", "line1": f"{_roas_lift(actual_roas, baseline_roas)} ROAS", "line2": "完整快照", "line3": "SKU 与审批可回放", "highlight": False},
    ]


def _campaigns_from_frames(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not frames:
        return []
    final_skus = frames[-1].get("sku_ads") or []
    return [
        {
            "id": index + 1,
            "name": item.get("name"),
            "spend": item.get("spend") or 0,
            "roi": item.get("roi") or 0,
            "ctr": 0,
        }
        for index, item in enumerate(final_skus[:5])
    ]


def _actions_from_frames(project_id: str, plan_version_id: str, tenant_key: str, frames: List[Dict[str, Any]], now: str) -> List[Dict[str, Any]]:
    rows = []
    for index, frame in enumerate(frames):
        for alert in frame.get("alerts", []):
            action_id = _id()
            rows.append({
                "id": action_id,
                "tenant_key": tenant_key,
                "project_id": project_id,
                "plan_version_id": plan_version_id,
                "frame_index": index,
                "type": alert.get("type") or "alert",
                "source": "低效 SKU",
                "target": "高效渠道",
                "amount": 0,
                "reason": alert.get("message"),
                "expected_impact": alert.get("recommendation"),
                "risk": alert.get("severity") or "warning",
                "status": "pending_approval" if alert.get("severity") == "critical" else "recommended",
                "decision": None,
                "decided_at": None,
                "created_at": now,
            })
    return rows


def _plan_version_summary(version: Dict[str, Any], active: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": version["id"],
        "label": f"Plan v{version.get('version_number', 1)}",
        "created_at": "当前" if active and version["id"] == active.get("id") else "",
        "summary": "持久化预算托管方案",
        "plan_ids": [plan.get("id") for plan in version.get("plan_options", [])],
        "active": bool(active and version["id"] == active.get("id")),
    }


def _pick_project(projects: List[Dict[str, Any]], project_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if project_id:
        for project in projects:
            if project.get("id") == project_id:
                return project
    return projects[-1] if projects else None


def _next_version_number(versions: List[Dict[str, Any]]) -> int:
    if not versions:
        return 1
    return max(int(item.get("version_number") or 0) for item in versions) + 1


def _project_name(brief: Dict[str, Any]) -> str:
    market_prefix = str(brief.get("market") or "").split("/")[0].strip() or "默认市场"
    if "东南亚" in market_prefix:
        return f"{brief.get('products')} · 东南亚直播"
    return f"{brief.get('products')} · {market_prefix}直播"


def _guardrails(brief: Dict[str, Any]) -> Dict[str, Any]:
    budget = float(brief.get("budget") or 0)
    return {
        "guard_limit": 15 if budget >= 5000 else 12,
        "approval_threshold": max(300, round(budget * 0.16)),
        "disabled_actions": ["价格承诺", "退款处理", "新开渠道"],
    }


def _empty_workbench() -> Dict[str, Any]:
    return {"active_project_id": None, "budget_projects": []}


def _status_label(status: Optional[str]) -> str:
    return {"completed": "已复盘", "launched": "托管中", "draft": "待托管"}.get(status or "draft", "待托管")


def _state_label(alerts: List[Dict[str, Any]]) -> str:
    if any(alert.get("severity") == "critical" for alert in alerts):
        return "待审批"
    if alerts:
        return "自动预警"
    return "运行中"


def _elapsed(seconds: int) -> str:
    minutes, second = divmod(int(seconds), 60)
    hour, minute = divmod(minutes, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d}"


def _time_from_created(value: Optional[str]) -> str:
    if not value:
        return ""
    return value[11:16] if len(value) >= 16 else value


def _money(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"${number:,.0f}"


def _signed_money(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    sign = "+" if number >= 0 else "-"
    return f"{sign}${abs(number):,.0f}"


def _percent(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    if number <= 1:
        number *= 100
    return f"{number:.0f}%"


def _roas_lift(actual: Any, baseline: Any) -> str:
    try:
        actual_number = float(actual or 0)
        baseline_number = float(baseline or 0)
    except (TypeError, ValueError):
        return "+0%"
    if baseline_number <= 0:
        return "+0%"
    lift = round((actual_number / baseline_number - 1) * 100)
    return f"{lift:+d}%"


def _id() -> str:
    return str(uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
