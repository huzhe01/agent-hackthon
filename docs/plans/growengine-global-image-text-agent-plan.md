# GrowEngine Global Image/Text Content Growth Agent Implementation Plan

> **For Hermes:** Use `subagent-driven-development` skill to implement this plan task-by-task if implementation starts in a new session.

**Goal:** Transform the existing `huzhe01/adproto` codebase into a demo-ready overseas image/text content growth Agent for cross-border merchants.

**Architecture:** Start from the existing React + Vite + Tailwind frontend and FastAPI backend. For hackathon/demo reliability, P0 is a static-first frontend demo that works on GitHub Pages without a backend; P1 adds FastAPI endpoints with the same data shape for local/API demos. The product flow is: product brief → image/text post variants → simulated publishing/performance → dashboard diagnosis → next content iteration plan.

**Tech Stack:** React 19, Vite, Tailwind CSS, Recharts, lucide-react, FastAPI, Pydantic, deterministic mock data, optional LLM API later.

---

## 0. Source Repo Status

Base repo already cloned and checked:

- Local source: `/opt/data/work/adproto`
- Remote: `https://github.com/huzhe01/adproto.git`
- Branch: `main`
- HEAD checked: `263600e`
- Existing public page: `https://huzhe01.github.io/adproto/`
- Important correction: `huzhe01.github.com/adproto` does not resolve; use `github.io` for GitHub Pages.

Reusable files/modules:

- `frontend/src/App.jsx` — current dashboard shell, sidebar, tabs, docs, campaign table, AI assistant state.
- `frontend/src/services/api.js` — existing API wrapper with backend fallback patterns.
- `frontend/src/components/CampaignSimulationModal.jsx` — current simulation modal, useful as reference but not the new core UI.
- `backend/api.py` — FastAPI app, existing campaign/metrics/diagnosis/bidding endpoints.
- `backend/simulator.py` — current OnlineLp simulation reference; do not reuse directly for content demo except conceptual pattern.
- `docker-compose.yml` — current two-service frontend/backend setup.

Key design constraint:

- The current GitHub Pages deployment is static. Therefore, the new demo must be able to run without a live backend. Backend API should be additive, not required for the first public demo.

---

## 1. Product Decision

### 1.1 Do NOT build live commerce first

Live commerce is too complex for a credible first demo because it requires:

- real-time stream state,
- comments/private messages,
- host behavior,
- SKU switching,
- live budget controls,
- realistic temporal causality.

It is easy to make but hard to make believable.

### 1.2 Build image/text content growth first

New positioning:

> **GrowEngine Global helps cross-border merchants turn scattered image/text social posts into a measurable growth loop. It tracks how each image, caption, platform, and market performs, then uses an AI Agent to recommend the next content iteration.**

Chinese positioning:

> **GrowEngine Global 是面向出海商家的图文内容增长 Agent：把多平台投稿、效果追踪、内容诊断和下一轮创意迭代连成闭环。**

Primary demo user:

- Small cross-border DTC merchant.
- Example product: portable blender / skincare kit / ergonomic desk lamp / AI note-taking SaaS.
- Markets: US, UK, Canada, SEA.
- Platforms: Instagram, Pinterest, Reddit, X/Twitter, Facebook.

---

## 2. End-to-End Demo Story

The demo should tell one clear story in 3–5 minutes:

1. **Merchant creates a content campaign**
   - Product: Portable Blender.
   - Market: US + UK.
   - Goal: Shopify clicks and sales.
   - Platforms: Instagram, Pinterest, Reddit, X.
   - Assets: 4 image concepts.

2. **Agent generates image/text post variants**
   - Same product becomes platform-specific posts.
   - Each post has title, caption, CTA, hashtags, creative angle, market, platform.

3. **System simulates publishing/performance**
   - Posts become `Published`, `Scheduled`, `Needs Review`, or `Failed`.
   - Metrics appear: impressions, engagement, saves, comments, clicks, CTR, leads, purchases, revenue.

4. **Dashboard identifies winners and losers**
   - Best platform.
   - Best creative angle.
   - Best market.
   - Posts with high engagement but weak CTA.
   - Posts with strong buying intent.

5. **Agent creates next iteration plan**
   - Generate 3–5 next posts.
   - Explain why each is recommended.
   - Output can be copied/exported as structured JSON.

