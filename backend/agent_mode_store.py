"""Agent Mode workbench seed store.

This module is the temporary persistence boundary for the /agent-mode page.
Replace the in-memory store with database reads/writes when the schema is ready.
"""

from copy import deepcopy
from typing import Any, Dict


BRIEF_CORE_FIELDS = {"budget", "target_roas", "products", "market", "channels"}
BRIEF_ALL_FIELDS = BRIEF_CORE_FIELDS | {"live_window", "inventory", "margin", "constraints"}

_INITIAL_BRIEF: Dict[str, Any] = {
    "budget": None,
    "target_roas": None,
    "channels": None,
    "products": None,
    "market": None,
    "live_window": None,
    "inventory": None,
    "margin": None,
    "constraints": None,
}

_INITIAL_LIVE_LOOP: Dict[str, Any] = {
    "status": "idle",
    "steps": [],
    "pending_action": None,
    "last_action": None,
    "verification": None,
}

_LIVE_DEMO: Dict[str, Any] = {
    "enabled": True,
    "tick_interval_ms": 5000,
    "frames": [
        {
            "id": "20-00",
            "time": "20:00",
            "elapsed": "00:00:00",
            "state_label": "开播预热",
            "metrics": {"spend": 0, "revenue": 0, "profit": 0, "roas": 0, "cpa": 0, "inventory": 1200},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 0, "total": 2500, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 0, "total": 1700, "tone": "violet"},
                {"id": "reserve", "label": "直播间尾场保留", "spent": 0, "total": 800, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "sku-pro", "sku": "BLD-US-600", "name": "便携榨汁杯 Pro", "spend": 0, "gmv": 0, "roi": 0, "units": 0, "status": "待启动"},
                {"id": "sku-mini", "sku": "BLD-US-MINI", "name": "便携榨汁杯 Mini", "spend": 0, "gmv": 0, "roi": 0, "units": 0, "status": "待启动"},
                {"id": "sku-pack", "sku": "BLD-US-2PK", "name": "双杯家庭装", "spend": 0, "gmv": 0, "roi": 0, "units": 0, "status": "待启动"},
            ],
            "events": [{"time": "20:00", "agent": "经营信号", "text": "开播预热，等待首批评论、点击和加购信号。", "tone": "cyan"}],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "waiting", "summary": "采集开播互动与点击。"},
                {"id": "analysis", "agent": "效果分析", "status": "idle", "summary": "等待首轮数据。"},
                {"id": "planning", "agent": "方案规划", "status": "idle", "summary": "等待策略输入。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "idle", "summary": "等待护栏校验。"},
                {"id": "delivery", "agent": "投放执行", "status": "idle", "summary": "等待执行。"},
                {"id": "verification", "agent": "效果验证", "status": "idle", "summary": "等待验证。"},
            ],
            "alerts": [],
        },
        {
            "id": "20-15",
            "time": "20:15",
            "elapsed": "00:15:00",
            "state_label": "冷启动观察",
            "metrics": {"spend": 620, "revenue": 1890, "profit": 1040, "roas": 3.0, "cpa": 9.8, "inventory": 1170},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 420, "total": 2500, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 200, "total": 1700, "tone": "violet"},
                {"id": "reserve", "label": "直播间尾场保留", "spent": 0, "total": 800, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "sku-pro", "sku": "BLD-US-600", "name": "便携榨汁杯 Pro", "spend": 310, "gmv": 1120, "roi": 3.6, "units": 28, "status": "放量"},
                {"id": "sku-mini", "sku": "BLD-US-MINI", "name": "便携榨汁杯 Mini", "spend": 190, "gmv": 510, "roi": 2.7, "units": 18, "status": "观察"},
                {"id": "sku-pack", "sku": "BLD-US-2PK", "name": "双杯家庭装", "spend": 120, "gmv": 260, "roi": 2.2, "units": 4, "status": "低速"},
            ],
            "events": [
                {"time": "20:15", "agent": "经营信号", "text": "达人间点击率 2.6%，品牌自播间加购开始抬升。", "tone": "cyan"},
                {"time": "20:15", "agent": "效果分析", "text": "冷启动 ROAS 3.0，暂不触发预算调整。", "tone": "emerald"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "完成首轮评论/点击/加购采集。"},
                {"id": "analysis", "agent": "效果分析", "status": "waiting", "summary": "归因冷启动效率。"},
                {"id": "planning", "agent": "方案规划", "status": "idle", "summary": "等待策略输入。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "idle", "summary": "等待护栏校验。"},
                {"id": "delivery", "agent": "投放执行", "status": "idle", "summary": "等待执行。"},
                {"id": "verification", "agent": "效果验证", "status": "idle", "summary": "等待验证。"},
            ],
            "alerts": [],
        },
        {
            "id": "20-45",
            "time": "20:45",
            "elapsed": "00:45:00",
            "state_label": "低效预警",
            "metrics": {"spend": 1380, "revenue": 3650, "profit": 2008, "roas": 2.6, "cpa": 12.4, "inventory": 1135},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 980, "total": 2500, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 400, "total": 1700, "tone": "violet"},
                {"id": "reserve", "label": "直播间尾场保留", "spent": 0, "total": 800, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "sku-pro", "sku": "BLD-US-600", "name": "便携榨汁杯 Pro", "spend": 650, "gmv": 2100, "roi": 3.2, "units": 54, "status": "稳定"},
                {"id": "sku-mini", "sku": "BLD-US-MINI", "name": "便携榨汁杯 Mini", "spend": 510, "gmv": 920, "roi": 1.8, "units": 32, "status": "降预算"},
                {"id": "sku-pack", "sku": "BLD-US-2PK", "name": "双杯家庭装", "spend": 220, "gmv": 630, "roi": 2.9, "units": 8, "status": "观察"},
            ],
            "events": [
                {"time": "20:45", "agent": "效果分析", "text": "TikTok 边际 ROAS 跌破 2.4，Mini SKU 拖低整体效率。", "tone": "amber"},
                {"time": "20:45", "agent": "方案规划", "text": "建议下调 Mini SKU 预算 25%，把曝光转向 Pro SKU 与品牌自播间。", "tone": "violet"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "识别 SKU 点击与加购差异。"},
                {"id": "analysis", "agent": "效果分析", "status": "done", "summary": "归因 Mini SKU 转化偏低。"},
                {"id": "planning", "agent": "方案规划", "status": "waiting", "summary": "生成降预算与转向策略。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "idle", "summary": "等待护栏校验。"},
                {"id": "delivery", "agent": "投放执行", "status": "idle", "summary": "等待执行。"},
                {"id": "verification", "agent": "效果验证", "status": "idle", "summary": "等待验证。"},
            ],
            "alerts": [{
                "id": "roi-low-20-45",
                "type": "roi_low",
                "severity": "warning",
                "title": "自动预警：Mini SKU ROI 偏低",
                "message": "BLD-US-MINI 近 15 分钟 ROI 仅 1.8，低于目标 ROAS 3.0。",
                "recommendation": "建议降低 Mini SKU 预算 25%，转给 Pro SKU 和品牌自播间。",
                "actions": ["同意降预算", "继续观察"],
            }],
        },
        {
            "id": "21-05",
            "time": "21:05",
            "elapsed": "01:05:00",
            "state_label": "调仓生效",
            "metrics": {"spend": 2100, "revenue": 7250, "profit": 3988, "roas": 3.5, "cpa": 8.8, "inventory": 1075},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 1200, "total": 2300, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 900, "total": 1900, "tone": "violet"},
                {"id": "reserve", "label": "直播间尾场保留", "spent": 0, "total": 800, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "sku-pro", "sku": "BLD-US-600", "name": "便携榨汁杯 Pro", "spend": 1020, "gmv": 4300, "roi": 4.2, "units": 116, "status": "主推"},
                {"id": "sku-mini", "sku": "BLD-US-MINI", "name": "便携榨汁杯 Mini", "spend": 590, "gmv": 1180, "roi": 2.0, "units": 42, "status": "限速"},
                {"id": "sku-pack", "sku": "BLD-US-2PK", "name": "双杯家庭装", "spend": 490, "gmv": 1770, "roi": 3.6, "units": 20, "status": "加码"},
            ],
            "events": [
                {"time": "21:05", "agent": "调度中心", "text": "策略未超过护栏，授权自动执行预算转移。", "tone": "violet"},
                {"time": "21:05", "agent": "投放执行", "text": "Mini SKU 预算下调，Meta 品牌自播预算上调。", "tone": "cyan"},
                {"time": "21:05", "agent": "效果验证", "text": "观察窗口内 ROAS 回升至 3.5。", "tone": "emerald"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "完成低效 SKU 信号采集。"},
                {"id": "analysis", "agent": "效果分析", "status": "done", "summary": "确认低效来自 Mini SKU 与达人间。"},
                {"id": "planning", "agent": "方案规划", "status": "done", "summary": "生成预算转向策略。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "done", "summary": "护栏内动作自动授权。"},
                {"id": "delivery", "agent": "投放执行", "status": "done", "summary": "完成预算调整。"},
                {"id": "verification", "agent": "效果验证", "status": "waiting", "summary": "验证调仓效果。"},
            ],
            "alerts": [],
        },
        {
            "id": "21-35",
            "time": "21:35",
            "elapsed": "01:35:00",
            "state_label": "预算压力",
            "metrics": {"spend": 3320, "revenue": 11680, "profit": 6424, "roas": 3.5, "cpa": 7.6, "inventory": 990},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 1350, "total": 2100, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 1970, "total": 2100, "tone": "violet"},
                {"id": "reserve", "label": "直播间尾场保留", "spent": 0, "total": 800, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "sku-pro", "sku": "BLD-US-600", "name": "便携榨汁杯 Pro", "spend": 1680, "gmv": 7200, "roi": 4.3, "units": 192, "status": "主推"},
                {"id": "sku-mini", "sku": "BLD-US-MINI", "name": "便携榨汁杯 Mini", "spend": 650, "gmv": 1410, "roi": 2.2, "units": 52, "status": "限速"},
                {"id": "sku-pack", "sku": "BLD-US-2PK", "name": "双杯家庭装", "spend": 990, "gmv": 3070, "roi": 3.1, "units": 36, "status": "加码"},
            ],
            "events": [
                {"time": "21:35", "agent": "经营信号", "text": "品牌自播间高意向评论占比升至 41%。", "tone": "cyan"},
                {"time": "21:35", "agent": "效果分析", "text": "Meta 转化窗口缩短，预算消耗速度高于计划。", "tone": "amber"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "发现高意向评论集中在品牌自播间。"},
                {"id": "analysis", "agent": "效果分析", "status": "done", "summary": "判断预算消耗速度偏快。"},
                {"id": "planning", "agent": "方案规划", "status": "waiting", "summary": "生成追加预算或降速备选策略。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "idle", "summary": "等待经营目标校验。"},
                {"id": "delivery", "agent": "投放执行", "status": "idle", "summary": "等待审批。"},
                {"id": "verification", "agent": "效果验证", "status": "idle", "summary": "等待验证。"},
            ],
            "alerts": [{
                "id": "budget-watch-21-35",
                "type": "budget_low",
                "severity": "warning",
                "title": "自动预警：预算消耗速度偏快",
                "message": "按当前节奏，预算将在 22:10 前进入尾场保留。",
                "recommendation": "建议二选一：追加 $1,200 保持高峰抢量，或降低 Meta 增速 18%。",
                "actions": ["追加预算审批", "降低增速"],
            }],
        },
        {
            "id": "22-05",
            "time": "22:05",
            "elapsed": "02:05:00",
            "state_label": "高峰审批",
            "metrics": {"spend": 4480, "revenue": 13920, "profit": 7656, "roas": 3.1, "cpa": 8.4, "inventory": 900},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 1600, "total": 1900, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 2480, "total": 2500, "tone": "violet"},
                {"id": "reserve", "label": "直播间尾场保留", "spent": 400, "total": 600, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "sku-pro", "sku": "BLD-US-600", "name": "便携榨汁杯 Pro", "spend": 2380, "gmv": 9600, "roi": 4.0, "units": 258, "status": "高峰"},
                {"id": "sku-mini", "sku": "BLD-US-MINI", "name": "便携榨汁杯 Mini", "spend": 760, "gmv": 1590, "roi": 2.1, "units": 60, "status": "限速"},
                {"id": "sku-pack", "sku": "BLD-US-2PK", "name": "双杯家庭装", "spend": 1340, "gmv": 2730, "roi": 2.0, "units": 34, "status": "需复查"},
            ],
            "events": [
                {"time": "22:05", "agent": "方案规划", "text": "生成追加预算 $1,200 与降速 18% 两个方案。", "tone": "violet"},
                {"time": "22:05", "agent": "调度中心", "text": "追加预算超过护栏，等待广告主确认。", "tone": "amber"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "高峰流量仍集中在品牌自播间。"},
                {"id": "analysis", "agent": "效果分析", "status": "done", "summary": "ROI 达标但余额不足。"},
                {"id": "planning", "agent": "方案规划", "status": "done", "summary": "输出追加预算与降速备选。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "waiting", "summary": "金额超过审批阈值，等待人工选择。"},
                {"id": "delivery", "agent": "投放执行", "status": "pending", "summary": "待审批后执行。"},
                {"id": "verification", "agent": "效果验证", "status": "idle", "summary": "等待验证。"},
            ],
            "alerts": [{
                "id": "budget-low-22-05",
                "type": "budget_low",
                "severity": "critical",
                "title": "自动预警：尾场预算不足",
                "message": "剩余预算约 $520，预计 12 分钟内耗尽，可能错过高峰尾段。",
                "recommendation": "建议人工审批追加 $1,200；若不追加，则降低 Meta 与双杯家庭装预算。",
                "actions": ["批准追加 $1,200", "降低预算"],
            }],
        },
        {
            "id": "22-30",
            "time": "22:30",
            "elapsed": "02:30:00",
            "state_label": "尾场控制",
            "metrics": {"spend": 5000, "revenue": 16000, "profit": 8800, "roas": 3.2, "cpa": 7.9, "inventory": 820},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 1700, "total": 1700, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 2700, "total": 2700, "tone": "violet"},
                {"id": "reserve", "label": "直播间尾场保留", "spent": 600, "total": 600, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "sku-pro", "sku": "BLD-US-600", "name": "便携榨汁杯 Pro", "spend": 2700, "gmv": 11200, "roi": 4.1, "units": 304, "status": "保留"},
                {"id": "sku-mini", "sku": "BLD-US-MINI", "name": "便携榨汁杯 Mini", "spend": 790, "gmv": 1670, "roi": 2.1, "units": 64, "status": "暂停"},
                {"id": "sku-pack", "sku": "BLD-US-2PK", "name": "双杯家庭装", "spend": 1510, "gmv": 3130, "roi": 2.1, "units": 42, "status": "降速"},
            ],
            "events": [
                {"time": "22:30", "agent": "投放执行", "text": "未追加预算，系统降速 Meta 尾场并暂停 Mini SKU。", "tone": "cyan"},
                {"time": "22:30", "agent": "效果验证", "text": "总 ROAS 维持 3.2，预算不再扩张。", "tone": "emerald"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "完成尾场信号采集。"},
                {"id": "analysis", "agent": "效果分析", "status": "done", "summary": "确认预算耗尽风险。"},
                {"id": "planning", "agent": "方案规划", "status": "done", "summary": "采用保守降速策略。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "done", "summary": "护栏校验通过，不增加总预算。"},
                {"id": "delivery", "agent": "投放执行", "status": "done", "summary": "暂停低效 SKU 并限速尾场。"},
                {"id": "verification", "agent": "效果验证", "status": "done", "summary": "ROAS 稳定在目标上方。"},
            ],
            "alerts": [],
        },
    ],
}


