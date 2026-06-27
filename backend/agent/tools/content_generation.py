"""Qiji image/copy generation and Xiaohongshu publishing preparation."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


DEFAULT_IMAGE_MODEL = "gpt-image-2"


def generate_marketing_content(arguments: Dict[str, Any]) -> Dict[str, Any]:
    product = str(arguments.get("product") or "商品")
    selling_points = _list(arguments.get("selling_points")) or ["适合直播间种草", "高转化卖点清晰"]
    audience = str(arguments.get("audience") or "小红书年轻消费人群")
    platform = str(arguments.get("platform") or "小红书")
    image_prompt = str(arguments.get("image_prompt") or _default_image_prompt(product, selling_points))
    offline = bool(arguments.get("offline"))

    copywriting = _copywriting(product, selling_points, audience, platform)
    image_result = _generate_image(image_prompt, offline=offline)
    return {
        "success": True,
        "image_model": DEFAULT_IMAGE_MODEL,
        "skill": "content-publishing",
        "product": product,
        "platform": platform,
        "copywriting": copywriting,
        "image_prompt": image_prompt,
        "image": image_result,
        "publish_status": "manual_review_required",
        "xhs_upload": {
            "status": "manual_review_required",
            "reason": "小红书投稿需要账号、素材版权和最终人工审核；当前工具只生成待发布物料包。",
            "required_env": ["XHS_ACCESS_TOKEN", "XHS_ACCOUNT_ID"],
        },
    }


def _generate_image(prompt: str, offline: bool = False) -> Dict[str, Any]:
    api_key = os.getenv("QIJI_API_KEY", "")
    base_url = (os.getenv("QIJI_BASE_URL") or "https://api.openai-next.com/v1").rstrip("/")
    if offline or not api_key:
        return {
            "status": "draft_only",
            "setup_required": not offline,
            "message": "未调用真实图片接口，已生成 prompt 草稿。",
            "url": None,
        }
    try:
        response = httpx.post(
            f"{base_url}/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEFAULT_IMAGE_MODEL,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        first = (data.get("data") or [{}])[0]
        return {
            "status": "generated",
            "url": first.get("url"),
            "revised_prompt": first.get("revised_prompt"),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "url": None,
            "error": str(exc),
            "fallback": "请先用 qiji_api.md 中的 dall-e-3 或 gpt-image-2 最小请求确认 key 与模型可用。",
        }


def _copywriting(product: str, selling_points: List[str], audience: str, platform: str) -> Dict[str, Any]:
    title = f"{platform}爆款笔记｜{product}真实体验"
    hook = f"如果你也在找一个适合直播间冲量的{product}，先看这条。"
    bullets = [f"{index + 1}. {point}" for index, point in enumerate(selling_points[:5])]
    body = "\n".join([hook, *bullets, "直播间建议：前 3 秒直接展示使用场景，结尾引导评论关键词领取优惠。"])
    return {
        "title": title,
        "body": body,
        "hashtags": [f"#{product}", "#直播电商", "#好物种草", "#出海品牌"],
        "target_audience": audience,
    }


def _default_image_prompt(product: str, selling_points: List[str]) -> str:
    return (
        f"真实摄影风格的小红书封面图，主体是{product}，突出{selling_points[0]}，"
        "干净明亮背景，生活方式场景，高级但不夸张，适合电商种草。"
    )


def _list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in value.replace("，", ",").split(",") if part.strip()]
    return []
