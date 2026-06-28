"""Runtime prompt helpers for Qiji/OpenAI-compatible agent calls."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .registry import TOOLS


SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def build_runtime_system_prompt(
    skill_names: Optional[Iterable[str]] = None,
    tool_names: Optional[Iterable[str]] = None,
    include_skill_bodies: bool = True,
) -> str:
    skills = load_skill_documents(skill_names=skill_names)
    skill_lines = "\n".join(
        f"- {item['name']}: {item['description']}"
        for item in skills
    )
    skill_sections = []
    if include_skill_bodies:
        skill_sections = [
            f"## Skill: {item['name']}\n{item['content']}"
            for item in skills
        ]

    principles = [
        "- 预算、渠道、商品、库存等字段不足时先追问，不要提前生成 plan。",
        "- 外部发布、媒体 RTA/RTB、数据库查询都必须遵守权限和审核边界。",
    ]
    selected_tools = set(tool_names or [])
    if not selected_tools or "simulate_live_workbench" in selected_tools:
        principles.insert(1, "- 没有真实数据时调用 simulate_live_workbench，不要编造静态页面数据。")

    return "\n".join([
        "MaiDeal agent runtime",
        "你是面向出海直播电商的工具调用 Agent。先识别用户目标，再选择合适的 skill 和 tool。",
        "",
        _build_selected_tool_prompt(tool_names),
        "",
        "可用 skills:",
        skill_lines,
        "",
        "Skill 文档:",
        "\n\n".join(skill_sections) if skill_sections else "- 未载入完整 skill 文档",
        "",
        "调用原则:",
        "\n".join(principles),
    ])


def load_skill_documents(
    skill_names: Optional[Iterable[str]] = None,
    max_chars_per_skill: int = 6000,
) -> List[Dict[str, str]]:
    """Load selected local SKILL.md files for the runtime prompt."""
    selected = set(skill_names or [])
    skills = []
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        raw_text = path.read_text(encoding="utf-8")
        metadata = _frontmatter(raw_text)
        name = metadata.get("name") or path.parent.name
        if selected and name not in selected and path.parent.name not in selected:
            continue
        content = _body_without_frontmatter(raw_text).strip()
        if len(content) > max_chars_per_skill:
            content = f"{content[:max_chars_per_skill].rstrip()}\n..."
        skills.append({
            "name": name,
            "description": metadata.get("description") or "",
            "content": content,
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


def _body_without_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    return parts[2] if len(parts) == 3 else text


def _build_selected_tool_prompt(tool_names: Optional[Iterable[str]] = None) -> str:
    selected = set(tool_names or [])
    tools = [
        tool
        for name, tool in TOOLS.items()
        if not selected or name in selected
    ]
    return "可用 agent 工具:\n" + "\n".join(
        f"- {tool.name}: {tool.description} (skill={tool.skill})"
        for tool in tools
    )