---

## 3. MVP Scope

### P0: Static GitHub Pages Demo

Must work without backend.

Build a new frontend page/tab with local deterministic data:

- Product/campaign brief panel.
- Post variant cards with image-style thumbnails.
- KPI dashboard.
- Platform breakdown.
- Post performance table.
- Agent insight panel.
- Next post plan.

No real social API. No login. No database. No image upload. No real publishing.

### P1: Local Backend API Demo

Add FastAPI endpoints mirroring the static demo data:

- Generate post variants.
- Simulate performance.
- Diagnose posts.
- Generate next content plan.

The frontend should use backend if available; otherwise fallback to static mock.

### P2: Optional integration layer

Define connector interfaces but keep them mocked:

- Instagram connector.
- Pinterest connector.
- Reddit connector.
- X connector.
- Shopify/GA4 connector.

Do not implement real OAuth/API during first hackathon pass.

---

## 4. Core Data Model

Use the same concepts in frontend mock data and backend Pydantic models.

### 4.1 ProductBrief

```ts
type ProductBrief = {
  id: string;
  productName: string;
  category: string;
  priceUsd: number;
  grossMarginPct: number;
  targetMarkets: string[];
  targetAudience: string;
  goal: 'awareness' | 'traffic' | 'leads' | 'sales';
  landingPage: string;
  brandVoice: 'practical' | 'premium' | 'playful' | 'expert' | 'minimal';
};
```

Demo example:

```json
{
  "id": "brief_portable_blender_us",
  "productName": "BlendGo Portable Blender",
  "category": "Wellness / Kitchen Gadget",
  "priceUsd": 39,
  "grossMarginPct": 62,
  "targetMarkets": ["US", "UK"],
  "targetAudience": "busy fitness beginners and office workers",
  "goal": "sales",
  "landingPage": "https://example-shop.com/products/blendgo",
  "brandVoice": "practical"
}
```

### 4.2 ContentCampaign

```ts
type ContentCampaign = {
  id: string;
  name: string;
  briefId: string;
  status: 'draft' | 'scheduled' | 'published' | 'completed';
  startDate: string;
  endDate: string;
  platforms: PlatformName[];
  markets: string[];
  objective: 'website_clicks' | 'leads' | 'sales' | 'community_engagement';
};
```

### 4.3 PostVariant

```ts
type PostVariant = {
  id: string;
  campaignId: string;
  platform: 'Instagram' | 'Pinterest' | 'Reddit' | 'X' | 'Facebook';
  market: 'US' | 'UK' | 'CA' | 'SEA';
  status: 'draft' | 'scheduled' | 'published' | 'needs_review' | 'failed';
  angle: 'before_after' | 'gift_guide' | 'pain_point' | 'tutorial' | 'comparison' | 'ugc_review';
  imageConcept: string;
  thumbnailTheme: 'blue' | 'green' | 'orange' | 'purple' | 'pink';
  title: string;
  caption: string;
  cta: string;
  hashtags: string[];
  scheduledAt: string;
};
```

### 4.4 PostMetrics

```ts
type PostMetrics = {
  postId: string;
  impressions: number;
  likes: number;
  saves: number;
  comments: number;
  shares: number;
  clicks: number;
  leads: number;
  purchases: number;
  revenueUsd: number;
  spendUsd: number;
  ctr: number;
  engagementRate: number;
  cvr: number;
  roas: number | null;
  score: number;
};
```

Score formula for MVP:

```ts
score =
  0.30 * normalized(ctr) +
  0.25 * normalized(engagementRate) +
  0.20 * normalized(saves + shares) +
  0.15 * normalized(cvr) +
  0.10 * normalized(revenueUsd)
```

### 4.5 AgentInsight

```ts
type AgentInsight = {
  id: string;
  severity: 'success' | 'warning' | 'opportunity' | 'info';
  title: string;
  evidence: string;
  recommendation: string;
  relatedPostIds: string[];
  expectedImpact: string;
};
```

### 4.6 NextPostSuggestion

```ts
type NextPostSuggestion = {
  id: string;
  platform: PlatformName;
  market: string;
  angle: string;
  title: string;
  caption: string;
  cta: string;
  imagePrompt: string;
  reason: string;
  expectedMetricLift: string;
};
```

