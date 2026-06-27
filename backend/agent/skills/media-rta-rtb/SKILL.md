---
name: media-rta-rtb
description: Inspect media platform API acquisition paths for Ocean Engine, Qianchuan, and Xiaohongshu JuGuang, especially permission-gated RTA/RTB or reporting integrations.
---

# Media RTA/RTB

Use this skill when the agent needs to plan a media platform integration.

## Workflow

1. Call `inspect_media_api` with platform names and requested capability.
2. Separate:
   - currently available reporting/material APIs
   - permission-gated RTA/RTB or realtime decision APIs
   - required advertiser/app authorization
3. Recommend a phased integration:
   - OAuth and advertiser authorization
   - reports and material data
   - conversion callbacks
   - realtime decision or bidding after platform approval

## Guardrail

Do not say RTA/RTB is connected until the platform confirms whitelist access and callback validation.
