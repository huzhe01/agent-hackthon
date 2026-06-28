"""Deterministic data simulator for the Agent Mode workbench."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import random
import re
from typing import Any, Dict, List


CORE_FIELDS = ("budget", "target_roas", "products", "market", "channels")


def validate_simulation_brief(brief: Dict[str, Any]) -> Dict[str, Any]:
    missing = [field for field in CORE_FIELDS if not _present(brief.get(field))]
    return {"complete": not missing, "missing": missing}


def build_simulation_bundle(brief: Dict[str, Any], version_number: int = 1) -> Dict[str, Any]:
    normalized = normalize_brief(brief)
    seed = _seed_for(normalized, version_number)
    rng = random.Random(seed)
    product_catalog = _build_product_catalog(normalized, rng)
    plan_options = _build_plan_options(normalized)
    recommended_plan = next(plan for plan in plan_options if plan.get("recommended"))
    channel_pools = _build_channel_pools(normalized, recommended_plan)
    live_demo = _build_live_demo(normalized, product_catalog, channel_pools, rng)
    events = _collect_events(live_demo["frames"])
    review = _build_review(normalized, live_demo, events)
    live_rooms = _build_live_rooms(normalized, plan_options)

    return {
        "simulator_seed": seed,
        "brief": normalized,
        "product_catalog": product_catalog,
        "channel_pools": channel_pools,
        "plan_options": plan_options,
        "live_rooms": live_rooms,
        "live_demo": live_demo,
        "all_events": events,
        "managed_events": events[-8:],
        "review": review,
        "review_benchmarks": review["benchmarks"],
        "review_actions": review["key_actions"],
        "strategy_notes": review["strategy_notes"],
        "lead_rows": review["lead_assets"],
        "fallback_campaigns": _build_campaigns(product_catalog),
    }


def normalize_brief(brief: Dict[str, Any]) -> Dict[str, Any]:
    budget = _as_float(brief.get("budget"), 5000)
    target_roas = _as_float(brief.get("target_roas"), 3.0)
    product = str(brief.get("products") or "商品").strip()
    market = str(brief.get("market") or "美国 / USD").strip()
    channels = normalize_channels(brief.get("channels"))
    channel_weights = normalize_channel_weights(brief.get("channels"), channels)
    inventory = max(100, int(_as_float(brief.get("inventory"), 1200)))
    margin_rate = _as_float(brief.get("margin"), 55)
    if margin_rate > 1:
        margin_rate = margin_rate / 100
    return {
        "budget": round(budget),
        "target_roas": target_roas,
        "products": product,
        "market": market,
        "currency": _currency_from_market(market),
        "channels": channels,
        "channel_weights": channel_weights,
        "live_window": brief.get("live_window") or "20:00-23:00",
        "inventory": inventory,
        "margin_rate": round(margin_rate, 2),
        "constraints": brief.get("constraints") or "",
    }


def normalize_channels(raw: Any) -> List[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    candidates = re.split(r"[,，/+、]|\\s+and\\s+|\\s+与\\s+|\\s+和\\s+", text, flags=re.I)
    labels = []
    for candidate in candidates:
        value = re.sub(r"\b\d{1,3}\s*%", "", candidate).strip()
        if not value or value in {"各 50%", "各50%"}:
            continue
        lower = value.lower()
        if "tiktok" in lower:
            label = "TikTok Ads"
        elif "facebook" in lower or lower in {"fb"}:
            label = "Facebook Ads"
        elif "meta" in lower:
            label = "Meta Ads"
        elif "shopee" in lower:
            label = "Shopee Ads"
        elif "google" in lower:
            label = "Google Ads"
        elif "amazon" in lower:
            label = "Amazon Ads"
        else:
            label = value if value.endswith("Ads") else f"{value} Ads"
        if label not in labels:
            labels.append(label)
    return labels


def normalize_channel_weights(raw: Any, channels: List[str]) -> Dict[str, int]:
    text = str(raw or "")
    percentages = [int(value) for value in re.findall(r"(\d{1,3})\s*%", text)]
    if not channels or len(percentages) < len(channels):
        return {}
    weights = percentages[:len(channels)]
    total = sum(weights)
    if total <= 0:
        return {}
    normalized = {channel: round(weight * 100 / total) for channel, weight in zip(channels, weights)}
    drift = 100 - sum(normalized.values())
    normalized[channels[-1]] += drift
    return normalized


def _build_product_catalog(brief: Dict[str, Any], rng: random.Random) -> List[Dict[str, Any]]:
    base = brief["products"]
    category = _category_for(base)
    price_ranges = {
        "electronics": (29, 89),
        "beauty": (12, 59),
        "fashion": (19, 129),
        "home": (15, 99),
        "accessory": (8, 49),
    }
    low, high = price_ranges.get(category, (12, 79))
    suffixes = ["Pro", "Mini", "套装", "基础款", "限量款"]
    inventory_remaining = brief["inventory"]
    skus = []
    for index, suffix in enumerate(suffixes):
        price = rng.randint(low, high)
        if suffix == "套装":
            price = round(price * 1.8)
        inventory = max(20, round(brief["inventory"] * rng.uniform(0.12, 0.28)))
        inventory_remaining -= inventory
        skus.append({
            "id": f"sku-{index + 1}",
            "sku_code": f"{_slug(base)}-{index + 1:02d}".upper(),
            "sku": f"{_slug(base)}-{index + 1:02d}".upper(),
            "name": f"{base} {suffix}",
            "category": category,
            "price": price,
            "base_inventory": inventory,
            "margin_rate": brief["margin_rate"],
            "attributes": {"variant": suffix, "market": brief["market"]},
        })
    if inventory_remaining > 0:
        skus[0]["base_inventory"] += inventory_remaining
    return skus


def _build_plan_options(brief: Dict[str, Any]) -> List[Dict[str, Any]]:
    modes = [
        ("steady", "保守", 0.9, "匀速投放，优先控制风险"),
        ("balanced", "均衡", 1.0, "前段测试，直播高峰加码", True),
        ("aggressive", "进取", 1.12, "高峰抢量，接受更高波动"),
    ]
    plans = []
    for item in modes:
        plan_id, title, roas_factor, rhythm = item[:4]
        recommended = bool(item[4]) if len(item) > 4 else False
        split = _channel_split(brief["channels"], plan_id, brief.get("channel_weights"))
        split_text = " / ".join(f"{label.replace(' Ads', '')} {pct}%" for label, pct in split.items())
        expected_low = brief["target_roas"] * (roas_factor - 0.08)
        expected_high = brief["target_roas"] * (roas_factor + 0.12)
        plans.append({
            "id": plan_id,
            "title": title,
            "recommended": recommended,
            "lines": [
                split_text,
                f"节奏：{rhythm}",
                f"预期 ROAS {expected_low:.1f}-{expected_high:.1f}",
                "推荐" if recommended else "可选方案",
            ],
            "channels_split": split,
            "budget": brief["budget"],
            "expected_roas": f"{expected_low:.1f}-{expected_high:.1f}",
            "rhythm": rhythm,
            "risks": "风险中等" if recommended else ("增长慢" if plan_id == "steady" else "波动较大"),
        })
    return plans


def _build_channel_pools(brief: Dict[str, Any], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    pools = []
    allocated = 0
    tones = ["cyan", "violet", "amber", "emerald"]
    channels = brief["channels"]
    for index, channel in enumerate(channels):
        if index == len(channels) - 1:
            total = brief["budget"] - allocated
        else:
            total = round(brief["budget"] * plan["channels_split"][channel] / 100)
            allocated += total
        pools.append({
            "id": _channel_id(channel),
            "label": channel,
            "spent": 0,
            "total": total,
            "remaining": total,
            "tone": tones[index % len(tones)],
        })
    return pools


def _build_live_demo(
    brief: Dict[str, Any],
    products: List[Dict[str, Any]],
    base_pools: List[Dict[str, Any]],
    rng: random.Random,
) -> Dict[str, Any]:
    frame_count = 8
    frames = []
    total_budget = sum(pool["total"] for pool in base_pools)
    spend_curve = _spend_curve(total_budget, frame_count)
    sold_units_by_sku = {product["id"]: 0 for product in products}
    for index in range(frame_count):
        progress = index / (frame_count - 1)
        spend = spend_curve[index]
        roas_factor = 0.72 + progress * 0.55 + rng.uniform(-0.08, 0.08)
        if index in {2, 4}:
            roas_factor -= 0.28
        revenue = round(spend * max(0, brief["target_roas"] * roas_factor))
        budget_pool = _spend_pools(base_pools, spend)
        sku_ads = _sku_frame(products, revenue, spend, sold_units_by_sku, rng, index)
        revenue = sum(item["gmv"] for item in sku_ads)
        spend = sum(pool["spent"] for pool in budget_pool)
        sold_total = sum(item["units"] for item in sku_ads)
        inventory = max(0, brief["inventory"] - sold_total)
        roas = round(revenue / spend, 1) if spend else 0
        frame_time = _frame_time(index)
        alerts = _frame_alerts(index, roas, brief, budget_pool, total_budget)
        events = _frame_events(index, roas, alerts, budget_pool)
        frames.append({
            "id": f"frame-{index:02d}",
            "time": frame_time,
            "elapsed": _elapsed(index),
            "elapsed_seconds": index * 60,
            "state_label": _state_label(index, alerts),
            "metrics": {
                "spend": spend,
                "revenue": revenue,
                "profit": revenue - spend,
                "roas": roas,
                "cpa": round(spend / max(1, sold_total), 1) if spend else 0,
                "inventory": inventory,
            },
            "budget_pool": budget_pool,
            "sku_ads": sku_ads,
            "events": events,
            "steps": _steps_for(index, alerts),
            "alerts": alerts,
        })
    return {"enabled": True, "tick_interval_ms": 5000, "frames": frames}


def _build_review(brief: Dict[str, Any], live_demo: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
    final_metrics = live_demo["frames"][-1]["metrics"]
    actual_roas = final_metrics["roas"]
    baseline_roas = round(max(0.1, brief["target_roas"] * 0.82), 1)
    baseline_profit = round(final_metrics["spend"] * baseline_roas - final_metrics["spend"])
    incremental_profit = final_metrics["profit"] - baseline_profit
    return {
        "expected_roas": brief["target_roas"],
        "actual_roas": actual_roas,
        "baseline_roas": baseline_roas,
        "incremental_profit": incremental_profit,
        "benchmarks": [
            {"title": "固定预算基线", "line1": f"ROAS {baseline_roas}", "line2": f"毛利 ${baseline_profit:,.0f}", "line3": "历史参照", "highlight": False},
            {"title": "MaiDeal 托管实际", "line1": f"ROAS {actual_roas}", "line2": f"毛利 ${final_metrics['profit']:,.0f}", "line3": f"${incremental_profit:,.0f} 增量毛利", "highlight": True},
            {"title": "增量贡献", "line1": f"{round((actual_roas / max(baseline_roas, 0.1) - 1) * 100):+d}% ROAS", "line2": "完整快照", "line3": "事件与审批可回放", "highlight": False},
        ],
        "key_actions": [
            {"time": event["time"], "action": event["text"], "result": "已记录", "type": event.get("event_type", "自动")}
            for event in events[-4:]
        ],
        "lead_assets": _lead_assets(brief),
        "strategy_notes": [
            f"{brief['products']} 在 {brief['market']} 的实际 ROAS 为 {actual_roas}。",
            "预算池、SKU 投放和审批动作已写入完整快照，可用于下一场策略。",
            "若出现 ROI 低或预算不足，优先触发审批而不是静默调整。",
        ],
        "api_trace": [
            {"endpoint": "/api/orchestrator/chat", "usage": "收集 brief 并触发 plan 生成。"},
            {"endpoint": "/api/agent-mode/workbench", "usage": "读取项目、SKU、直播帧和复盘。"},
            {"endpoint": "supabase:agent_live_frames", "usage": "持久化完整直播序列。"},
        ],
    }


def _build_live_rooms(brief: Dict[str, Any], plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    labels = ["A · 达人测评", "B · 品牌自播", "C · 尾场承接"]
    budget_parts = [0.34, 0.42, 0.24]
    rooms = []
    for index, label in enumerate(labels):
        room_plan = plans[min(index, len(plans) - 1)]
        rooms.append({
            "id": ["creator", "brand", "clearance"][index],
            "name": f"直播间 {label}",
            "market": " + ".join(brief["channels"]),
            "role": ["前段种草与人群蓄水", "高峰成交主承接", "尾场转化与清库存"][index],
            "budget": round(brief["budget"] * budget_parts[index]),
            "spent": 0,
            "roas": "待启动",
            "channel": room_plan["lines"][0],
            "risk": ["低风险", "推荐均衡", "高波动"][index],
            "status": "待启动",
            "recommended": index == 1,
            "plan_options": plans,
        })
    return rooms


def _build_campaigns(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {"id": index + 1, "name": f"{product['name']}_直播投放", "spend": 0, "roi": 0, "ctr": 0}
        for index, product in enumerate(products[:3])
    ]


def _collect_events(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    events = []
    for frame in frames:
        for event in frame.get("events", []):
            events.append({**event, "frame_index": frames.index(frame), "event_type": event.get("event_type", "signal")})
    return events


def _channel_split(channels: List[str], mode: str, base_weights: Dict[str, int] | None = None) -> Dict[str, int]:
    if not channels:
        return {}
    if base_weights:
        split = {channel: int(base_weights.get(channel, 0)) for channel in channels}
        drift = 100 - sum(split.values())
        split[channels[-1]] += drift
    else:
        base = 100 // len(channels)
        split = {channel: base for channel in channels}
        split[channels[-1]] += 100 - sum(split.values())
    if len(channels) >= 2:
        if mode == "steady":
            shift = min(5, max(0, split[channels[-1]] - 10))
            split[channels[-1]] -= shift
            split[channels[0]] += shift
        elif mode == "aggressive":
            shift = min(5, max(0, split[channels[0]] - 10))
            split[channels[0]] -= shift
            split[channels[-1]] += shift
    return split


def _spend_pools(base_pools: List[Dict[str, Any]], spend: int) -> List[Dict[str, Any]]:
    remaining = spend
    pools = []
    total_budget = sum(pool["total"] for pool in base_pools) or 1
    for index, pool in enumerate(base_pools):
        if index == len(base_pools) - 1:
            pool_spend = min(pool["total"], remaining)
        else:
            pool_spend = min(pool["total"], round(spend * pool["total"] / total_budget))
            remaining -= pool_spend
        next_pool = deepcopy(pool)
        next_pool["spent"] = pool_spend
        next_pool["remaining"] = max(0, pool["total"] - pool_spend)
        pools.append(next_pool)
    return pools


def _spend_curve(total_budget: int, frame_count: int) -> List[int]:
    if frame_count <= 1:
        return [total_budget]
    curve = [
        round(total_budget * ((index / (frame_count - 1)) ** 1.12))
        for index in range(frame_count)
    ]
    curve[0] = 0
    curve[-1] = total_budget
    for index in range(1, frame_count):
        curve[index] = max(curve[index], curve[index - 1])
    return curve


def _sku_frame(products: List[Dict[str, Any]], revenue: int, spend: int, sold_units_by_sku: Dict[str, int], rng: random.Random, index: int) -> List[Dict[str, Any]]:
    weights = [max(0.08, rng.uniform(0.12, 0.35)) for _ in products]
    weights[0] += 0.18
    if index in {2, 4} and len(weights) > 1:
        weights[1] *= 0.45
    weight_total = sum(weights)
    ads = []
    remaining_revenue = revenue
    remaining_spend = spend
    for product_index, product in enumerate(products):
        if product_index == len(products) - 1:
            gmv = remaining_revenue
            sku_spend = remaining_spend
        else:
            gmv = round(revenue * weights[product_index] / weight_total)
            sku_spend = round(spend * weights[product_index] / weight_total)
            remaining_revenue -= gmv
            remaining_spend -= sku_spend
        units = min(product["base_inventory"], round(gmv / max(product["price"], 1)))
        sold_units_by_sku[product["id"]] += units
        ads.append({
            "id": product["id"],
            "sku": product["sku_code"],
            "name": product["name"],
            "spend": sku_spend,
            "gmv": gmv,
            "roi": round(gmv / sku_spend, 1) if sku_spend else 0,
            "units": sold_units_by_sku[product["id"]],
            "status": _sku_status(product_index, index),
        })
    return ads


def _frame_alerts(index: int, roas: float, brief: Dict[str, Any], pools: List[Dict[str, Any]], total_budget: int) -> List[Dict[str, Any]]:
    alerts = []
    if index in {2, 4} and roas and roas < brief["target_roas"]:
        alerts.append({
            "id": f"roi-low-{index}",
            "type": "roi_low",
            "severity": "warning",
            "title": "自动预警：ROI 低于目标",
            "message": f"当前 ROAS {roas}，低于目标 {brief['target_roas']}。",
            "recommendation": "建议降低低效 SKU 预算并转向高转化渠道。",
            "actions": ["批准调整", "继续观察"],
        })
    if index >= 5 and sum(pool["spent"] for pool in pools) > total_budget * 0.78:
        alerts.append({
            "id": f"budget-low-{index}",
            "type": "budget_low",
            "severity": "warning",
            "title": "自动预警：预算接近耗尽",
            "message": "按当前节奏，预算将在尾场前接近耗尽。",
            "recommendation": "建议降低增速或申请追加预算。",
            "actions": ["降低增速", "追加预算审批"],
        })
    return alerts


def _frame_events(index: int, roas: float, alerts: List[Dict[str, Any]], pools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    time_label = _frame_time(index)
    if alerts:
        return [
            {"time": time_label, "agent": "效果分析", "text": alerts[0]["message"], "tone": "amber", "event_type": "alert"},
            {"time": time_label, "agent": "方案规划", "text": alerts[0]["recommendation"], "tone": "violet", "event_type": "strategy"},
        ]
    if index == 0:
        return [{"time": time_label, "agent": "经营信号", "text": "开播预热，等待首批评论、点击和加购信号。", "tone": "cyan", "event_type": "signal"}]
    return [{"time": time_label, "agent": "效果验证", "text": f"当前 ROAS {roas}，预算池累计消耗 ${sum(pool['spent'] for pool in pools):,}。", "tone": "emerald", "event_type": "verification"}]


def _steps_for(index: int, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    names = [("signal", "经营信号"), ("analysis", "效果分析"), ("planning", "方案规划"), ("orchestrator", "调度中心"), ("delivery", "投放执行"), ("verification", "效果验证")]
    active = min(index, len(names) - 1)
    steps = []
    for step_index, (step_id, agent) in enumerate(names):
        if step_index < active:
            status = "done"
        elif step_index == active:
            status = "waiting" if alerts else "pending"
        else:
            status = "idle"
        steps.append({"id": step_id, "agent": agent, "status": status, "summary": _step_summary(agent, alerts)})
    return steps


def _lead_assets(brief: Dict[str, Any]) -> List[Dict[str, Any]]:
    channel = brief["channels"][0] if brief["channels"] else "Live"
    return [
        {"user": "@buyer.live", "channel": channel, "score": 91, "action": f"咨询 {brief['products']} 库存", "status": "待回复"},
        {"user": "@cart_signal", "channel": channel, "score": 84, "action": "加购未付", "status": "跟进中"},
    ]


def _step_summary(agent: str, alerts: List[Dict[str, Any]]) -> str:
    if alerts and agent in {"调度中心", "投放执行"}:
        return "等待人工审批。"
    return {
        "经营信号": "采集评论、点击和加购。",
        "效果分析": "识别变化并归因。",
        "方案规划": "生成预算与人群策略。",
        "调度中心": "校验目标与护栏。",
        "投放执行": "写入预算调整。",
        "效果验证": "验证回写复盘。",
    }[agent]


def _state_label(index: int, alerts: List[Dict[str, Any]]) -> str:
    if alerts:
        return "自动预警"
    return ["开播预热", "冷启动", "策略观察", "调仓验证", "高峰放量", "预算观察", "尾场承接", "复盘写入"][min(index, 7)]


def _sku_status(product_index: int, frame_index: int) -> str:
    if frame_index == 0:
        return "待启动"
    if product_index == 0:
        return "主推"
    if frame_index in {2, 4} and product_index == 1:
        return "降预算"
    return "观察"


def _category_for(product: str) -> str:
    text = product.lower()
    if any(keyword in text for keyword in ["手机", "壳", "case", "配件"]):
        return "accessory"
    if any(keyword in text for keyword in ["杯", "电", "机", "camera"]):
        return "electronics"
    if any(keyword in text for keyword in ["美", "妆", "护肤"]):
        return "beauty"
    if any(keyword in text for keyword in ["衣", "鞋", "包"]):
        return "fashion"
    return "home"


def _seed_for(brief: Dict[str, Any], version_number: int) -> str:
    raw = "|".join([
        str(brief.get("products")),
        str(brief.get("market")),
        str(brief.get("budget")),
        ",".join(brief.get("channels") or []),
        str(brief.get("target_roas")),
        str(version_number),
    ])
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _as_float(value: Any, fallback: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.\-]", "", str(value or ""))
    try:
        return float(cleaned) if cleaned else fallback
    except ValueError:
        return fallback


def _currency_from_market(market: str) -> str:
    if "/" in market:
        return market.split("/")[-1].strip()
    return "USD"


def _channel_id(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _slug(value: str) -> str:
    ascii_part = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return ascii_part or sha256(value.encode("utf-8")).hexdigest()[:8]


def _frame_time(index: int) -> str:
    seconds = index * 60
    minute, second = divmod(seconds, 60)
    return f"20:{minute:02d}:{second:02d}"


def _elapsed(index: int) -> str:
    seconds = index * 60
    minute, second = divmod(seconds, 60)
    return f"00:00:{second:02d}" if minute == 0 else f"00:{minute:02d}:{second:02d}"


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})
