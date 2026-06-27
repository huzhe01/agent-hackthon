"""OpenAI-compatible registry for MaiDeal agent tools."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable, Dict, Iterable, List, Optional

from .tools.budget_allocator import allocate_budget
from .tools.content_generation import generate_marketing_content
from .tools.database_query import query_backend_database
from .tools.external_knowledge import refresh_business_knowledge
from .tools.media_platforms import inspect_media_api
from .tools.model_estimation import estimate_ad_performance
from .tools.simulator import simulate_live_workbench


Handler = Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass(frozen=True)
class AgentTool:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Handler
    layer: str
    skill: str

    def as_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def as_summary(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "layer": self.layer,
            "skill": self.skill,
        }


def _object(properties: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
    }


TOOLS: Dict[str, AgentTool] = {
    "estimate_ad_performance": AgentTool(
        name="estimate_ad_performance",
        description="使用 ad_rec_backend 兼容的流量/CTR 估计能力，为商品、渠道或素材预估点击、GMV、ROI 和推荐理由。",
        parameters=_object({
            "product": {"type": "string", "description": "商品或 SKU 名称"},
            "category": {"type": "string", "description": "商品类目"},
            "budget": {"type": "number", "description": "用于估算的预算"},
            "channels": {"type": "array", "items": {"type": "string"}, "description": "候选渠道"},
            "audience_size": {"type": "integer", "description": "预估触达人群规模"},
            "average_order_value": {"type": "number", "description": "客单价"},
        }, ["product"]),
        handler=estimate_ad_performance,
        layer="tool",
        skill="traffic-estimation",
    ),
    "query_backend_database": AgentTool(
        name="query_backend_database",
        description="通过后端安全 allowlist 查询 Supabase/工作台数据，不暴露 service role，也不执行任意 SQL。",
        parameters=_object({
            "resource": {
                "type": "string",
                "enum": ["workbench", "budget_projects", "plan_versions", "skus", "live_frames", "events", "actions", "reviews"],
            },
            "project_id": {"type": "string"},
            "plan_version_id": {"type": "string"},
            "limit": {"type": "integer"},
        }, ["resource"]),
        handler=query_backend_database,
        layer="tool",
        skill="database-query",
    ),
    "generate_marketing_content": AgentTool(
        name="generate_marketing_content",
        description="用 Qiji/OpenAI-compatible 图片模型 gpt-image-2 生成投放物料图、标题和小红书文案；无 key 时返回可审核草稿和配置提示。",
        parameters=_object({
            "product": {"type": "string"},
            "selling_points": {"type": "array", "items": {"type": "string"}},
            "audience": {"type": "string"},
            "platform": {"type": "string", "description": "例如 小红书"},
            "image_prompt": {"type": "string"},
            "offline": {"type": "boolean"},
        }, ["product"]),
        handler=generate_marketing_content,
        layer="tool",
        skill="content-publishing",
    ),
    "allocate_budget": AgentTool(
        name="allocate_budget",
        description="在线性预算约束、渠道 ROI 预估、min/max 护栏下求解预算分配，返回可解释的最优分配。",
        parameters=_object({
            "total_budget": {"type": "number"},
            "channels": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "roi": {"type": "number"},
                        "min_budget": {"type": "number"},
                        "max_budget": {"type": "number"},
                    },
                    "required": ["id", "roi"],
                },
            },
            "reserve_ratio": {"type": "number"},
        }, ["total_budget", "channels"]),
        handler=allocate_budget,
        layer="tool",
        skill="budget-allocation",
    ),
    "inspect_media_api": AgentTool(
        name="inspect_media_api",
        description="查询媒体 RTA/RTB/API 接入信息，覆盖巨量引擎、巨量千川、小红书聚光，并给出权限、资质和下一步。",
        parameters=_object({
            "platforms": {"type": "array", "items": {"type": "string"}},
            "capability": {"type": "string", "description": "例如 RTA/RTB、报表、素材、计划管理"},
        }),
        handler=inspect_media_api,
        layer="tool",
        skill="media-rta-rtb",
    ),
    "refresh_business_knowledge": AgentTool(
        name="refresh_business_knowledge",
        description="使用 Xiaosu/Cloudsway SmartSearch 查询外部经营线索，写入本地 knowledge，并提炼 memory。",
        parameters=_object({
            "query": {"type": "string"},
            "count": {"type": "integer"},
            "freshness": {"type": "string", "enum": ["Day", "Week", "Month"]},
            "offline_results": {"type": "array", "items": {"type": "object"}},
            "knowledge_dir": {"type": "string"},
            "memory_dir": {"type": "string"},
        }, ["query"]),
        handler=refresh_business_knowledge,
        layer="tool",
        skill="business-knowledge",
    ),
    "simulate_live_workbench": AgentTool(
        name="simulate_live_workbench",
        description="在没有真实投放数据时，根据 brief 生成 SKU、渠道预算池、直播帧、事件、审批和复盘快照。",
        parameters=_object({
            "brief": {"type": "object"},
            "version_number": {"type": "integer"},
        }, ["brief"]),
        handler=simulate_live_workbench,
        layer="tool",
        skill="live-simulator",
    ),
}


def list_agent_tools() -> List[Dict[str, Any]]:
    return [tool.as_summary() for tool in TOOLS.values()]


def get_agent_tool_schemas(names: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
    if names is None:
        selected = TOOLS.values()
    else:
        selected = [TOOLS[name] for name in names if name in TOOLS]
    return [tool.as_schema() for tool in selected]


def dispatch_agent_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    tool = TOOLS.get(name)
    if not tool:
        return {"success": False, "error": f"未知 agent 工具: {name}"}
    try:
        result = tool.handler(arguments or {})
        if "tool" not in result:
            result["tool"] = name
        return result
    except Exception as exc:  # pragma: no cover - defensive safety for agent runtime
        return {"success": False, "tool": name, "error": str(exc)}


def build_tool_prompt() -> str:
    """Compact prompt block for models that need to reason about tool use."""
    return "可用 agent 工具:\n" + "\n".join(
        f"- {tool.name}: {tool.description} (skill={tool.skill})"
        for tool in TOOLS.values()
    )


def dispatch_tool_json(name: str, arguments_json: str) -> Dict[str, Any]:
    try:
        arguments = json.loads(arguments_json or "{}")
    except json.JSONDecodeError:
        arguments = {}
    return dispatch_agent_tool(name, arguments)
