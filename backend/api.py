#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GrowEngine 后端 API 服务
=========================
提供广告投放平台的核心 API 接口，包括：
- 广告计划 CRUD
- 实时数据监控
- 模拟竞价服务
- AI 诊断建议

技术栈: FastAPI + Uvicorn
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from urllib.parse import urlparse
import random
import math
import uuid
import json
import httpx
import asyncio
import os
from dotenv import load_dotenv

try:
    from agent_mode_store import read_workbench, write_workbench, reset_workbench
    from agent_mode_repository import create_agent_mode_repository
    from orchestrator import orchestrator_chat
    from agent.registry import dispatch_agent_tool, get_agent_tool_schemas
except ImportError:  # pragma: no cover - used by tests importing backend.api as a package
    from backend.agent_mode_store import read_workbench, write_workbench, reset_workbench
    from backend.agent_mode_repository import create_agent_mode_repository
    from backend.orchestrator import orchestrator_chat
    from backend.agent.registry import dispatch_agent_tool, get_agent_tool_schemas

load_dotenv()

# ==================== 应用初始化 ====================

app = FastAPI(
    title="GrowEngine API",
    description="广告投放自动化平台 - 后端 API 服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================

class Campaign(BaseModel):
    """广告计划模型"""
    id: int
    name: str
    status: str = "learning"  # active, learning, paused
    budget: float = 5000
    bid: float = 65
    spend: float = 0
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0
    cvr: float = 0
    cpa: float = 0
    roi: float = 0
    learning_stage: str = "learning"  # learning, passed, failed
    bid_type: str = "oCPM"  # CPC, CPM, oCPM, NOBID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CampaignCreate(BaseModel):
    """创建广告计划请求"""
    name: str
    budget: float = Field(ge=100, le=1000000)
    bid: float = Field(ge=0.1, le=10000)
    target_type: str = "商品购买"
    bid_type: str = "oCPM"

class CampaignUpdate(BaseModel):
    """更新广告计划请求"""
    name: Optional[str] = None
    budget: Optional[float] = None
    bid: Optional[float] = None
    status: Optional[str] = None

class BidRequest(BaseModel):
    """竞价请求"""
    campaign_id: int
    p_value: float  # 预估转化率
    user_features: Optional[Dict[str, Any]] = None

class BidResponse(BaseModel):
    """竞价响应"""
    bid_price: float
    win_probability: float
    estimated_conversion: float

class DiagnosticItem(BaseModel):
    """诊断项目"""
    type: str  # warning, opportunity, success
    title: str
    description: str
    action: str
    priority: int = 1

class MetricsSnapshot(BaseModel):
    """实时指标快照"""
    timestamp: str
    total_spend: float
    total_gmv: float
    roi: float
    ctr: float
    cvr: float
    active_campaigns: int

class AgentChatRequest(BaseModel):
    """Agent 对话请求"""
    messages: List[Dict[str, str]]
    enable_tools: bool = True
    model: Optional[str] = None
    models: Optional[List[str]] = None
    enabled_data_sources: Optional[List[str]] = None

class CampaignPreview(BaseModel):
    """AI 生成的计划预览"""
    name: str
    budget: float
    bid: float
    target_type: str = "商品购买"
    bid_type: str = "oCPM"

# ==================== LLM Agent 配置 ====================

QIJI_DEFAULT_BASE_URL = "https://api.openai-next.com/v1"
QIJI_DEFAULT_MODEL = "gpt-5"
XIAOSU_SEARCH_DEFAULT_URL = "https://aisearchapi.cloudsway.net/api/search/smart"


def get_qiji_config() -> Dict[str, str]:
    """Read Qiji/OpenAI-compatible model configuration from env."""
    return {
        "api_base": os.getenv("QIJI_BASE_URL") or QIJI_DEFAULT_BASE_URL,
        "api_key": os.getenv("QIJI_API_KEY") or os.getenv("LLM_API_KEY") or "",
        "model": os.getenv("QIJI_MODEL") or QIJI_DEFAULT_MODEL,
    }


def get_xiaosu_search_config() -> Dict[str, str]:
    """Read Xiaosu/Cloudsway SmartSearch configuration from env."""
    return {
        "api_base": os.getenv("CLOUDSWAY_SEARCH_URL") or XIAOSU_SEARCH_DEFAULT_URL,
        "api_key": os.getenv("CLOUDSWAY_SEARCH_KEY") or os.getenv("XIAOSU_SEARCH_API_KEY") or "",
    }


LLM_CONFIG = get_qiji_config()

AGENT_DATA_SOURCES = [
    {
        "id": "realtime_metrics",
        "label": "实时数据",
        "description": "GMV、消耗、ROI、CTR、CVR、活跃计划数",
        "enabled_by_default": True,
    },
    {
        "id": "trend_metrics",
        "label": "趋势曲线",
        "description": "消耗、GMV、ROAS 的小时级趋势",
        "enabled_by_default": True,
    },
    {
        "id": "campaigns",
        "label": "投放计划",
        "description": "计划状态、预算、出价、学习阶段和转化指标",
        "enabled_by_default": True,
    },
    {
        "id": "diagnosis",
        "label": "智能诊断",
        "description": "学习失败、ROI 风险、高潜力扩量建议",
        "enabled_by_default": True,
    },
    {
        "id": "product_ads",
        "label": "商品投放",
        "description": "直播间商品、库存、价格、佣金、投放表现",
        "enabled_by_default": True,
    },
    {
        "id": "creative_library",
        "label": "素材库",
        "description": "直播切片、短视频素材、疲劳度、CTR、状态",
        "enabled_by_default": True,
    },
    {
        "id": "business_clues",
        "label": "经营线索",
        "description": "调用小宿/Cloudsway Search 发现市场、竞品、达人和平台趋势",
        "enabled_by_default": True,
    },
]


def get_agent_data_sources() -> List[Dict[str, Any]]:
    """Return data scopes that can be granted to the agent."""
    return [dict(source) for source in AGENT_DATA_SOURCES]


def _selected_source_ids(enabled_data_sources: Optional[List[str]]) -> Set[str]:
    known_sources = {source["id"] for source in AGENT_DATA_SOURCES}
    if not enabled_data_sources:
        return known_sources
    selected = set(enabled_data_sources)
    return selected & known_sources


TEXT_MODEL_PREFIXES = (
    "gpt-",
    "gpt",
    "o1",
    "o3",
    "o4",
    "claude",
    "gemini",
    "qwen",
    "deepseek",
    "glm",
    "kimi",
    "moonshot",
    "llama",
    "doubao",
    "yi-",
    "mistral",
)

NON_AGENT_MODEL_HINTS = (
    "image",
    "dall-e",
    "flux",
    "stable-diffusion",
    "sd3",
    "recraft",
    "ideogram",
    "whisper",
    "tts",
    "embedding",
    "rerank",
    "bge",
    "clip",
    "video",
    "wan",
)

VERIFIED_QIJI_CHAT_MODELS = [
    "gpt-5",
    "gpt-5.5",
    "gpt-5.5-openai-compact",
    "gpt-5-mini",
    "gpt-5-nano",
    "qwen-max",
    "deepseek-chat",
]


def _looks_like_agent_model(model_id: str) -> bool:
    model_id_lower = model_id.lower()
    if any(hint in model_id_lower for hint in NON_AGENT_MODEL_HINTS):
        return False
    return model_id_lower.startswith(TEXT_MODEL_PREFIXES)


def get_agent_model_options(model_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Return selectable chat models, keeping the verified default first."""
    default_model = get_qiji_config()["model"] or QIJI_DEFAULT_MODEL
    ordered_ids = [default_model]
    if model_ids:
        available_ids = set(model_ids)
        ordered_ids.extend([
            model_id
            for model_id in VERIFIED_QIJI_CHAT_MODELS
            if model_id in available_ids and model_id != default_model
        ])
        ordered_ids.extend(sorted(model_ids))
    else:
        ordered_ids.extend([
            model_id
            for model_id in VERIFIED_QIJI_CHAT_MODELS
            if model_id != default_model
        ])

    options = []
    seen = set()
    for model_id in ordered_ids:
        if not model_id or model_id in seen:
            continue
        if model_id != default_model and not _looks_like_agent_model(model_id):
            continue
        seen.add(model_id)
        options.append({
            "id": model_id,
            "label": model_id,
            "enabled_by_default": model_id == default_model,
            "supports_tools": True,
            "provider": "Qiji",
        })

    return options[:48]

AGENT_SYSTEM_PROMPT = """你是 MaiStream 出海直播电商投放助手「智投星」。你服务 TikTok Shop / 海外直播间运营团队，可以帮助用户：
1. 查询直播间投放、商品、素材和实时经营数据
2. 分析投放问题并给出优化建议
3. 根据用户需求创建新的广告计划或动作预览

你有以下工具可以使用：
- get_realtime_metrics: 获取当前实时经营指标
- get_metrics_trend: 获取小时级消耗与 GMV 趋势
- get_campaigns: 获取当前所有广告计划数据
- get_diagnosis: 获取智能诊断建议
- get_product_ads: 获取直播间商品投放列表
- get_creative_library: 获取素材库与素材疲劳度
- search_business_clues: 使用小宿/Cloudsway Search 搜索外部经营线索
- estimate_ad_performance / allocate_budget / simulate_live_workbench / query_backend_database / generate_marketing_content / inspect_media_api / refresh_business_knowledge: 使用 MaiDeal agent 工具层完成预估、预算分配、数据查询、内容生成、媒体 API 情报、知识检索和无真实数据模拟
- create_campaign_preview: 创建广告计划预览（用户需确认后才会真正创建）

回答时请：
- 使用中文回复
- 简洁专业，直击要点
- 如果需要创建计划，先调用 create_campaign_preview 生成预览
- 不要声称已经执行调价、暂停或创建；必须等待用户确认
- 数据展示时使用清晰的格式"""

TOOL_BY_SOURCE = {
    "realtime_metrics": {
        "type": "function",
        "function": {
            "name": "get_realtime_metrics",
            "description": "获取当前直播间投放实时指标，包括消耗、GMV、ROI、CTR、CVR、活跃计划数。当用户问现在表现、实时数据、今日概况时调用。"
        },
    },
    "trend_metrics": {
        "type": "function",
        "function": {
            "name": "get_metrics_trend",
            "description": "获取消耗、GMV、ROAS 的小时级趋势数据。当用户问趋势、峰值、时段表现、投放节奏时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "获取多少小时内的数据，默认24，范围1到168",
                    }
                },
            },
        },
    },
    "campaigns": {
        "type": "function",
        "function": {
            "name": "get_campaigns",
            "description": "获取当前所有广告计划的数据，包括名称、状态、预算、消耗、ROI等指标。当用户询问广告效果、投放数据时调用此工具。"
        },
    },
    "diagnosis": {
        "type": "function",
        "function": {
            "name": "get_diagnosis",
            "description": "获取智能诊断建议，分析当前投放问题和优化机会。当用户询问如何优化、有什么问题时调用此工具。"
        },
    },
    "product_ads": {
        "type": "function",
        "function": {
            "name": "get_product_ads",
            "description": "获取直播间商品投放列表，包括商品、国家市场、售价、库存、消耗、GMV、ROAS、转化率。当用户问商品、货盘、爆品或投放列表时调用。"
        },
    },
    "creative_library": {
        "type": "function",
        "function": {
            "name": "get_creative_library",
            "description": "获取直播间素材库，包括直播切片、短视频素材、CTR、CVR、疲劳度和可用状态。当用户问素材、创意疲劳、换素材时调用。"
        },
    },
    "business_clues": {
        "type": "function",
        "function": {
            "name": "search_business_clues",
            "description": "调用小宿/Cloudsway SmartSearch 搜索外部经营线索。适合用户询问市场趋势、竞品动态、TikTok Shop 平台变化、达人内容、选品机会、海外直播电商线索时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或自然语言问题，例如：TikTok Shop Thailand beauty livestream trends",
                    },
                    "count": {
                        "type": "integer",
                        "description": "返回结果数量，默认8，范围1到20",
                    },
                    "freshness": {
                        "type": "string",
                        "description": "时间过滤",
                        "enum": ["Day", "Week", "Month"],
                    },
                    "sites": {
                        "type": "array",
                        "description": "可选站点过滤，例如 tiktok.com、shopify.com",
                        "items": {"type": "string"},
                    },
                    "enable_content": {
                        "type": "boolean",
                        "description": "是否抓取正文片段，默认true",
                    },
                },
                "required": ["query"],
            },
        },
    },
}

ACTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_campaign_preview",
            "description": "根据用户需求生成广告计划预览，需要用户确认后才会真正创建。当用户要求创建新计划时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "计划名称，应该包含活动类型和产品信息"
                    },
                    "budget": {
                        "type": "number",
                        "description": "日预算(元)，默认5000"
                    },
                    "bid": {
                        "type": "number",
                        "description": "目标CPA出价(元)，默认65"
                    },
                    "target_type": {
                        "type": "string",
                        "description": "投放目标：商品购买、表单提交、应用下载",
                        "enum": ["商品购买", "表单提交", "应用下载"]
                    },
                    "bid_type": {
                        "type": "string",
                        "description": "出价方式",
                        "enum": ["oCPM", "CPC", "CPM"]
                    }
                },
                "required": ["name", "budget", "bid"]
            }
        }
    }
]

ACTION_TOOLS = ACTION_TOOLS + get_agent_tool_schemas()


def build_agent_tools(enabled_data_sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Build OpenAI-compatible tool schemas from selected data scopes."""
    selected_sources = _selected_source_ids(enabled_data_sources)
    tools = [
        TOOL_BY_SOURCE[source["id"]]
        for source in AGENT_DATA_SOURCES
        if source["id"] in selected_sources and source["id"] in TOOL_BY_SOURCE
    ]
    return tools + ACTION_TOOLS


AGENT_TOOLS = build_agent_tools()

# ==================== 模拟数据存储 (内存) ====================

# 初始化模拟广告计划数据
MOCK_CAMPAIGNS: Dict[int, Campaign] = {}

def init_mock_data():
    """初始化模拟数据"""
    global MOCK_CAMPAIGNS
    
    campaign_data = [
        {
            "id": 101,
            "name": "新品推广_冬季大衣_V1",
            "status": "active",
            "budget": 5000,
            "bid": 45.00,
            "spend": 3200.50,
            "impressions": 85200,
            "clicks": 2130,
            "ctr": 2.50,
            "cvr": 3.2,
            "cpa": 47.06,
            "roi": 3.8,
            "learning_stage": "passed",
            "bid_type": "oCPM"
        },
        {
            "id": 102,
            "name": "双11预热_美妆礼盒_自动出价",
            "status": "learning",
            "budget": 2000,
            "bid": 120.00,
            "spend": 450.00,
            "impressions": 12000,
            "clicks": 180,
            "ctr": 1.50,
            "cvr": 1.1,
            "cpa": 225.00,
            "roi": 0.8,
            "learning_stage": "learning",
            "bid_type": "NOBID"
        },
        {
            "id": 103,
            "name": "库存清仓_长尾流量_003",
            "status": "paused",
            "budget": 1000,
            "bid": 20.00,
            "spend": 890.00,
            "impressions": 150000,
            "clicks": 4500,
            "ctr": 3.00,
            "cvr": 0.5,
            "cpa": 39.55,
            "roi": 1.2,
            "learning_stage": "failed",
            "bid_type": "CPC"
        },
        {
            "id": 104,
            "name": "品牌曝光_春节活动_A/B测试",
            "status": "active",
            "budget": 8000,
            "bid": 80.00,
            "spend": 5600.00,
            "impressions": 220000,
            "clicks": 6600,
            "ctr": 3.00,
            "cvr": 2.8,
            "cpa": 30.27,
            "roi": 4.5,
            "learning_stage": "passed",
            "bid_type": "oCPM"
        },
        {
            "id": 105,
            "name": "定向人群_高消费用户_精准投放",
            "status": "active",
            "budget": 3000,
            "bid": 150.00,
            "spend": 1800.00,
            "impressions": 8000,
            "clicks": 320,
            "ctr": 4.00,
            "cvr": 5.5,
            "cpa": 102.27,
            "roi": 5.2,
            "learning_stage": "passed",
            "bid_type": "oCPM"
        }
    ]
    
    for data in campaign_data:
        now = datetime.now().isoformat()
        campaign = Campaign(**data, created_at=now, updated_at=now)
        MOCK_CAMPAIGNS[campaign.id] = campaign

# 启动时初始化数据
init_mock_data()


def build_realtime_metrics_snapshot() -> MetricsSnapshot:
    """Build a current metrics snapshot for API responses and agent tools."""
    campaigns = list(MOCK_CAMPAIGNS.values())
    active_campaigns = [c for c in campaigns if c.status == "active"]

    total_spend = sum(c.spend for c in campaigns)
    total_gmv = sum(c.spend * c.roi for c in campaigns)
    avg_roi = total_gmv / total_spend if total_spend > 0 else 0
    fluctuation = random.uniform(0.98, 1.02)

    return MetricsSnapshot(
        timestamp=datetime.now().isoformat(),
        total_spend=round(total_spend * fluctuation, 2),
        total_gmv=round(total_gmv * fluctuation, 2),
        roi=round(avg_roi * fluctuation, 2),
        ctr=round(random.uniform(2.8, 3.5), 2),
        cvr=round(random.uniform(2.0, 4.0), 2),
        active_campaigns=len(active_campaigns)
    )


def build_metrics_trend(hours: int = 24) -> List[Dict[str, Any]]:
    """Build hourly spend, GMV and ROAS trend data."""
    hours = max(1, min(hours, 168))
    data = []
    now = datetime.now()

    for i in range(hours):
        timestamp = now - timedelta(hours=hours - i)
        hour = timestamp.hour
        if 8 <= hour <= 10 or 19 <= hour <= 22:
            base_spend = random.uniform(3000, 5000)
        elif 0 <= hour <= 6:
            base_spend = random.uniform(500, 1500)
        else:
            base_spend = random.uniform(1500, 3000)

        roi = random.uniform(3.5, 5.0)
        data.append({
            "time": timestamp.strftime("%H:%M"),
            "date": timestamp.strftime("%Y-%m-%d"),
            "spend": round(base_spend, 2),
            "gmv": round(base_spend * roi, 2),
            "roas": round(roi, 2)
        })

    return data


def get_product_ad_rows() -> List[Dict[str, Any]]:
    """Mock live-commerce product ad rows for the agent-native page."""
    return [
        {
            "id": "sku-1021",
            "product": "Ceramide Repair Cushion Foundation",
            "market": "TH",
            "price": 19.9,
            "currency": "USD",
            "stock": 1280,
            "commission_rate": "18%",
            "spend": 2480.4,
            "gmv": 13920.8,
            "roas": 5.61,
            "ctr": 3.9,
            "cvr": 6.2,
            "status": "scaling",
            "note": "晚高峰转化稳定，可承接加预算",
        },
        {
            "id": "sku-1044",
            "product": "Vitamin C Glow Serum Set",
            "market": "VN",
            "price": 24.5,
            "currency": "USD",
            "stock": 860,
            "commission_rate": "15%",
            "spend": 1840.0,
            "gmv": 6940.3,
            "roas": 3.77,
            "ctr": 2.8,
            "cvr": 4.4,
            "status": "learning",
            "note": "素材点击正常，直播讲解转化偏低",
        },
        {
            "id": "sku-1188",
            "product": "Wireless Mini Hair Styler",
            "market": "US",
            "price": 36.0,
            "currency": "USD",
            "stock": 340,
            "commission_rate": "12%",
            "spend": 960.8,
            "gmv": 2290.0,
            "roas": 2.38,
            "ctr": 4.2,
            "cvr": 1.8,
            "status": "watch",
            "note": "库存偏低，建议限制扩量",
        },
        {
            "id": "sku-1206",
            "product": "Seamless Sculpt Leggings",
            "market": "ID",
            "price": 16.8,
            "currency": "USD",
            "stock": 2140,
            "commission_rate": "20%",
            "spend": 1220.5,
            "gmv": 7460.2,
            "roas": 6.11,
            "ctr": 5.1,
            "cvr": 7.0,
            "status": "winner",
            "note": "短视频切片带货强，适合复制到相邻人群",
        },
    ]


def get_creative_library_rows() -> List[Dict[str, Any]]:
    """Mock creative asset rows for live-room material decisions."""
    return [
        {
            "id": "crt-2301",
            "name": "主播试色_15s_高光片段",
            "type": "live_clip",
            "product": "Ceramide Repair Cushion Foundation",
            "market": "TH",
            "ctr": 4.8,
            "cvr": 6.5,
            "fatigue": 22,
            "status": "active",
            "hook": "3 秒前后脸部对比",
        },
        {
            "id": "crt-2317",
            "name": "买一送一_优惠锚点_短视频",
            "type": "short_video",
            "product": "Vitamin C Glow Serum Set",
            "market": "VN",
            "ctr": 3.1,
            "cvr": 4.0,
            "fatigue": 48,
            "status": "testing",
            "hook": "价格锚点 + 套装价值感",
        },
        {
            "id": "crt-2330",
            "name": "造型器_痛点开场_UGC",
            "type": "ugc_video",
            "product": "Wireless Mini Hair Styler",
            "market": "US",
            "ctr": 5.6,
            "cvr": 2.2,
            "fatigue": 64,
            "status": "fatiguing",
            "hook": "通勤前 5 分钟快速造型",
        },
        {
            "id": "crt-2342",
            "name": "运动裤_腰线对比_直播切片",
            "type": "live_clip",
            "product": "Seamless Sculpt Leggings",
            "market": "ID",
            "ctr": 6.4,
            "cvr": 7.6,
            "fatigue": 18,
            "status": "winner",
            "hook": "身材修饰前后对比",
        },
    ]


def _truncate_text(value: Optional[str], max_length: int = 900) -> str:
    if not value:
        return ""
    text = " ".join(str(value).split())
    if len(text) <= max_length:
        return text
    return f"{text[:max_length].rstrip()}..."


def _source_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        hostname = urlparse(url).hostname or ""
        return hostname.removeprefix("www.")
    except Exception:
        return ""


def _clue_angle(text: str) -> str:
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in ["competitor", "brand", "benchmark", "pricing", "market share", "竞品"]):
        return "竞品动态"
    if any(keyword in text_lower for keyword in ["creator", "influencer", "kol", "达人", "affiliate"]):
        return "达人/联盟线索"
    if any(keyword in text_lower for keyword in ["policy", "seller", "fee", "regulation", "平台", "规则"]):
        return "平台规则"
    if any(keyword in text_lower for keyword in ["trend", "viral", "hashtag", "直播", "短视频", "content"]):
        return "内容趋势"
    return "市场机会"


def _normalize_search_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    web_pages = payload.get("webPages", {}) if isinstance(payload, dict) else {}
    items = web_pages.get("value", []) if isinstance(web_pages, dict) else []
    results = []

    for item in items:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        main_text = item.get("mainText") or item.get("content") or ""
        results.append({
            "title": item.get("name", ""),
            "url": url,
            "source": _source_from_url(url),
            "snippet": _truncate_text(item.get("snippet", ""), 420),
            "main_text": _truncate_text(main_text, 900),
            "content_crawled": item.get("contentCrawled"),
            "score": item.get("score"),
        })

    return results


def _build_business_clues(query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clues = []
    for result in results[:6]:
        text = f"{result.get('title', '')} {result.get('snippet', '')} {result.get('main_text', '')}"
        clues.append({
            "angle": _clue_angle(text),
            "title": result.get("title", ""),
            "source": result.get("source", ""),
            "url": result.get("url", ""),
            "evidence": result.get("snippet") or _truncate_text(result.get("main_text", ""), 260),
            "next_action": f"结合「{query}」评估是否转化为直播间选品、素材或投放测试。",
        })
    return clues


def search_business_clues(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call Xiaosu/Cloudsway SmartSearch and normalize results for the agent."""
    config = get_xiaosu_search_config()
    query = str(arguments.get("query", "")).strip()
    if not query:
        return {
            "success": False,
            "type": "business_clues",
            "error": "query 不能为空",
        }

    if not config["api_key"]:
        return {
            "success": False,
            "type": "business_clues",
            "error": "CLOUDSWAY_SEARCH_KEY 或 XIAOSU_SEARCH_API_KEY 未配置，无法调用小宿/Cloudsway Search。",
            "data": {
                "query": query,
                "setup": "在 .env.hackathon 中填写 CLOUDSWAY_SEARCH_KEY 或 XIAOSU_SEARCH_API_KEY 后重启 Docker 服务。",
            },
        }

    count = int(arguments.get("count") or 8)
    count = max(1, min(count, 20))
    enable_content = arguments.get("enable_content", True)
    sites = arguments.get("sites") or []
    if isinstance(sites, str):
        sites = [sites]

    params = {
        "q": query,
        "count": count,
        "enableContent": str(bool(enable_content)).lower(),
        "contentType": "TEXT",
        "mainText": "true",
        "contentTimeout": 3,
    }

    freshness = arguments.get("freshness")
    if freshness in {"Day", "Week", "Month"}:
        params["freshness"] = freshness
    if sites:
        params["sites"] = ",".join([site.strip() for site in sites if site and site.strip()])

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                config["api_base"],
                headers={
                    "Authorization": config["api_key"],
                    "pragma": "no-cache",
                },
                params=params,
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "type": "business_clues",
            "error": f"小宿/Cloudsway Search HTTP {exc.response.status_code}: {_truncate_text(exc.response.text, 240)}",
            "data": {"query": query},
        }
    except Exception as exc:
        return {
            "success": False,
            "type": "business_clues",
            "error": f"小宿/Cloudsway Search 调用失败: {str(exc)}",
            "data": {"query": query},
        }

    results = _normalize_search_results(payload)
    return {
        "success": True,
        "type": "business_clues",
        "data": {
            "query": query,
            "original_query": payload.get("queryContext", {}).get("originalQuery", query),
            "results": results,
            "clues": _build_business_clues(query, results),
        },
        "count": len(results),
    }

# ==================== API 路由 ====================

# ---------- 健康检查 ----------

@app.get("/", tags=["System"])
async def root():
    """API 根路由"""
    return {
        "service": "GrowEngine API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", tags=["System"])
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ---------- 广告计划管理 ----------

@app.get("/api/campaigns", response_model=List[Campaign], tags=["Campaigns"])
async def list_campaigns(
    status: Optional[str] = Query(None, description="按状态过滤"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """获取广告计划列表"""
    campaigns = list(MOCK_CAMPAIGNS.values())
    
    if status:
        campaigns = [c for c in campaigns if c.status == status]
    
    return campaigns[offset:offset + limit]

@app.get("/api/campaigns/{campaign_id}", response_model=Campaign, tags=["Campaigns"])
async def get_campaign(campaign_id: int):
    """获取单个广告计划详情"""
    if campaign_id not in MOCK_CAMPAIGNS:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return MOCK_CAMPAIGNS[campaign_id]

@app.post("/api/campaigns", response_model=Campaign, tags=["Campaigns"])
async def create_campaign(request: CampaignCreate):
    """创建新广告计划"""
    new_id = max(MOCK_CAMPAIGNS.keys(), default=100) + 1
    now = datetime.now().isoformat()
    
    new_campaign = Campaign(
        id=new_id,
        name=request.name,
        budget=request.budget,
        bid=request.bid,
        bid_type=request.bid_type,
        status="learning",
        learning_stage="learning",
        spend=0,
        impressions=0,
        clicks=0,
        ctr=0,
        cvr=0,
        cpa=0,
        roi=0,
        created_at=now,
        updated_at=now
    )
    
    MOCK_CAMPAIGNS[new_id] = new_campaign
    return new_campaign

@app.put("/api/campaigns/{campaign_id}", response_model=Campaign, tags=["Campaigns"])
async def update_campaign(campaign_id: int, request: CampaignUpdate):
    """更新广告计划"""
    if campaign_id not in MOCK_CAMPAIGNS:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    campaign = MOCK_CAMPAIGNS[campaign_id]
    update_data = request.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    campaign.updated_at = datetime.now().isoformat()
    MOCK_CAMPAIGNS[campaign_id] = campaign
    return campaign

@app.delete("/api/campaigns/{campaign_id}", tags=["Campaigns"])
async def delete_campaign(campaign_id: int):
    """删除广告计划"""
    if campaign_id not in MOCK_CAMPAIGNS:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    del MOCK_CAMPAIGNS[campaign_id]
    return {"message": f"Campaign {campaign_id} deleted successfully"}

@app.post("/api/campaigns/{campaign_id}/toggle", response_model=Campaign, tags=["Campaigns"])
async def toggle_campaign_status(campaign_id: int):
    """切换广告计划状态 (启用/暂停)"""
    if campaign_id not in MOCK_CAMPAIGNS:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    campaign = MOCK_CAMPAIGNS[campaign_id]
    
    if campaign.status == "paused":
        campaign.status = "active"
    else:
        campaign.status = "paused"
    
    campaign.updated_at = datetime.now().isoformat()
    return campaign

# ---------- 实时数据 ----------

@app.get("/api/metrics/realtime", response_model=MetricsSnapshot, tags=["Metrics"])
async def get_realtime_metrics():
    """获取实时指标数据"""
    return build_realtime_metrics_snapshot()

@app.get("/api/metrics/trend", tags=["Metrics"])
async def get_metrics_trend(
    hours: int = Query(24, ge=1, le=168, description="获取多少小时内的趋势数据")
):
    """获取趋势数据 (用于图表展示)"""
    return build_metrics_trend(hours)

# ---------- 竞价服务 ----------

@app.post("/api/bidding/calculate", response_model=BidResponse, tags=["Bidding"])
async def calculate_bid(request: BidRequest):
    """计算竞价出价"""
    if request.campaign_id not in MOCK_CAMPAIGNS:
        raise HTTPException(status_code=404, detail=f"Campaign {request.campaign_id} not found")
    
    campaign = MOCK_CAMPAIGNS[request.campaign_id]
    
    # 使用 OnlineLp 策略计算出价: bid = alpha * pValue
    # 这里 alpha 约等于 CPA 目标
    alpha = campaign.bid
    bid_price = alpha * request.p_value
    
    # 模拟获胜概率 (基于出价和市场竞争)
    win_probability = min(0.95, 0.3 + bid_price / 200)
    
    # 预估转化
    estimated_conversion = request.p_value * win_probability
    
    return BidResponse(
        bid_price=round(bid_price, 4),
        win_probability=round(win_probability, 4),
        estimated_conversion=round(estimated_conversion, 6)
    )

@app.post("/api/bidding/simulate", tags=["Bidding"])
async def simulate_auction(campaign_id: int, steps: int = Query(48, ge=1, le=100)):
    """模拟竞价过程"""
    if campaign_id not in MOCK_CAMPAIGNS:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    campaign = MOCK_CAMPAIGNS[campaign_id]
    results = []
    
    total_cost = 0
    total_conversions = 0
    total_wins = 0
    remaining_budget = campaign.budget
    cpa_constraint = campaign.bid * 1.5  # 模拟 CPA 约束
    
    # 模拟 alpha 变化曲线 (先升后降或波动)
    base_alpha = campaign.bid
    
    for step in range(steps):
        # 模拟 Alpha 动态调整
        progress = step / steps
        alpha_factor = 1.0 + 0.3 * math.sin(progress * math.pi * 2) + random.uniform(-0.1, 0.1)
        current_alpha = base_alpha * alpha_factor
        
        # 模拟每个时间步的流量
        # 早高峰(8-10点)和晚高峰(19-22点)流量大
        hour_equiv = (step / steps) * 24
        is_peak = (8 <= hour_equiv <= 10) or (19 <= hour_equiv <= 22)
        traffic_count = random.randint(150, 300) if is_peak else random.randint(50, 120)
        
        step_cost = 0
        step_conversions = 0
        step_wins = 0
        
        for _ in range(traffic_count):
            p_value = random.uniform(0.001, 0.08)
            bid_price = current_alpha * p_value
            
            # 模拟市场竞争价格
            market_price = random.uniform(0.5, bid_price * 1.3)
            
            if bid_price >= market_price:
                # 预算控制
                if step_cost + market_price <= remaining_budget:
                    step_wins += 1
                    step_cost += market_price
                    
                    # 模拟转化
                    if random.random() < p_value:
                        step_conversions += 1
        
        remaining_budget -= step_cost
        total_cost += step_cost
        total_conversions += step_conversions
        total_wins += step_wins
        
        real_cpa = total_cost / max(total_conversions, 1)
        
        results.append({
            "step": step,
            "alpha": round(current_alpha, 2),
            "traffic": traffic_count,
            "wins": step_wins,
            "cost": round(step_cost, 2),
            "conversions": step_conversions,
            "total_cost": round(total_cost, 2),
            "total_wins": total_wins,
            "total_conversions": total_conversions,
            "real_cpa": round(real_cpa, 2),
            "remaining_budget": round(remaining_budget, 2),
            "budget_percentage": round((campaign.budget - remaining_budget) / campaign.budget * 100, 1),
            "roi": round((total_conversions * 150) / max(total_cost, 1), 2)  # 假设客单价 150
        })
    
    return {
        "meta": {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "budget": campaign.budget,
            "cpa_constraint": round(cpa_constraint, 2)
        },
        "history": results
    }

# ---------- AI 诊断服务 ----------

@app.get("/api/diagnosis", response_model=List[DiagnosticItem], tags=["AI Diagnosis"])
async def get_diagnosis():
    """获取智能诊断建议"""
    campaigns = list(MOCK_CAMPAIGNS.values())
    diagnostics = []
    
    for campaign in campaigns:
        # 检测学习失败
        if campaign.learning_stage == "failed":
            diagnostics.append(DiagnosticItem(
                type="warning",
                title=f"计划 [{campaign.name[:15]}...] 学习失败",
                description=f"该计划冷启动失败，当前 CTR {campaign.ctr}% 低于行业均值。建议检查定向人群或提高出价。",
                action="一键优化设置",
                priority=1
            ))
        
        # 检测 ROI 过低
        if campaign.roi < 1.0 and campaign.status == "active":
            diagnostics.append(DiagnosticItem(
                type="warning",
                title=f"计划 [{campaign.name[:15]}...] ROI 低于盈亏线",
                description=f"当前 ROI 仅为 {campaign.roi}，低于 1.0 盈亏平衡点。持续投放将造成亏损。",
                action="暂停计划",
                priority=1
            ))
        
        # 发现高潜力
        if campaign.roi > 4.0 and campaign.spend < campaign.budget * 0.5:
            diagnostics.append(DiagnosticItem(
                type="opportunity",
                title=f"高潜力计划 [{campaign.name[:15]}...]",
                description=f"该计划 ROI 达到 {campaign.roi}，但预算消耗仅 {campaign.spend/campaign.budget*100:.1f}%，存在起量空间。",
                action="提升出价 +15%",
                priority=2
            ))
    
    # 通用建议
    if not diagnostics:
        diagnostics.append(DiagnosticItem(
            type="success",
            title="投放状态良好",
            description="当前所有计划运行正常，暂无异常需要处理。",
            action="查看详细报告",
            priority=3
        ))
    
    return sorted(diagnostics, key=lambda x: x.priority)

# ---------- AI 助手 ----------

@app.post("/api/ai/chat", tags=["AI Assistant"])
async def ai_chat(message: str = Query(..., min_length=1)):
    """AI 助手对话接口"""

    # 简单的关键词匹配响应 (生产环境应接入真正的 LLM)
    responses = {
        "roi": "根据您的投放数据分析，目前计划「新品推广_冬季大衣_V1」表现最佳，ROI达到3.8。建议继续加大预算。",
        "消耗": "近7天整体消耗趋势上升12%，GMV增长24%。投放效率持续优化中。主力消耗计划为「品牌曝光_春节活动」。",
        "学习": "系统检测到您有1条计划正在冷启动中，预计24小时内完成学习期。建议保持当前出价不变。",
        "素材": "检测到素材「Video_003」点击率连续3天下滑，建议更换创意素材或调整投放人群。",
        "出价": "当前建议出价区间为 ¥40-80 (oCPM模式)。系统将根据实时竞争环境自动调整。",
        "人群": "系统发现 [精致妈妈] 人群在同类商品中转化率极高，但在当前投放中占比不足5%。建议添加该定向包。"
    }

    # 匹配关键词
    for keyword, response in responses.items():
        if keyword in message.lower():
            return {"response": response, "source": "keyword_match"}

    # 默认响应
    default_responses = [
        "根据您的描述，我建议您查看「智能诊断」面板获取更详细的分析。",
        "让我帮您分析一下...目前系统运行正常，如需具体指标请告诉我计划名称或 ID。",
        "您好！我可以帮您分析投放效果、调整出价策略、诊断问题。请问具体想了解什么？"
    ]

    return {
        "response": random.choice(default_responses),
        "source": "default"
    }


@app.get("/api/agent-mode/workbench", tags=["Agent Mode"])
def get_agent_mode_workbench(project_id: Optional[str] = None):
    """Read the Agent Mode workbench data boundary."""
    repository = create_agent_mode_repository()
    if repository.enabled:
        try:
            return repository.build_workbench(project_id=project_id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Agent Mode persistence error: {exc}") from exc
    return read_workbench()


@app.put("/api/agent-mode/workbench", tags=["Agent Mode"])
def update_agent_mode_workbench(payload: Dict[str, Any]):
    """Update the Agent Mode workbench seed store."""
    return write_workbench(payload)


@app.get("/api/ai/data-sources", tags=["AI Agent"])
async def list_agent_data_sources():
    """获取 Agent 可访问的数据源列表。"""
    return {
        "data_sources": get_agent_data_sources(),
        "default_enabled": [source["id"] for source in AGENT_DATA_SOURCES if source["enabled_by_default"]],
    }


@app.get("/api/ai/models", tags=["AI Agent"])
async def list_agent_models():
    """获取 Qiji/OpenAI-compatible 可选模型列表。"""
    config = get_qiji_config()

    if not config["api_key"]:
        return {
            "default_model": config["model"],
            "models": get_agent_model_options(),
            "source": "fallback",
            "message": "QIJI_API_KEY 未配置，已使用 qiji_api.md 中验证过的 gpt-5 作为默认模型。配置 key 后会自动读取 /models。",
        }

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=config["api_key"],
            base_url=config["api_base"],
            default_headers={"User-Agent": "curl/8.5.0"},
        )
        models_page = await client.models.list()
        model_ids = [model.id for model in models_page.data if getattr(model, "id", None)]
        return {
            "default_model": config["model"],
            "models": get_agent_model_options(model_ids),
            "source": "qiji",
        }
    except Exception as exc:
        return {
            "default_model": config["model"],
            "models": get_agent_model_options(),
            "source": "fallback",
            "message": f"读取 Qiji /models 失败，已回退到默认模型: {str(exc)}",
        }

# ---------- Agent 工具执行 ----------

def execute_tool(tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行 Agent 工具调用"""
    arguments = arguments or {}

    if tool_name == "get_realtime_metrics":
        snapshot = build_realtime_metrics_snapshot()
        return {
            "success": True,
            "data": snapshot.model_dump(),
        }

    elif tool_name == "get_metrics_trend":
        hours = int(arguments.get("hours", 24) or 24)
        trend = build_metrics_trend(hours)
        return {
            "success": True,
            "data": trend,
            "count": len(trend),
        }

    if tool_name == "get_campaigns":
        # 获取所有广告计划数据
        campaigns = list(MOCK_CAMPAIGNS.values())
        campaign_list = []
        for c in campaigns:
            campaign_list.append({
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "budget": c.budget,
                "spend": c.spend,
                "roi": c.roi,
                "ctr": c.ctr,
                "cvr": c.cvr,
                "learning_stage": c.learning_stage
            })
        return {
            "success": True,
            "data": campaign_list,
            "count": len(campaign_list)
        }

    elif tool_name == "get_diagnosis":
        # 获取诊断建议
        campaigns = list(MOCK_CAMPAIGNS.values())
        diagnostics = []

        for campaign in campaigns:
            if campaign.learning_stage == "failed":
                diagnostics.append({
                    "type": "warning",
                    "title": f"计划 [{campaign.name[:15]}...] 学习失败",
                    "suggestion": "检查定向人群或提高出价"
                })
            if campaign.roi < 1.0 and campaign.status == "active":
                diagnostics.append({
                    "type": "warning",
                    "title": f"计划 [{campaign.name[:15]}...] ROI 低于盈亏线",
                    "suggestion": "考虑暂停或优化"
                })
            if campaign.roi > 4.0 and campaign.spend < campaign.budget * 0.5:
                diagnostics.append({
                    "type": "opportunity",
                    "title": f"高潜力计划 [{campaign.name[:15]}...]",
                    "suggestion": f"ROI达到{campaign.roi}，建议提升出价抢量"
                })

        return {
            "success": True,
            "data": diagnostics,
            "count": len(diagnostics)
        }

    elif tool_name == "get_product_ads":
        rows = get_product_ad_rows()
        return {
            "success": True,
            "data": rows,
            "count": len(rows),
        }

    elif tool_name == "get_creative_library":
        rows = get_creative_library_rows()
        return {
            "success": True,
            "data": rows,
            "count": len(rows),
        }

    elif tool_name == "search_business_clues":
        return search_business_clues(arguments)

    elif tool_name == "create_campaign_preview":
        # 创建计划预览（不实际创建，返回预览数据）
        args = arguments
        preview = {
            "name": args.get("name", f"新建计划_{datetime.now().strftime('%m%d')}"),
            "budget": args.get("budget", 5000),
            "bid": args.get("bid", 65),
            "target_type": args.get("target_type", "商品购买"),
            "bid_type": args.get("bid_type", "oCPM"),
            "estimated_impressions": int(args.get("budget", 5000) / args.get("bid", 65) * 1000 * 1.5),
            "estimated_conversions": int(args.get("budget", 5000) / args.get("bid", 65) * 0.8)
        }
        return {
            "success": True,
            "type": "campaign_preview",
            "data": preview,
            "message": "计划预览已生成，等待用户确认创建"
        }

    registry_result = dispatch_agent_tool(tool_name, arguments)
    if registry_result.get("success") or not registry_result.get("error", "").startswith("未知 agent 工具"):
        return registry_result

    return {"success": False, "error": f"未知工具: {tool_name}"}

# ---------- Agent 对话接口 (流式响应) ----------

@app.post("/api/ai/agent", tags=["AI Agent"])
async def agent_chat(request: AgentChatRequest):
    """
    Agentic AI 对话接口 - 支持 SSE 流式响应和工具调用

    该接口会：
    1. 将用户消息发送给 LLM
    2. 如果 LLM 决定调用工具，执行工具并将结果返回给 LLM
    3. 流式返回 LLM 的最终回复
    """

    async def generate_stream():
        try:
            from openai import AsyncOpenAI

            config = get_qiji_config()
            selected_model = (
                request.model
                or (request.models[0] if request.models else None)
                or config["model"]
                or QIJI_DEFAULT_MODEL
            )

            if not config["api_key"]:
                yield f"data: {json.dumps({'type': 'error', 'content': 'QIJI_API_KEY 未配置，无法调用 Qiji/OpenAI-compatible 模型。请在 .env.hackathon 中填写后重启容器。'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
            messages.extend(request.messages)

            client = AsyncOpenAI(
                api_key=config["api_key"],
                base_url=config["api_base"],
                default_headers={"User-Agent": "curl/8.5.0"},
                timeout=120.0,
            )

            yield f"data: {json.dumps({'type': 'model', 'model': selected_model}, ensure_ascii=False)}\n\n"

            tools = build_agent_tools(request.enabled_data_sources) if request.enable_tools else []
            first_call_kwargs = {
                "model": selected_model,
                "messages": messages,
                "stream": False,
                "max_completion_tokens": 900,
                "extra_body": {"reasoning_effort": "minimal"},
            }
            if tools:
                first_call_kwargs["tools"] = tools

            completion = await client.chat.completions.create(**first_call_kwargs)
            choice = completion.choices[0] if completion.choices else None
            assistant_message = choice.message if choice else None
            tool_calls = assistant_message.tool_calls if assistant_message else []

            if tool_calls:
                messages.append(assistant_message.model_dump(exclude_none=True))

                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        tool_args = {}

                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'arguments': tool_args}, ensure_ascii=False)}\n\n"

                    tool_result = execute_tool(tool_name, tool_args)
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': tool_result}, ensure_ascii=False)}\n\n"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })
            elif assistant_message and assistant_message.content:
                yield f"data: {json.dumps({'type': 'content', 'content': assistant_message.content}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            stream = await client.chat.completions.create(
                model=selected_model,
                messages=messages,
                stream=True,
                max_completion_tokens=900,
                extra_body={"reasoning_effort": "minimal"},
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", "") or ""
                if content:
                    yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except ImportError:
            yield f"data: {json.dumps({'type': 'error', 'content': '后端缺少 openai Python SDK，请重新构建 Docker 镜像。'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type': 'error', 'content': 'LLM 请求超时，请稍后重试'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'服务异常: {str(e)}'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ---------- Orchestrator 对话接口 ----------

@app.post("/api/orchestrator/chat", tags=["Orchestrator"])
async def orchestrator_chat_endpoint(request: AgentChatRequest):
    """Orchestrator 多 Agent 编排对话 — SSE 流式响应"""
    workbench = read_workbench()
    return StreamingResponse(
        orchestrator_chat(request.messages, workbench),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/workbench/reset", tags=["Orchestrator"])
async def reset_workbench_endpoint():
    """重置工作台到初始 briefing 状态"""
    wb = reset_workbench()
    return {"ok": True, "workbench": wb}


@app.get("/api/workbench/state", tags=["Orchestrator"])
async def get_workbench_state():
    """获取完整工作台状态"""
    return {"ok": True, "workbench": read_workbench()}


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
