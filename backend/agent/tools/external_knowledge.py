"""External knowledge search and local memory persistence."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List
from urllib.parse import urlencode

import httpx


DEFAULT_SEARCH_URL = "https://aisearchapi.cloudsway.net/api/search/smart"
BASE_DIR = Path(__file__).resolve().parents[1]


def refresh_business_knowledge(arguments: Dict[str, Any]) -> Dict[str, Any]:
    query = str(arguments.get("query") or "").strip()
    if not query:
        return {"success": False, "error": "query 不能为空"}

    offline_results = arguments.get("offline_results")
    if offline_results:
        results = _normalize_results(offline_results)
        source = "offline_results"
    else:
        search = _search_cloudsway(query, arguments)
        if not search["success"]:
            return search
        results = search["results"]
        source = "cloudsway"

    knowledge_dir = Path(arguments.get("knowledge_dir") or BASE_DIR / "knowledge")
    memory_dir = Path(arguments.get("memory_dir") or BASE_DIR / "memory")
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slug(query)
    knowledge_path = knowledge_dir / f"{stamp}-{slug}.jsonl"
    memory_path = memory_dir / f"{stamp}-{slug}.json"

    with knowledge_path.open("w", encoding="utf-8") as file:
        for result in results:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

    memory = {
        "query": query,
        "created_at": stamp,
        "source": source,
        "summary": _summarize(query, results),
        "signals": [_signal(result) for result in results[:6]],
    }
    memory_path.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "success": True,
        "query": query,
        "source": source,
        "count": len(results),
        "knowledge_path": str(knowledge_path),
        "memory_path": str(memory_path),
        "memory": memory,
    }


def _search_cloudsway(query: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("CLOUDSWAY_SEARCH_KEY") or os.getenv("XIAOSU_SEARCH_API_KEY") or ""
    if not api_key:
        return {
            "success": False,
            "error": "CLOUDSWAY_SEARCH_KEY 或 XIAOSU_SEARCH_API_KEY 未配置。",
            "setup": "配置 key 后可调用 xiaosu_api.md 中的 Cloudsway SmartSearch。",
        }
    params = {
        "q": query,
        "count": max(1, min(20, int(arguments.get("count") or 8))),
        "enableContent": "true",
        "contentType": "TEXT",
        "mainText": "true",
        "contentTimeout": 3,
    }
    if arguments.get("freshness"):
        params["freshness"] = arguments["freshness"]
    response = httpx.get(
        f"{DEFAULT_SEARCH_URL}?{urlencode(params)}",
        headers={"Authorization": api_key, "pragma": "no-cache"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    raw_results = data.get("webPages", {}).get("value") or data.get("results") or []
    return {"success": True, "results": _normalize_results(raw_results)}


def _normalize_results(raw_results: Any) -> List[Dict[str, Any]]:
    results = []
    for item in raw_results or []:
        title = item.get("title") or item.get("name") or "Untitled"
        url = item.get("url") or item.get("link") or ""
        snippet = item.get("snippet") or item.get("description") or item.get("main_text") or item.get("content") or ""
        results.append({
            "title": str(title),
            "url": str(url),
            "snippet": str(snippet)[:1000],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })
    return results


def _summarize(query: str, results: List[Dict[str, Any]]) -> str:
    if not results:
        return f"未找到与 {query} 相关的外部经营线索。"
    top_titles = "；".join(result["title"] for result in results[:3])
    return f"围绕 {query} 共沉淀 {len(results)} 条线索，重点关注：{top_titles}。"


def _signal(result: Dict[str, Any]) -> Dict[str, str]:
    return {
        "title": result["title"],
        "url": result["url"],
        "insight": result["snippet"][:160] or "需要进一步阅读全文。",
    }


def _slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text).strip("-").lower()
    return value[:80] or "knowledge"
