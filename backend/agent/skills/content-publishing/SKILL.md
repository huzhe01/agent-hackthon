---
name: content-publishing
description: Generate ecommerce creative packages for Xiaohongshu or social posting with Qiji gpt-image-2 image generation, copywriting, manual review, and optional upload preparation.
---

# Content Publishing

Use this skill when a MaiDeal agent needs to create publishable ecommerce material.

## Workflow

1. Confirm product, target audience, platform, selling points, and compliance constraints.
2. Call `generate_marketing_content` to create:
   - image prompt for `gpt-image-2`
   - Xiaohongshu-style title, body, hashtags
   - upload package metadata
3. If `image.status=generated`, attach the returned image URL to the material package.
4. If `image.status=draft_only`, ask the operator to configure `QIJI_API_KEY` or review the prompt manually.
5. Never claim that the content was posted unless a platform upload API confirms it.

## Safety

- Keep API keys only on the backend.
- Require human review before Xiaohongshu publishing.
- Do not promise product effects that are unsupported by the product brief.