---

## 5. Dashboard Design

### 5.1 Layout

New main tab name:

- Sidebar label: `内容增长`
- Internal key: `contentGrowth`
- Page component: `ImageTextGrowthDashboard`

Page sections in order:

1. **Hero / Campaign Brief**
   - Campaign name.
   - Product.
   - Markets.
   - Platforms.
   - Goal.
   - Status.
   - Demo mode badge.

2. **KPI Cards**
   - Total Impressions.
   - Engagement Rate.
   - Clicks / CTR.
   - Leads.
   - Revenue.
   - Best Platform.
   - Winning Angle.
   - Agent Confidence.

3. **Performance Trend**
   - Recharts line/area chart.
   - X-axis: 7 days.
   - Lines: impressions, clicks, revenue.
   - Optional stacked bar: platform contribution.

4. **Platform Breakdown**
   - Cards or horizontal bars for Instagram, Pinterest, Reddit, X, Facebook.
   - Metrics per platform: impressions, CTR, engagement, revenue, score.
   - Highlight winner.

5. **Post Performance Table**
   - Thumbnail.
   - Platform.
   - Market.
   - Angle.
   - Title.
   - Status.
   - Engagement.
   - CTR.
   - Leads.
   - Revenue.
   - Score.
   - Agent note.

6. **Agent Insights Panel**
   - 4–6 insights.
   - Each insight includes evidence and recommended action.
   - Make it feel like a growth strategist, not generic chatbot text.

7. **Next Content Plan**
   - Cards for 3–5 suggested posts.
   - Include title/caption/CTA/image prompt/reason.
   - Button: `Copy JSON` or `Export Plan`.

### 5.2 Dashboard KPI Definitions

- `Total Impressions`: sum of all published post impressions.
- `Engagement Rate`: `(likes + saves + comments + shares) / impressions`.
- `CTR`: `clicks / impressions`.
- `Lead Rate`: `leads / clicks`.
- `Revenue`: sum of `revenueUsd`.
- `Best Platform`: platform with highest weighted score, not just impressions.
- `Winning Angle`: angle with highest average score.
- `Agent Confidence`: deterministic score from insight evidence quality, e.g. `86%`.

### 5.3 Visual Style

Keep existing Tailwind style but shift from domestic ad backend to global SaaS:

- Use English-first labels with optional Chinese subtitles.
- Use USD.
- Use platform badges.
- Add market flags/text chips: US, UK, CA, SEA.
- Use `Demo Mode` badge to be transparent.
- Avoid overusing “AI” in every label; show concrete actions.

---

## 6. Agent Logic

For MVP, use deterministic rules so the demo is stable.

### 6.1 Diagnosis Rules

Rules should produce insights like these:

1. **High engagement, low CTR**
   - Condition: engagementRate > 6% and ctr < 1.2%.
   - Diagnosis: content is interesting but CTA is weak.
   - Recommendation: add clearer CTA and product benefit in first line.

2. **High saves on Pinterest**
   - Condition: platform = Pinterest and saves / impressions above threshold.
   - Diagnosis: evergreen visual content works.
   - Recommendation: create more gift guide/checklist pins.

3. **High comments on Reddit, low conversion**
   - Condition: platform = Reddit, comments high, purchases low.
   - Diagnosis: topic triggers discussion but not purchase intent.
   - Recommendation: make next post more problem/solution and include proof.

4. **Strong revenue with low impressions**
   - Condition: revenueUsd high percentile and impressions below median.
   - Diagnosis: content is conversion efficient but under-distributed.
   - Recommendation: boost or repurpose to Instagram/Pinterest.

5. **Creative fatigue**
   - Condition: trend clicks down for same angle over days.
   - Diagnosis: angle may be saturated.
   - Recommendation: rotate to comparison/tutorial angle.

6. **Market mismatch**
   - Condition: UK CTR high but revenue low, US revenue high.
   - Diagnosis: UK interest exists but landing offer/pricing may not fit.
   - Recommendation: localized shipping/price proof for UK.

### 6.2 Next Plan Generation Rules

Next suggestions derive from winners:

