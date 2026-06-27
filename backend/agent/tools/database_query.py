"""Safe backend data query tool for the agent."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from agent_mode_repository import AGENT_TABLES, create_agent_mode_repository
    from agent_mode_store import read_workbench
except ImportError:  # pragma: no cover
    from backend.agent_mode_repository import AGENT_TABLES, create_agent_mode_repository
    from backend.agent_mode_store import read_workbench


RESOURCE_TO_TABLE = {
    "budget_projects": AGENT_TABLES["projects"],
    "plan_versions": AGENT_TABLES["versions"],
    "skus": AGENT_TABLES["skus"],
    "live_frames": AGENT_TABLES["frames"],
    "events": AGENT_TABLES["events"],
    "actions": AGENT_TABLES["actions"],
    "reviews": AGENT_TABLES["reviews"],
}


def query_backend_database(arguments: Dict[str, Any]) -> Dict[str, Any]:
    resource = str(arguments.get("resource") or "").strip()
    limit = max(1, min(100, int(arguments.get("limit") or 20)))
    if resource == "workbench":
        return {
            "success": True,
            "resource": resource,
            "configured": True,
            "data": read_workbench(),
        }
    if resource not in RESOURCE_TO_TABLE:
        return {
            "success": False,
            "resource": resource,
            "error": f"不支持的资源: {resource}",
            "allowed": ["workbench", *RESOURCE_TO_TABLE.keys()],
        }

    env_override: Optional[Dict[str, str]] = arguments.get("env")
    repository = create_agent_mode_repository(env=env_override) if isinstance(env_override, dict) else create_agent_mode_repository()
    if not getattr(repository, "enabled", False):
        return {
            "success": False,
            "resource": resource,
            "configured": False,
            "error": "Supabase 未配置，无法查询持久化数据。",
            "setup": "配置 SUPABASE_URL 和 SUPABASE_SECRET_KEY 后重启后端。",
        }

    params = {"tenant_key": f"eq.{getattr(repository, 'tenant_key', 'demo')}", "limit": str(limit)}
    if arguments.get("project_id"):
        params["project_id"] = f"eq.{arguments['project_id']}"
    if arguments.get("plan_version_id"):
        params["plan_version_id"] = f"eq.{arguments['plan_version_id']}"
    if resource in {"budget_projects", "plan_versions", "events", "reviews"}:
        params["order"] = "created_at.desc"
    if resource == "live_frames":
        params["order"] = "frame_index.asc"

    rows = repository.transport.request("GET", RESOURCE_TO_TABLE[resource], params=params)
    return {
        "success": True,
        "resource": resource,
        "configured": True,
        "count": len(rows),
        "rows": rows,
    }