_PHONE_CASE_LIVE_DEMO: Dict[str, Any] = {
    "enabled": True,
    "tick_interval_ms": 5000,
    "frames": [
        {
            "id": "sg-20-00",
            "time": "20:00",
            "elapsed": "00:00:00",
            "state_label": "开播预热",
            "metrics": {"spend": 0, "revenue": 0, "profit": 0, "roas": 0, "cpa": 0, "inventory": 2600},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 0, "total": 1700, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 0, "total": 900, "tone": "violet"},
                {"id": "reserve", "label": "Shopee 尾场保留", "spent": 0, "total": 600, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "case-pro", "sku": "CASE-SEA-MAG", "name": "磁吸手机壳 Pro", "spend": 0, "gmv": 0, "roi": 0, "units": 0, "status": "待启动"},
                {"id": "case-clear", "sku": "CASE-SEA-CLEAR", "name": "透明防摔手机壳", "spend": 0, "gmv": 0, "roi": 0, "units": 0, "status": "待启动"},
                {"id": "case-pack", "sku": "CASE-SEA-3PK", "name": "三件套换新装", "spend": 0, "gmv": 0, "roi": 0, "units": 0, "status": "待启动"},
            ],
            "events": [{"time": "20:00", "agent": "经营信号", "text": "东南亚晚高峰开播，等待 TikTok 评论和 Shopee 加购信号。", "tone": "cyan"}],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "waiting", "summary": "采集评论、点击和加购。"},
                {"id": "analysis", "agent": "效果分析", "status": "idle", "summary": "等待首轮转化。"},
                {"id": "planning", "agent": "方案规划", "status": "idle", "summary": "等待策略输入。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "idle", "summary": "等待护栏校验。"},
                {"id": "delivery", "agent": "投放执行", "status": "idle", "summary": "等待执行。"},
                {"id": "verification", "agent": "效果验证", "status": "idle", "summary": "等待验证。"},
            ],
            "alerts": [],
        },
        {
            "id": "sg-20-30",
            "time": "20:30",
            "elapsed": "00:30:00",
            "state_label": "冷启动放量",
            "metrics": {"spend": 520, "revenue": 1690, "profit": 760, "roas": 3.3, "cpa": 4.2, "inventory": 2508},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 380, "total": 1700, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 140, "total": 900, "tone": "violet"},
                {"id": "reserve", "label": "Shopee 尾场保留", "spent": 0, "total": 600, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "case-pro", "sku": "CASE-SEA-MAG", "name": "磁吸手机壳 Pro", "spend": 260, "gmv": 1040, "roi": 4.0, "units": 48, "status": "放量"},
                {"id": "case-clear", "sku": "CASE-SEA-CLEAR", "name": "透明防摔手机壳", "spend": 180, "gmv": 480, "roi": 2.7, "units": 36, "status": "观察"},
                {"id": "case-pack", "sku": "CASE-SEA-3PK", "name": "三件套换新装", "spend": 80, "gmv": 170, "roi": 2.1, "units": 8, "status": "低速"},
            ],
            "events": [
                {"time": "20:30", "agent": "经营信号", "text": "磁吸款评论询价集中，越南和菲律宾流量点击率更高。", "tone": "cyan"},
                {"time": "20:30", "agent": "效果分析", "text": "冷启动 ROAS 3.3，TikTok 可继续试探放量。", "tone": "emerald"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "识别磁吸款询价增长。"},
                {"id": "analysis", "agent": "效果分析", "status": "waiting", "summary": "归因冷启动效率。"},
                {"id": "planning", "agent": "方案规划", "status": "idle", "summary": "等待策略输入。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "idle", "summary": "等待护栏校验。"},
                {"id": "delivery", "agent": "投放执行", "status": "idle", "summary": "等待执行。"},
                {"id": "verification", "agent": "效果验证", "status": "idle", "summary": "等待验证。"},
            ],
            "alerts": [],
        },
        {
            "id": "sg-21-00",
            "time": "21:00",
            "elapsed": "01:00:00",
            "state_label": "低效预警",
            "metrics": {"spend": 1280, "revenue": 3320, "profit": 1494, "roas": 2.6, "cpa": 5.8, "inventory": 2390},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 920, "total": 1700, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 360, "total": 900, "tone": "violet"},
                {"id": "reserve", "label": "Shopee 尾场保留", "spent": 0, "total": 600, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "case-pro", "sku": "CASE-SEA-MAG", "name": "磁吸手机壳 Pro", "spend": 620, "gmv": 2440, "roi": 3.9, "units": 116, "status": "主推"},
                {"id": "case-clear", "sku": "CASE-SEA-CLEAR", "name": "透明防摔手机壳", "spend": 490, "gmv": 650, "roi": 1.3, "units": 54, "status": "降预算"},
                {"id": "case-pack", "sku": "CASE-SEA-3PK", "name": "三件套换新装", "spend": 170, "gmv": 230, "roi": 1.4, "units": 12, "status": "暂停候选"},
            ],
            "events": [
                {"time": "21:00", "agent": "效果分析", "text": "透明款点击高但加购低，拖累整体 ROAS 至 2.6。", "tone": "amber"},
                {"time": "21:00", "agent": "方案规划", "text": "建议透明款降预算 30%，转向磁吸款和 Shopee 尾场券。", "tone": "violet"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "发现透明款点击与加购脱节。"},
                {"id": "analysis", "agent": "效果分析", "status": "done", "summary": "归因透明款转化偏低。"},
                {"id": "planning", "agent": "方案规划", "status": "waiting", "summary": "生成 SKU 降预算策略。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "idle", "summary": "等待护栏校验。"},
                {"id": "delivery", "agent": "投放执行", "status": "idle", "summary": "等待执行。"},
                {"id": "verification", "agent": "效果验证", "status": "idle", "summary": "等待验证。"},
            ],
            "alerts": [{
                "id": "case-roi-low-21-00",
                "type": "roi_low",
                "severity": "warning",
                "title": "自动预警：透明款 ROI 偏低",
                "message": "CASE-SEA-CLEAR 近 30 分钟 ROI 仅 1.3，低于目标 ROAS 2.8。",
                "recommendation": "建议降低透明款预算 30%，转给磁吸款 Pro 和 Shopee 尾场保留。",
                "actions": ["同意降预算", "继续观察"],
            }],
        },
        {
            "id": "sg-21-30",
            "time": "21:30",
            "elapsed": "01:30:00",
            "state_label": "调仓生效",
            "metrics": {"spend": 2140, "revenue": 7420, "profit": 3339, "roas": 3.5, "cpa": 4.1, "inventory": 2210},
            "budget_pool": [
                {"id": "tiktok", "label": "TikTok Ads", "spent": 1240, "total": 1500, "tone": "cyan"},
                {"id": "meta", "label": "Meta Ads", "spent": 540, "total": 900, "tone": "violet"},
                {"id": "reserve", "label": "Shopee 尾场保留", "spent": 360, "total": 800, "tone": "amber"},
            ],
            "sku_ads": [
                {"id": "case-pro", "sku": "CASE-SEA-MAG", "name": "磁吸手机壳 Pro", "spend": 1220, "gmv": 5360, "roi": 4.4, "units": 256, "status": "主推"},
                {"id": "case-clear", "sku": "CASE-SEA-CLEAR", "name": "透明防摔手机壳", "spend": 560, "gmv": 860, "roi": 1.5, "units": 70, "status": "限速"},
                {"id": "case-pack", "sku": "CASE-SEA-3PK", "name": "三件套换新装", "spend": 360, "gmv": 1200, "roi": 3.3, "units": 40, "status": "加码"},
            ],
            "events": [
                {"time": "21:30", "agent": "调度中心", "text": "策略在护栏内，自动转移透明款预算到磁吸款与尾场券。", "tone": "violet"},
                {"time": "21:30", "agent": "效果验证", "text": "调仓后 ROAS 回升至 3.5，继续观察尾场库存。", "tone": "emerald"},
            ],
            "steps": [
                {"id": "signal", "agent": "经营信号", "status": "done", "summary": "完成 SKU 信号采集。"},
                {"id": "analysis", "agent": "效果分析", "status": "done", "summary": "确认透明款低效。"},
                {"id": "planning", "agent": "方案规划", "status": "done", "summary": "生成预算转向策略。"},
                {"id": "orchestrator", "agent": "调度中心", "status": "done", "summary": "护栏内动作自动授权。"},
                {"id": "delivery", "agent": "投放执行", "status": "done", "summary": "完成预算调整。"},
                {"id": "verification", "agent": "效果验证", "status": "done", "summary": "ROAS 已回升。"},
            ],
            "alerts": [],
        },
    ],
}


