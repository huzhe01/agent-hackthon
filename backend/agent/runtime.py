"""Runtime prompt helpers for Qiji/OpenAI-compatible agent calls."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .registry import build_tool_prompt


SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def build_runtime_system_prompt() -> str:
    skills = _skill_index()
    skill_lines = "\n".join(
        f"- {item['name']}: {item['description']}"
        for item in skills
    )
    return "\n".join([
        "MaiDeal agent runtime",
        "你是面向出海直播电商的工具调用 Agent。先识别用户目标，再选择合适的 skill 和 tool。",
        "",
        build_tool_prompt(),
        "",
        "可用 skills:",
        skill_lines,
        "",
        "调用原则:",
        "- 预算、渠道、商品、库存等字段不足时先追问，不要提前生成 plan。",
        "- 没有真实数据时调用 simulate_live_workbench，不要编造静态页面数据。",
        "- 外部发布、媒体 RTA/RTB、数据库查询都必须遵守权限和审核边界。",
    ])


def _skill_index() -> List[Dict[str, str]]:
    skills = []
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        metadata = _frontmatter(path.read_text(encoding="utf-8"))
        skills.append({
            "name": metadata.get("name") or path.parent.name,
            "description": metadata.get("description") or "",
        })
    return skills


def _frontmatter(text: str) -> Dict[str, str]:
    if not text.startswith("---"):
        return {}
    _, raw, _body = text.split("---", 2)
    values: Dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values
