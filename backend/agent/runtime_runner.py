"""Multi-round Qiji/OpenAI-compatible agent runtime."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

from .registry import dispatch_agent_tool, get_agent_tool_schemas
from .runtime import build_runtime_system_prompt, load_skill_documents


DEFAULT_BASE_URL = "https://api.openai-next.com/v1"
DEFAULT_MODEL = "gpt-5"


async def run_agent_runtime(
    messages: List[Dict[str, Any]],
    config: Optional[Dict[str, str]] = None,
    client: Any = None,
    model: Optional[str] = None,
    tool_names: Optional[Iterable[str]] = None,
    skill_names: Optional[Iterable[str]] = None,
    max_tool_rounds: int = 6,
    enable_tools: bool = True,
) -> Dict[str, Any]:
    """Run a bounded tool-calling loop against a Qiji/OpenAI-compatible model."""
    config = config or {}
    selected_model = model or config.get("model") or DEFAULT_MODEL
    skills = load_skill_documents(skill_names=skill_names)
    api_messages = [
        {
            "role": "system",
            "content": build_runtime_system_prompt(
                skill_names=[skill["name"] for skill in skills],
                tool_names=tool_names,
            ),
        },
        *[dict(message) for message in messages],
    ]
    tools = get_agent_tool_schemas(tool_names) if enable_tools else []
    runtime_client = client or _create_openai_client(config)

    tool_calls_log: List[Dict[str, Any]] = []
    tool_results_log: List[Dict[str, Any]] = []

    for round_index in range(max(1, max_tool_rounds)):
        call_kwargs: Dict[str, Any] = {
            "model": selected_model,
            "messages": api_messages,
            "stream": False,
            "max_completion_tokens": 1200,
            "extra_body": {"reasoning_effort": "minimal"},
        }
        if tools:
            call_kwargs["tools"] = tools

        completion = await runtime_client.chat.completions.create(**call_kwargs)
        choice = completion.choices[0] if getattr(completion, "choices", None) else None
        assistant_message = getattr(choice, "message", None) if choice else None
        if assistant_message is None:
            return {
                "success": False,
                "model": selected_model,
                "output_text": "",
                "error": "模型没有返回 message",
                "rounds": round_index + 1,
                "tool_calls": tool_calls_log,
                "tool_results": tool_results_log,
                "skills_loaded": [skill["name"] for skill in skills],
            }

        tool_calls = list(getattr(assistant_message, "tool_calls", None) or [])
        content = getattr(assistant_message, "content", None) or ""
        if not tool_calls:
            return {
                "success": True,
                "model": selected_model,
                "output_text": content,
                "rounds": round_index + 1,
                "tool_calls": tool_calls_log,
                "tool_results": tool_results_log,
                "skills_loaded": [skill["name"] for skill in skills],
            }

        api_messages.append(_assistant_message_to_dict(assistant_message))
        for tool_call in tool_calls:
            name = getattr(getattr(tool_call, "function", None), "name", "")
            raw_arguments = getattr(getattr(tool_call, "function", None), "arguments", "{}") or "{}"
            arguments = _loads_json_object(raw_arguments)
            tool_call_id = getattr(tool_call, "id", f"call_{round_index}_{len(tool_calls_log)}")
            result = dispatch_agent_tool(name, arguments)

            call_record = {
                "id": tool_call_id,
                "name": name,
                "arguments": arguments,
            }
            result_record = {
                "id": tool_call_id,
                "name": name,
                "result": result,
            }
            tool_calls_log.append(call_record)
            tool_results_log.append(result_record)

            api_messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    return {
        "success": False,
        "model": selected_model,
        "output_text": "",
        "error": f"已达到最大工具调用轮次 {max_tool_rounds}",
        "rounds": max_tool_rounds,
        "tool_calls": tool_calls_log,
        "tool_results": tool_results_log,
        "skills_loaded": [skill["name"] for skill in skills],
    }


def _create_openai_client(config: Dict[str, str]) -> Any:
    api_key = config.get("api_key") or ""
    if not api_key:
        raise ValueError("QIJI_API_KEY 未配置，无法启动 agent runtime")

    from openai import AsyncOpenAI

    return AsyncOpenAI(
        api_key=api_key,
        base_url=config.get("api_base") or DEFAULT_BASE_URL,
        default_headers={"User-Agent": "curl/8.5.0"},
        timeout=120.0,
    )


def _assistant_message_to_dict(message: Any) -> Dict[str, Any]:
    if isinstance(message, dict):
        return message
    if hasattr(message, "model_dump"):
        dumped = message.model_dump(exclude_none=True)
        dumped.setdefault("role", "assistant")
        return dumped

    payload: Dict[str, Any] = {
        "role": "assistant",
        "content": getattr(message, "content", None),
    }
    tool_calls = []
    for tool_call in list(getattr(message, "tool_calls", None) or []):
        function = getattr(tool_call, "function", None)
        tool_calls.append({
            "id": getattr(tool_call, "id", ""),
            "type": getattr(tool_call, "type", "function"),
            "function": {
                "name": getattr(function, "name", ""),
                "arguments": getattr(function, "arguments", "{}") or "{}",
            },
        })
    if tool_calls:
        payload["tool_calls"] = tool_calls
    return payload


def _loads_json_object(raw: str) -> Dict[str, Any]:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}