def _build_budget_projects() -> list:
    return [
        {
            "id": "blender-us-live",
            "name": "便携榨汁杯 · 美国直播",
            "market": "美国 / USD",
            "status": "已复盘",
            "budget": "$5,000",
            "spent": "$5,000",
            "roas": "3.1",
            "updated_at": "22:30",
            "workbench": {
                "phase": "review",
                "brief_complete": True,
                "brief_fields": {
                    "budget": "$5,000",
                    "target_roas": "3.0",
                    "channels": "Meta + TikTok（各 50%）",
                    "products": "便携榨汁杯",
                    "market": "美国 / USD",
                    "live_window": "20:00-23:00",
                    "inventory": "1,200 件",
                    "margin": "55%",
                    "constraints": "Meta 最多占 45%",
                },
                "project": {
                    "name": "便携榨汁杯 · 美国直播",
                    "product": "便携榨汁杯",
                    "market": "美国 / USD",
                    "totalBudget": "$5,000",
                    "totalBudgetValue": 5000,
                    "liveWindow": "20:00-23:00",
                    "inventory": "1,200 件",
                    "margin": "55%",
                    "targetRoas": "3.0",
                    "channels": "Meta + TikTok（各 50%）",
                },
                "selected_room_id": "brand",
                "selected_plan": "balanced",
                "plan_versions": [
                    {
                        "id": "plan-v1-blender",
                        "label": "Plan v1",
                        "created_at": "22:30",
                        "summary": "美国直播固定预算复盘版本，均衡方案完成托管。",
                        "plan_ids": ["steady", "balanced", "aggressive"],
                        "active": True,
                    },
                ],
                "live_demo": deepcopy(_LIVE_DEMO),
            },
        },
        {
            "id": "phonecase-sea-live",
            "name": "东南亚手机壳直播",
            "market": "东南亚 / SGD",
            "status": "待托管",
            "budget": "$3,200",
            "spent": "$0",
            "roas": "2.8",
            "updated_at": "新预算",
            "workbench": {
                "phase": "plan",
                "brief_complete": True,
                "brief_fields": {
                    "budget": "$3,200",
                    "target_roas": "2.8",
                    "channels": "TikTok + Shopee",
                    "products": "磁吸手机壳",
                    "market": "东南亚 / SGD",
                    "live_window": "20:00-22:30",
                    "inventory": "2,600 件",
                    "margin": "45%",
                    "constraints": "Shopee 尾场保留不少于 $600",
                },
                "project": {
                    "name": "东南亚手机壳直播",
                    "product": "磁吸手机壳",
                    "market": "东南亚 / SGD",
                    "totalBudget": "$3,200",
                    "totalBudgetValue": 3200,
                    "liveWindow": "20:00-22:30",
                    "inventory": "2,600 件",
                    "margin": "45%",
                    "targetRoas": "2.8",
                    "channels": "TikTok + Shopee",
                },
                "selected_room_id": "sea-brand",
                "selected_plan": "balanced",
                "guard_limit": "12",
                "approval_threshold": "600",
                "left_timeline": [
                    {"role": "广告主", "content": "新增预算：东南亚手机壳直播，预算 $3,200，目标 ROAS 2.8。"},
                    {"role": "调度中心", "content": "已建立新预算项目，建议 TikTok 负责种草，Shopee 承接尾场转化。", "agent": True},
                ],
                "live_rooms": [
                    {"id": "sea-creator", "name": "手机壳直播间 A · 达人测评", "market": "TikTok Shop SEA", "role": "前段种草与评论蓄水", "budget": 1100, "spent": 0, "roas": "2.5-2.9", "channel": "TikTok 75% / Shopee 25%", "risk": "低风险", "status": "待启动"},
                    {"id": "sea-brand", "name": "手机壳直播间 B · 品牌自播", "market": "TikTok + Shopee", "role": "主承接与套装成交", "budget": 1400, "spent": 0, "roas": "2.8-3.4", "channel": "TikTok 55% / Shopee 45%", "risk": "推荐均衡", "status": "待启动", "recommended": True},
                    {"id": "sea-clearance", "name": "手机壳直播间 C · 尾场清单", "market": "Shopee Live", "role": "优惠券尾场冲量", "budget": 700, "spent": 0, "roas": "3.0-3.6", "channel": "TikTok 35% / Shopee 65%", "risk": "高波动", "status": "待启动"},
                ],
                "plan_options": [
                    {"id": "steady", "title": "保守", "lines": ["TikTok 65% / Shopee 35%", "先测磁吸款，透明款限速", "预期 ROAS 2.5-2.9", "优先保护预算"]},
                    {"id": "balanced", "title": "均衡", "recommended": True, "lines": ["TikTok 55% / Shopee 45%", "前段种草，尾场券承接", "预期 ROAS 2.8-3.4", "风险中等，推荐"]},
                    {"id": "aggressive", "title": "进取", "lines": ["TikTok 45% / Shopee 55%", "尾场集中放券冲量", "预期 ROAS 3.0-3.6", "库存和券预算波动更高"]},
                ],
                "plan_versions": [
                    {
                        "id": "plan-v1-phonecase",
                        "label": "Plan v1",
                        "created_at": "新预算",
                        "summary": "东南亚手机壳直播首版方案，TikTok 种草，Shopee 尾场承接。",
                        "plan_ids": ["steady", "balanced", "aggressive"],
                        "active": True,
                    },
                ],
                "live_demo": deepcopy(_PHONE_CASE_LIVE_DEMO),
                "lead_rows": [
                    {"user": "@minh.case", "channel": "TikTok", "score": 91, "action": "询问 iPhone 15 款式", "status": "待回复"},
                    {"user": "@sg_mall", "channel": "Shopee", "score": 86, "action": "领取尾场券", "status": "跟进中"},
                    {"user": "@nina.my", "channel": "TikTok", "score": 69, "action": "咨询透明款防摔", "status": "已回复"},
                    {"user": "@casehub.ph", "channel": "Shopee", "score": 58, "action": "加购三件套", "status": "观察"},
                ],
                "review_benchmarks": [
                    {"title": "固定预算基线", "line1": "ROAS 2.4", "line2": "毛利 $1,180", "line3": "历史参照", "highlight": False},
                    {"title": "MaiDeal 托管预估", "line1": "ROAS 3.0", "line2": "毛利 $1,520", "line3": "+$340 预估增量毛利", "highlight": True},
                    {"title": "增量贡献", "line1": "+25% ROAS", "line2": "+28.8% 毛利", "line3": "2 次 SKU 调仓", "highlight": False},
                ],
                "review_actions": [
                    {"time": "21:00", "action": "透明款预算 -30%", "result": "+$96", "type": "自动"},
                    {"time": "21:30", "action": "磁吸款加码 $320", "result": "+$140", "type": "自动"},
                    {"time": "21:45", "action": "Shopee 尾场券加码", "result": "待审批", "type": "审批"},
                ],
                "strategy_notes": [
                    "磁吸款评论询价强，建议作为主 SKU 承接直播间流量。",
                    "透明款点击高但加购弱，适合保留低预算做补充曝光。",
                    "Shopee 尾场券对套装转化更明显，需预留不少于 $600。",
                ],
                "fallback_campaigns": [
                    {"id": 201, "name": "SEA_磁吸手机壳_品牌自播", "spend": 0, "roi": 0, "ctr": 0},
                    {"id": 202, "name": "SEA_透明防摔款_达人测评", "spend": 0, "roi": 0, "ctr": 0},
                    {"id": 203, "name": "SEA_三件套_尾场券承接", "spend": 0, "roi": 0, "ctr": 0},
                ],
            },
        },
    ]

