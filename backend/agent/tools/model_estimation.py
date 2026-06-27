"""Ad performance estimation tool with optional ad_rec_backend signals."""

from __future__ import annotations

import math
from typing import Any, Dict, List


def estimate_ad_performance(arguments: Dict[str, Any]) -> Dict[str, Any]:
    product = str(arguments.get("product") or "商品")
    category = str(arguments.get("category") or _infer_category(product))
    budget = float(arguments.get("budget") or 1000)
    channels = _channels(arguments.get("channels"))
    audience_size = int(arguments.get("audience_size") or 120000)
    aov = float(arguments.get("average_order_value") or _aov_for_category(category))
    ad_signals = _load_ad_rec_signals(category)

    channel_rows = []
    for index, channel in enumerate(channels):
        signal = ad_signals[index % len(ad_signals)] if ad_signals else {}
        base_ctr = float(signal.get("ctr") or _base_ctr(channel, category))
        cpc = _cpc_for_channel(channel, category)
        channel_budget = budget / len(channels)
        clicks = min(audience_size * base_ctr, channel_budget / cpc)
        cvr = _cvr_for_category(category) * (1 + min(base_ctr, 0.2))
        conversions = clicks * cvr
        gmv = conversions * aov
        channel_rows.append({
            "channel": channel,
            "ad_signal": signal.get("title") or f"{category} baseline",
            "estimated_ctr": round(base_ctr, 4),
            "estimated_clicks": round(clicks),
            "estimated_conversions": round(conversions, 1),
            "estimated_gmv": round(gmv, 2),
            "estimated_roi": round(gmv / max(channel_budget, 1), 2),
            "recommended_bid": round(cpc * 1.15, 2),
        })

    total_gmv = sum(row["estimated_gmv"] for row in channel_rows)
    return {
        "success": True,
        "engine": "ad_rec_backend-compatible",
        "product": product,
        "category": category,
        "budget": budget,
        "estimated_gmv": round(total_gmv, 2),
        "estimated_roi": round(total_gmv / max(budget, 1), 2),
        "channels": channel_rows,
        "notes": [
            "优先使用 ad_rec_backend 中同类目广告 CTR 作为先验。",
            "真实投放前仍需用直播间历史转化率和渠道报表校准。",
        ],
    }


def _load_ad_rec_signals(category: str) -> List[Dict[str, Any]]:
    try:
        from ad_rec_backend.data_manager import DataManager
    except Exception:
        return []
    try:
        manager = DataManager.get_instance()
        if not manager.ads:
            manager.load_data()
        ads = manager.get_ads_by_category(category, size=5) or manager.get_top_ads(5, sort_by="ctr")
        return [ad.to_dict() for ad in ads[:5]]
    except Exception:
        return []


def _channels(raw: Any) -> List[str]:
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    if isinstance(raw, str) and raw.strip():
        parts = [part.strip() for part in raw.replace("、", "+").replace("/", "+").split("+")]
        return [part for part in parts if part]
    return ["TikTok Ads", "Meta Ads"]


def _infer_category(product: str) -> str:
    lower = product.lower()
    if any(word in lower for word in ["手机", "phone", "case", "壳"]):
        return "accessory"
    if any(word in lower for word in ["美妆", "beauty", "护肤"]):
        return "beauty"
    if any(word in lower for word in ["杯", "家居", "home"]):
        return "home"
    return "electronics"


def _aov_for_category(category: str) -> float:
    return {"accessory": 18, "beauty": 35, "home": 42, "electronics": 68}.get(category, 39)


def _base_ctr(channel: str, category: str) -> float:
    channel_lower = channel.lower()
    base = {"accessory": 0.028, "beauty": 0.034, "home": 0.024, "electronics": 0.019}.get(category, 0.022)
    if "tiktok" in channel_lower:
        base *= 1.2
    elif "shopee" in channel_lower:
        base *= 1.05
    elif "meta" in channel_lower:
        base *= 0.96
    return base


def _cvr_for_category(category: str) -> float:
    return {"accessory": 0.035, "beauty": 0.028, "home": 0.024, "electronics": 0.018}.get(category, 0.022)


def _cpc_for_channel(channel: str, category: str) -> float:
    channel_lower = channel.lower()
    base = 0.22 if category == "accessory" else 0.38
    if "meta" in channel_lower:
        return base * 1.15
    if "shopee" in channel_lower:
        return base * 0.9
    return base