- If best angle is `ugc_review`, create two variants with stronger proof.
- If Pinterest saves are high, create gift-guide/checklist posts.
- If Instagram carousel wins, suggest before/after or step-by-step carousel.
- If Reddit comments are high, suggest discussion post with soft CTA.
- If X clicks are high, suggest concise benefit-led thread/post.

Output should be copyable JSON.

---

## 7. File-Level Implementation Plan

The plan below assumes the new repo will be named exactly `agent-hackthon` as requested.

### Task 1: Bootstrap New Repo from adproto

**Objective:** Create the new working directory using `adproto` as base, without pushing yet.

**Files:**

- Create directory: `/opt/data/work/agent-hackthon`
- Source: `/opt/data/work/adproto`

**Steps:**

```bash
cd /opt/data/work
rm -rf agent-hackthon
git clone https://github.com/huzhe01/adproto.git agent-hackthon
cd agent-hackthon
git remote remove origin
```

When the new GitHub repo exists later:

```bash
git remote add origin https://github.com/<owner>/agent-hackthon.git
git push -u origin main
```

**Verification:**

```bash
git status
npm --prefix frontend ci --no-audit --no-fund
npm --prefix frontend run build
```

Expected: frontend build passes.

**Commit:**

Do not commit until the new repo remote is created, unless working locally only.

---

### Task 2: Add Frontend Demo Data

**Objective:** Add deterministic content growth mock data that works on GitHub Pages.

**Files:**

- Create: `frontend/src/data/contentDemoData.js`

**Content shape:**

Export:

```js
export const demoProductBrief = {...};
export const demoCampaign = {...};
export const demoPostVariants = [...];
export const demoDailyTrend = [...];
export const demoPlatformBenchmarks = {...};
```

Minimum dataset:

- 1 product brief.
- 1 campaign.
- 12 post variants.
- 5 platforms: Instagram, Pinterest, Reddit, X, Facebook.
- 2 markets: US, UK.
- 6 angles: UGC review, gift guide, before/after, tutorial, comparison, pain point.
- 7 days of trend data.

**Implementation notes:**

- Use local SVG-like visual thumbnails via gradient metadata instead of binary image files.
- Do not import remote images for P0; public demo should not depend on third-party image URLs.

**Verification:**

```bash
npm --prefix frontend run build
```

Expected: build passes.

---

### Task 3: Add Frontend Analytics Helpers

**Objective:** Calculate KPI summaries, rankings, and scores from mock data.

**Files:**

- Create: `frontend/src/lib/contentAnalytics.js`

**Functions:**

```js
export function calculatePostMetrics(posts) {}
export function summarizeContentPerformance(posts) {}
export function rankPlatforms(posts) {}
export function rankAngles(posts) {}
export function generateAgentInsights(posts, summary) {}
export function generateNextPostPlan(posts, summary, insights) {}
```

**Behavior:**

- All outputs must be deterministic.
- No random calls in render path.
- Score must be explainable.

**Verification script:**

Create a temporary Node check if needed:

```bash
node -e "import('./frontend/src/lib/contentAnalytics.js').then(m => console.log(Object.keys(m)))"
```

Expected: exported function names printed.

---

### Task 4: Create Content Thumbnail Component

**Objective:** Render image-like post thumbnails without external assets.

**Files:**

- Create: `frontend/src/components/content/ContentThumbnail.jsx`

**Props:**

```ts
{
  theme: 'blue' | 'green' | 'orange' | 'purple' | 'pink',
  angle: string,
  title: string,
  platform: string
}
```

**UI behavior:**

- Gradient background.
- Platform badge.
- Angle label.
- Short title overlay.
- 4:5 aspect ratio for social image feel.

**Verification:**

```bash
npm --prefix frontend run build
```

Expected: build passes.

---

### Task 5: Create KPI Card Component

**Objective:** Reusable KPI cards for the content dashboard.

**Files:**

- Create: `frontend/src/components/content/ContentKpiCard.jsx`

**Props:**

```ts
{
  label: string,
  value: string,
  change?: string,
  tone?: 'blue' | 'green' | 'orange' | 'purple' | 'slate',
  icon?: ReactComponent,
  helper?: string
}
```

**Verification:**

```bash
npm --prefix frontend run build
```

---

### Task 6: Create Platform Breakdown Component

**Objective:** Show which platforms perform best and why.

**Files:**

- Create: `frontend/src/components/content/PlatformBreakdown.jsx`

