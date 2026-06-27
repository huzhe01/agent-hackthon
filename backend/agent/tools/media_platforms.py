"""Media platform RTA/RTB/API acquisition helper."""

from __future__ import annotations

from typing import Any, Dict, List


PLATFORM_CATALOG = {
    "巨量引擎": {
        "official_url": "https://open.oceanengine.com/",
        "doc_url": "https://open.oceanengine.com/labels/7/docs/1696710749917196",
        "capabilities": ["OAuth/应用授权", "广告主账号", "计划/素材/报表 API", "RTA/转化归因能力申请"],
        "requires": ["开发者账号", "广告主授权", "应用审核", "回调服务域名", "行业资质"],
        "next_steps": [
            "在巨量引擎开放平台创建应用并申请广告投放相关权限。",
            "完成广告主账号授权，保存 access_token 与 advertiser_id。",
            "RTA/RTB 类能力通常需要商务白名单、回调 URL 和联调验收。",
        ],
    },
    "巨量千川": {
        "official_url": "https://open.oceanengine.com/",
        "doc_url": "https://open.oceanengine.com/labels/8/docs/1708428054592516",
        "capabilities": ["千川账号授权", "直播/商品推广计划管理", "报表查询", "转化数据回传"],
        "requires": ["千川主体资质", "抖音电商/店铺授权", "应用权限包", "联调环境"],
        "next_steps": [
            "确认账户是千川投放主体并接入开放平台权限。",
            "先打通计划、素材、报表接口，再评估实时竞价/人群回传接口。",
            "对接真实 RTA 前，需要确认平台是否开放白名单。",
        ],
    },
    "聚光": {
        "official_url": "https://ad.xiaohongshu.com/openApiDoc",
        "doc_url": "https://ad.xiaohongshu.com/openApiDoc?articleId=3047&categoryId=761",
        "capabilities": ["小红书聚光开放 API", "广告主授权", "计划/创意/报表", "素材与线索数据"],
        "requires": ["聚光广告主账号", "开发者应用", "API 权限申请", "品牌/行业资质"],
        "next_steps": [
            "在聚光开放文档确认账号权限与接口范围。",
            "先接广告报表和素材接口，沉淀投放效果数据。",
            "RTA/RTB 若需实时出价或人群决策，应向平台商务申请专项权限。",
        ],
    },
}


ALIASES = {
    "小红书": "聚光",
    "小红书聚光": "聚光",
    "oceanengine": "巨量引擎",
    "千川": "巨量千川",
}


def inspect_media_api(arguments: Dict[str, Any]) -> Dict[str, Any]:
    raw_platforms = arguments.get("platforms") or ["巨量引擎", "巨量千川", "聚光"]
    capability = str(arguments.get("capability") or "RTA/RTB")
    platforms = []
    for raw in raw_platforms:
        name = ALIASES.get(str(raw).strip(), str(raw).strip())
        data = PLATFORM_CATALOG.get(name)
        if not data:
            platforms.append({
                "name": name,
                "official_url": "",
                "requires": ["需要先确认平台开放文档和商务权限"],
                "next_steps": ["补充平台名称后再查询。"],
                "status": "unknown",
            })
            continue
        platforms.append({
            "name": name,
            "requested_capability": capability,
            "official_url": data["official_url"],
            "doc_url": data["doc_url"],
            "capabilities": data["capabilities"],
            "requires": data["requires"],
            "next_steps": data["next_steps"],
            "status": "permission_gated",
        })
    return {
        "success": True,
        "capability": capability,
        "platforms": platforms,
        "integration_principle": "先打通授权、报表和素材数据，再申请实时人群/竞价类白名单；不要在未授权时模拟真实投放执行。",
    }