AGENT_MODE_WORKBENCH: Dict[str, Any] = {
    "phase": "briefing",
    "brief_fields": deepcopy(_INITIAL_BRIEF),
    "brief_complete": False,
    "project": {
        "name": "",
        "product": "",
        "market": "",
        "totalBudget": "",
        "totalBudgetValue": 0,
        "liveWindow": "",
        "inventory": "",
        "margin": "",
        "targetRoas": "",
        "channels": "",
    },
    "layout": {
        "left_panel_width": 300,
        "right_panel_width": 390,
        "brief_collapsed": False,
    },
    "active_project_id": None,
    "budget_projects": _build_budget_projects(),
    "selected_room_id": "brand",
    "selected_plan": "balanced",
    "guard_limit": "15",
    "approval_threshold": "800",
    "chat_welcome": "你好！我是 MaiDeal 投放调度中心。请描述你的经营目标，例如：「我要给便携榨汁杯做一场美国市场直播，预算 $5,000」。我会帮你逐步梳理投放方案。",
    "left_timeline": [],
    "agent_roster": [
        {"id": "orchestrator", "name": "调度中心", "label": "编排", "tone": "violet", "status": "待命"},
        {"id": "planning", "name": "方案规划", "label": "规划", "tone": "indigo", "status": "待命"},
        {"id": "delivery", "name": "投放执行", "label": "执行", "tone": "cyan", "status": "待命"},
        {"id": "analysis", "name": "效果分析", "label": "分析", "tone": "amber", "status": "待命"},
        {"id": "signal", "name": "经营信号", "label": "信号", "tone": "emerald", "status": "待命"},
    ],
    "default_trend": [
        {"time": "20:00", "spend": 120, "gmv": 380},
        {"time": "20:30", "spend": 310, "gmv": 920},
        {"time": "21:00", "spend": 650, "gmv": 2140},
        {"time": "21:30", "spend": 980, "gmv": 3280},
        {"time": "22:00", "spend": 1420, "gmv": 4620},
        {"time": "22:30", "spend": 1810, "gmv": 5700},
        {"time": "23:00", "spend": 2180, "gmv": 6540},
    ],
    "live_rooms": [],
    "plan_options": [],
    "plan_versions": [],
    "live_loop": deepcopy(_INITIAL_LIVE_LOOP),
    "live_demo": deepcopy(_LIVE_DEMO),
    "process_steps": [
        "生成预算拆分、直播间选择和投放目标。",
        "按护栏自动调仓，超阈值请求人工审批。",
        "沉淀高意向评论、私信、加购和达人线索。",
        "复盘动作证据，生成下一场托管记忆。",
    ],
    "lead_rows": [
        {"user": "@jenny_w", "channel": "Meta", "score": 92, "action": "评论：哪里买？", "status": "待回复"},
        {"user": "@mike2024", "channel": "Meta", "score": 88, "action": "加购未付", "status": "跟进中"},
        {"user": "@sara.lee", "channel": "TikTok", "score": 64, "action": "咨询容量", "status": "已回复"},
        {"user": "@tomh", "channel": "TikTok", "score": 41, "action": "点赞停留 18 秒", "status": "观察"},
    ],
    "fallback_campaigns": [
        {"id": 101, "name": "新品推广_便携榨汁杯_USA_V1", "spend": 980, "roi": 3.4, "ctr": 2.8},
        {"id": 102, "name": "达人直播间_前段蓄水_自动出价", "spend": 620, "roi": 2.9, "ctr": 3.1},
        {"id": 103, "name": "清仓冲量_高峰窗口_003", "spend": 580, "roi": 3.8, "ctr": 2.4},
    ],
    "managed_events": [
        {"time": "21:42", "agent": "经营信号", "text": "Meta 高意向评论占比升至 38%", "tone": "cyan"},
        {"time": "21:43", "agent": "效果分析", "text": "TikTok 边际 ROAS 跌破 2.4，Meta 维持 3.5", "tone": "amber"},
        {"time": "21:44", "agent": "投放执行", "text": "提议：$600 TikTok → Meta，低于调仓上限", "tone": "violet"},
        {"time": "21:54", "agent": "效果分析", "text": "观察窗口结束：增量毛利 +$210，保留动作", "tone": "emerald"},
    ],
    "review_benchmarks": [
        {"title": "固定预算基线", "line1": "ROAS 2.6", "line2": "毛利 $2,980", "line3": "灰度参照", "highlight": False},
        {"title": "MaiDeal 托管实际", "line1": "ROAS 3.1", "line2": "毛利 $3,597", "line3": "+$617 增量毛利", "highlight": True},
        {"title": "增量贡献", "line1": "+19% ROAS", "line2": "+20.7% 毛利", "line3": "3 次自主调仓", "highlight": False},
    ],
    "review_actions": [
        {"time": "21:44", "action": "$600 TikTok → Meta", "result": "+$210", "type": "自动"},
        {"time": "22:10", "action": "Meta 加码 $400", "result": "+$180", "type": "自动"},
        {"time": "22:35", "action": "暂停低效素材", "result": "+$95", "type": "自动"},
        {"time": "22:50", "action": "追加预算 $900", "result": "人工批准", "type": "审批"},
    ],
    "strategy_notes": [
        "该品类高峰期 Meta 高意向率显著优于 TikTok，建议默认 Meta 偏配。",
        "TikTok 适合前段拉量蓄水，后段及时止损。",
        "10 分钟观察窗对本场调仓验证有效，可沿用。",
    ],
    "disabled_actions": ["价格承诺", "退款处理", "新开渠道"],
}