**Props:**

```ts
{
  platforms: Array<{
    platform: string,
    impressions: number,
    engagementRate: number,
    ctr: number,
    revenueUsd: number,
    score: number
  }>
}
```

**UI behavior:**

- Horizontal bar or card list.
- Highlight highest score as `Best channel`.
- Show platform-specific notes.

---

### Task 7: Create Post Performance Table

**Objective:** Main evidence table for published image/text posts.

**Files:**

- Create: `frontend/src/components/content/PostPerformanceTable.jsx`

**Columns:**

- Thumbnail.
- Platform.
- Market.
- Angle.
- Title.
- Status.
- Engagement Rate.
- CTR.
- Leads.
- Revenue.
- Score.
- Agent Note.

**Interactions for P0:**

- Sort by score descending by default.
- Allow filter by platform and market if easy.
- No pagination needed for 12 rows.

---

### Task 8: Create Agent Insights Panel

**Objective:** Show concrete, evidence-backed recommendations.

**Files:**

- Create: `frontend/src/components/content/AgentInsightsPanel.jsx`

**Display:**

Each insight card should show:

- severity badge,
- title,
- evidence,
- recommendation,
- expected impact.

Example insight:

```text
Pinterest saves are 2.4x above average
Evidence: Gift-guide pins generated 412 saves from 18.2k impressions.
Recommendation: Create two more gift-guide pins with clearer price anchor under $50.
Expected impact: +15–25% outbound clicks.
```

---

### Task 9: Create Next Content Plan Component

**Objective:** Render the Agent’s next recommended image/text posts.

**Files:**

- Create: `frontend/src/components/content/NextPostPlan.jsx`

**Features:**

- Cards for 3–5 next post suggestions.
- Show platform, market, angle, title, caption, CTA, image prompt, reason.
- Add `Copy JSON` button.

**P0 implementation:**

- `navigator.clipboard.writeText(JSON.stringify(plan, null, 2))`.
- If clipboard unavailable, show `<textarea>` fallback or silently no-op with button state.

---

### Task 10: Create Main Dashboard Page

**Objective:** Assemble all content components into the demo page.

**Files:**

- Create: `frontend/src/pages/ImageTextGrowthDashboard.jsx`

**Imports:**

- `demoProductBrief`, `demoCampaign`, `demoPostVariants`, `demoDailyTrend` from `../data/contentDemoData`.
- analytics helpers from `../lib/contentAnalytics`.
- Recharts components for trend chart.
- content components from `../components/content/`.

**Sections:**

1. Campaign brief header.
2. KPI cards.
3. Trend chart.
4. Platform breakdown.
5. Post performance table.
6. Agent insights.
7. Next content plan.

**Verification:**

```bash
npm --prefix frontend run build
```

Expected: build passes and chunk warning is acceptable for now.

---

### Task 11: Wire New Tab into Existing App

**Objective:** Add `内容增长` tab to existing sidebar and render the new dashboard.

**Files:**

- Modify: `frontend/src/App.jsx`

**Changes:**

1. Import page:

```js
import ImageTextGrowthDashboard from './pages/ImageTextGrowthDashboard';
```

2. Add title:

```js
contentGrowth: '图文内容增长',
```

3. Add sidebar item near top:

```jsx
<SidebarItem
  icon={Sparkles}
  label="内容增长"
  active={activeTab === 'contentGrowth'}
  onClick={() => setActiveTab('contentGrowth')}
/>
```

4. Render the page before old dashboard content:

```jsx
{activeTab === 'contentGrowth' ? (
  <ImageTextGrowthDashboard />
) : isDocsView ? (
  ...
) : (
  ...existing dashboard...
)}
```

5. Optional: set default active tab to `contentGrowth` for demo:

```js
const [activeTab, setActiveTab] = useState('contentGrowth');
```

**Verification:**

```bash
npm --prefix frontend run build
```

Expected: build passes.

---

### Task 12: Rename Product Surface for Demo

**Objective:** Make the product feel like global content growth, not domestic ad backend.

**Files:**

- Modify: `frontend/src/App.jsx`
- Modify: `README.md`
- Modify: `README_CN.md`

**Changes:**

- Brand display: `GrowEngine Global`.
- User role: `Growth Operator`.
- Sidebar group: `Global Growth`.
- Replace visible default labels where easy:
  - `广告投放` → `内容增长` or `Global Growth`.
  - `新建投放` → `New Content Campaign`.

Do not rewrite all legacy pages in P0; just make the first landing page coherent.

**Verification:**

```bash
npm --prefix frontend run build
```

---

### Task 13: Add Backend Pydantic Models

**Objective:** Define backend content model types matching frontend data.

**Files:**

- Create: `backend/content_models.py`

**Models:**

- `ProductBrief`
- `ContentCampaign`
- `PostVariant`
- `PostMetrics`
- `AgentInsight`
- `NextPostSuggestion`
- `ContentDemoState`

Use Pydantic v2 style.

**Verification:**

```bash
cd backend
uv run --with-requirements requirements.txt python - <<'PY'
from content_models import ProductBrief
print(ProductBrief.model_fields.keys())
PY
```

Expected: model fields printed.

---

### Task 14: Add Backend Seed Data and Analytics

**Objective:** Mirror frontend demo data and deterministic rules in backend.

**Files:**

- Create: `backend/content_seed.py`
- Create: `backend/content_engine.py`

**Functions in `content_engine.py`:**

```py
def calculate_summary(posts): ...
def rank_platforms(posts): ...
def rank_angles(posts): ...
def generate_agent_insights(posts, summary): ...
def generate_next_post_plan(posts, summary, insights): ...
def build_demo_state(): ...
```

**Verification:**

```bash
cd backend
uv run --with-requirements requirements.txt python - <<'PY'
from content_engine import build_demo_state
state = build_demo_state()
print(len(state.posts), len(state.insights), len(state.next_plan))
PY
```

Expected: counts are non-zero.

---

### Task 15: Add Backend Content API Router

**Objective:** Add content growth endpoints without bloating `backend/api.py` further.

**Files:**

- Create: `backend/content_api.py`
- Modify: `backend/api.py`

**Endpoints:**

```text
GET  /api/content/demo-state
GET  /api/content/summary
GET  /api/content/posts
GET  /api/content/insights
GET  /api/content/next-plan
POST /api/content/generate-posts
POST /api/content/simulate-performance
```

**`backend/api.py` change:**

```py
from content_api import router as content_router
app.include_router(content_router)
```

If relative import issues arise, keep same pattern as current flat `api.py` execution.

**Verification:**

```bash
cd backend
uv run --with-requirements requirements.txt --with httpx python - <<'PY'
from fastapi.testclient import TestClient
import api
client = TestClient(api.app)
for path in ['/api/content/demo-state','/api/content/summary','/api/content/posts','/api/content/insights','/api/content/next-plan']:
    r = client.get(path)
    print(path, r.status_code)
PY
```

Expected: all `200`.

---

### Task 16: Add Frontend Content API Fallback

**Objective:** Let the dashboard use backend if available but still work statically.

**Files:**

- Create: `frontend/src/services/contentApi.js`

**Functions:**

```js
export async function getContentDemoState() {}
export async function getContentSummary() {}
export async function getContentPosts() {}
export async function getContentInsights() {}
export async function getNextPostPlan() {}
```

**Fallback rule:**

- Try `VITE_API_BASE_URL + /api/content/demo-state`.
- On failure, return local mock + computed analytics.
- Expose `source: 'api' | 'local-demo'` so UI can show a badge.

**Verification:**

- With no backend: dashboard loads in local demo mode.
- With backend: dashboard loads in API mode.

Commands:

```bash
npm --prefix frontend run build
```

---

### Task 17: Update README for Hackathon Story

**Objective:** Make the repo understandable to judges/users.

**Files:**

- Modify: `README.md`
- Modify: `README_CN.md`

**README structure:**

1. Product one-liner.
2. Demo screenshot/gif placeholder.
3. Problem.
4. Solution.
5. Demo flow.
6. Architecture.
7. Run locally.
8. Public GitHub Pages link.
9. Roadmap.

**Key English tagline:**

```text
GrowEngine Global turns image/text social posts into a measurable growth loop for cross-border merchants.
```

**Key Chinese tagline:**

```text
GrowEngine Global 帮助出海商家把图文投稿变成可量化、可复盘、可迭代的增长闭环。
```

---

### Task 18: Cleanup Heavy Demo Artifacts Later