def _deep_merge(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in patch.items():
        bv = base.get(key)
        if isinstance(bv, list) and isinstance(value, dict):
            for item in bv:
                item_id = item.get("id") if isinstance(item, dict) else None
                if item_id and item_id in value:
                    item.update(deepcopy(value[item_id]))
        elif isinstance(value, dict) and isinstance(bv, dict):
            _deep_merge(bv, value)
        else:
            base[key] = deepcopy(value)
    return base


def read_workbench() -> Dict[str, Any]:
    return deepcopy(AGENT_MODE_WORKBENCH)


def write_workbench(payload: Dict[str, Any]) -> Dict[str, Any]:
    _deep_merge(AGENT_MODE_WORKBENCH, payload or {})
    return read_workbench()


def patch_workbench(patch: Dict[str, Any]) -> None:
    """Apply a partial patch without returning a full copy."""
    _deep_merge(AGENT_MODE_WORKBENCH, patch or {})


def reset_workbench() -> Dict[str, Any]:
    """Reset to the initial briefing state."""
    global AGENT_MODE_WORKBENCH
    AGENT_MODE_WORKBENCH["phase"] = "briefing"
    AGENT_MODE_WORKBENCH["brief_fields"] = deepcopy(_INITIAL_BRIEF)
    AGENT_MODE_WORKBENCH["brief_complete"] = False
    AGENT_MODE_WORKBENCH["project"] = {
        "name": "", "product": "", "market": "",
        "totalBudget": "", "totalBudgetValue": 0,
        "liveWindow": "", "inventory": "", "margin": "",
        "targetRoas": "", "channels": "",
    }
    AGENT_MODE_WORKBENCH["active_project_id"] = None
    AGENT_MODE_WORKBENCH["budget_projects"] = _build_budget_projects()
    AGENT_MODE_WORKBENCH["left_timeline"] = []
    AGENT_MODE_WORKBENCH["live_rooms"] = []
    AGENT_MODE_WORKBENCH["plan_options"] = []
    AGENT_MODE_WORKBENCH["plan_versions"] = []
    AGENT_MODE_WORKBENCH["live_loop"] = deepcopy(_INITIAL_LIVE_LOOP)
    AGENT_MODE_WORKBENCH["live_demo"] = deepcopy(_LIVE_DEMO)
    AGENT_MODE_WORKBENCH["selected_plan"] = "balanced"
    AGENT_MODE_WORKBENCH["guard_limit"] = "15"
    AGENT_MODE_WORKBENCH["approval_threshold"] = "800"
    AGENT_MODE_WORKBENCH["chat_welcome"] = "你好！我是 MaiDeal 投放调度中心。请描述你的经营目标，例如：「我要给便携榨汁杯做一场美国市场直播，预算 $5,000」。我会帮你逐步梳理投放方案。"
    for agent in AGENT_MODE_WORKBENCH.get("agent_roster", []):
        agent["status"] = "待命"
    return read_workbench()


def get_brief_completion() -> Dict[str, Any]:
    """Return brief collection status."""
    brief = AGENT_MODE_WORKBENCH.get("brief_fields", {})
    filled = [k for k in BRIEF_ALL_FIELDS if brief.get(k) is not None]
    missing = [k for k in BRIEF_ALL_FIELDS if brief.get(k) is None]
    core_filled = [k for k in BRIEF_CORE_FIELDS if brief.get(k) is not None]
    core_missing = [k for k in BRIEF_CORE_FIELDS if brief.get(k) is None]
    complete = len(core_missing) == 0
    if complete and not AGENT_MODE_WORKBENCH.get("brief_complete"):
        AGENT_MODE_WORKBENCH["brief_complete"] = True
    return {
        "filled": filled,
        "missing": missing,
        "core_filled": core_filled,
        "core_missing": core_missing,
        "complete": complete,
        "progress": f"{len(core_filled)}/{len(BRIEF_CORE_FIELDS)}",
    }