**Objective:** Reduce repo weight before creating/pushing the new repo.

**Files/directories to review:**

- `Simple_Tiktok_App/app-debug*.apk`
- `Simple_Tiktok_App/app/src/main/res/raw/*.mp3`
- `ad_rec_backend/data/clicks.csv`
- `backend/saved_model/onlineLpTest/period.csv`

**Decision:**

- If `agent-hackthon` is strictly for content growth demo, remove APKs and large media files.
- If preserving history matters, use Git LFS or keep in old repo only.

**Suggested cleanup for new repo only:**

```bash
git rm -r Simple_Tiktok_App
git rm ad_rec_backend/data/clicks.csv || true
git rm backend/saved_model/onlineLpTest/period.csv || true
```

Only do this after confirming the new repo does not need Android/TikTok app assets.

---

## 8. Acceptance Criteria

### Demo Acceptance

- Public/static frontend works without backend.
- Main page opens directly to `内容增长` / `Content Growth` dashboard.
- Viewer can understand the full flow in under 60 seconds.
- Dashboard shows:
  - campaign brief,
  - post variants,
  - performance KPIs,
  - platform breakdown,
  - post performance table,
  - agent insights,
  - next post suggestions.
- Agent recommendations are evidence-backed and specific.
- No live-commerce concepts appear in the P0 demo.

### Technical Acceptance

- `npm --prefix frontend run build` passes.
- FastAPI imports if backend work is included.
- Content endpoints return `200` if backend work is included.
- GitHub Pages deployment can serve the dashboard without API.
- No secrets or API keys are committed.

---

## 9. Suggested Commit Plan

After the new repo is created:

```bash
git add frontend/src/data frontend/src/lib frontend/src/components/content frontend/src/pages
git commit -m "feat: add image-text content growth dashboard"

git add frontend/src/App.jsx
git commit -m "feat: make content growth dashboard the demo entry"

git add backend/content_models.py backend/content_seed.py backend/content_engine.py backend/content_api.py backend/api.py
git commit -m "feat: add content growth API demo endpoints"

git add README.md README_CN.md
git commit -m "docs: describe GrowEngine Global hackathon demo"
```

If cleanup is confirmed:

```bash
git rm -r Simple_Tiktok_App
git commit -m "chore: remove unrelated Android demo artifacts"
```

---

## 10. Implementation Order Recommendation

Do this exact order:

1. Frontend local demo data.
2. Frontend analytics helpers.
3. Dashboard components.
4. Main dashboard page.
5. Wire sidebar/default landing.
6. Build verification.
7. README rewrite.
8. Backend API parity.
9. Optional cleanup.
10. Push to new `agent-hackthon` repo.

Reason: this gets a visible demo fastest and avoids being blocked by backend/API work.

---

## 11. Future Roadmap After P0

### Real data import

- CSV import from social platforms.
- Manual metrics input.
- UTM click import.
- Shopify order export import.

### Real publishing integrations

- Buffer/Later/Hootsuite API first, easier than direct platform APIs.
- Later direct APIs: Meta/Instagram, Pinterest, Reddit, X.

### Real Agent layer

- LLM-generated post variants.
- LLM-generated diagnosis explanations.
- Human approval queue.
- Brand voice memory.
- Multi-language localization.

### SaaS layer

- Auth.
- Workspace.
- Database.
- Billing.
- Audit log.
- Role-based access.

---

## 12. Final Product Narrative

Use this for README/pitch:

```text
Cross-border merchants publish content everywhere, but their growth loop is broken: posts live across Instagram, Pinterest, Reddit, X, and Facebook, while performance data, creative learnings, and next-step decisions are scattered.

GrowEngine Global turns image/text posts into a measurable growth loop. It tracks every post by platform, market, creative angle, and business outcome, then uses an AI Agent to diagnose what worked and generate the next content iteration.
```

Chinese version:

```text
出海商家每天在 Instagram、Pinterest、Reddit、X、Facebook 等平台发布大量图文内容，但内容表现、创意经验和下一步动作是割裂的。

GrowEngine Global 把图文投稿变成可量化的增长闭环：按平台、市场、创意角度和业务结果追踪每条内容表现，并由 AI Agent 诊断有效模式，生成下一轮投稿方案。
```
