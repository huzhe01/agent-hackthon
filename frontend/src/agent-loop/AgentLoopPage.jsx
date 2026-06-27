import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowUp,
  BarChart3,
  Bot,
  Boxes,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Circle,
  Clock3,
  Compass,
  Database,
  ExternalLink,
  Eye,
  Film,
  FolderKanban,
  Image as ImageIcon,
  Loader2,
  Mic,
  Paperclip,
  Plus,
  Radio,
  RefreshCw,
  Search,
  ShieldCheck,
  ShoppingBag,
  SlidersHorizontal,
  Sparkles,
  Target,
  TrendingUp,
  User,
  Zap,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import * as api from '../services/api';

const fallbackModels = [
  {
    id: 'gpt-5',
    label: 'gpt-5',
    enabled_by_default: true,
    supports_tools: true,
    provider: 'Qiji',
  },
  { id: 'gpt-5.5', label: 'gpt-5.5', enabled_by_default: false, supports_tools: true, provider: 'Qiji' },
  { id: 'gpt-5.5-openai-compact', label: 'gpt-5.5 compact', enabled_by_default: false, supports_tools: true, provider: 'Qiji' },
  { id: 'gpt-5-mini', label: 'gpt-5-mini', enabled_by_default: false, supports_tools: true, provider: 'Qiji' },
  { id: 'gpt-5-nano', label: 'gpt-5-nano', enabled_by_default: false, supports_tools: true, provider: 'Qiji' },
  { id: 'qwen-max', label: 'qwen-max', enabled_by_default: false, supports_tools: true, provider: 'Qiji' },
  { id: 'deepseek-chat', label: 'deepseek-chat', enabled_by_default: false, supports_tools: true, provider: 'Qiji' },
];

const fallbackDataSources = [
  { id: 'realtime_metrics', label: '实时数据', description: 'GMV、消耗、ROI、CTR、CVR', enabled_by_default: true },
  { id: 'trend_metrics', label: '趋势曲线', description: '消耗、GMV、ROAS 小时趋势', enabled_by_default: true },
  { id: 'campaigns', label: '投放计划', description: '计划状态、预算、出价和学习阶段', enabled_by_default: true },
  { id: 'diagnosis', label: '智能诊断', description: '异常、机会和优化建议', enabled_by_default: true },
  { id: 'product_ads', label: '商品投放', description: '商品、库存、佣金和转化表现', enabled_by_default: true },
  { id: 'creative_library', label: '素材库', description: '直播切片、短视频和疲劳度', enabled_by_default: true },
  { id: 'business_clues', label: '经营线索', description: '市场、竞品、达人和平台趋势搜索', enabled_by_default: true },
];

const projects = [
  {
    id: 'glow-beauty',
    name: 'GlowBeauty TikTok Shop',
    market: 'SEA',
    status: 'Live',
    sessions: [
      { id: 'bangkok-evening', name: '曼谷晚高峰直播间', market: 'TH', gmv: '¥48,640', status: '投放中', health: '优' },
      { id: 'jakarta-flash', name: '雅加达美妆闪购', market: 'ID', gmv: '¥31,820', status: '学习期', health: '稳' },
      { id: 'vietnam-skincare', name: '越南护肤套装专场', market: 'VN', gmv: '¥22,410', status: '待复盘', health: '险' },
    ],
  },
  {
    id: 'fashion-sea',
    name: 'SEA 女装直播矩阵',
    market: 'ID / PH',
    status: 'Planning',
    sessions: [
      { id: 'leggings-night', name: '塑形裤夜场', market: 'ID', gmv: '¥27,950', status: '投放中', health: '优' },
      { id: 'holiday-dress', name: '节日连衣裙上新', market: 'PH', gmv: '¥12,880', status: '待开播', health: '稳' },
    ],
  },
  {
    id: 'home-us',
    name: 'US Home Deals',
    market: 'US',
    status: 'Watch',
    sessions: [
      { id: 'styler-demo', name: '迷你造型器演示场', market: 'US', gmv: '¥18,220', status: '控量中', health: '险' },
    ],
  },
];

const productAds = [
  { id: 'sku-1021', product: 'Ceramide Repair Cushion', market: 'TH', spend: 2480, gmv: 13921, roas: 5.61, stock: 1280, status: '扩量' },
  { id: 'sku-1044', product: 'Vitamin C Serum Set', market: 'VN', spend: 1840, gmv: 6940, roas: 3.77, stock: 860, status: '学习' },
  { id: 'sku-1188', product: 'Mini Hair Styler', market: 'US', spend: 961, gmv: 2290, roas: 2.38, stock: 340, status: '观察' },
  { id: 'sku-1206', product: 'Sculpt Leggings', market: 'ID', spend: 1221, gmv: 7460, roas: 6.11, stock: 2140, status: '爆品' },
];

const creativeAssets = [
  { id: 'crt-2301', name: '主播试色_15s_高光片段', type: '直播切片', ctr: 4.8, cvr: 6.5, fatigue: 22, status: '可扩量', color: 'bg-blue-100 text-blue-700' },
  { id: 'crt-2317', name: '买一送一_优惠锚点_短视频', type: '短视频', ctr: 3.1, cvr: 4.0, fatigue: 48, status: '测试中', color: 'bg-emerald-100 text-emerald-700' },
  { id: 'crt-2330', name: '造型器_痛点开场_UGC', type: 'UGC', ctr: 5.6, cvr: 2.2, fatigue: 64, status: '疲劳', color: 'bg-amber-100 text-amber-700' },
  { id: 'crt-2342', name: '运动裤_腰线对比_直播切片', type: '直播切片', ctr: 6.4, cvr: 7.6, fatigue: 18, status: '爆款', color: 'bg-cyan-100 text-cyan-700' },
];

const defaultBusinessClues = [
  {
    angle: '内容趋势',
    title: 'SEA 美妆直播间短切片持续抢量',
    source: 'internal-playbook',
    evidence: '试色前后对比、限时券口播和主播近景演示更容易转化为可投素材。',
    next_action: '让 Agent 搜索当地 TikTok Shop 美妆趋势，再生成 3 条素材测试 brief。',
  },
  {
    angle: '市场机会',
    title: '印尼塑形服饰夜场有扩量窗口',
    source: 'internal-playbook',
    evidence: '晚 20:00 后女性运动/塑形品类 ROAS 高于全天均值，适合用直播切片放大。',
    next_action: '搜索竞品卖点与达人脚本，拆出新素材 hooks。',
  },
  {
    angle: '平台规则',
    title: '跨境店铺需持续关注佣金与履约变化',
    source: 'internal-playbook',
    evidence: '平台费用、达人佣金和履约体验会直接影响 CPA 与放量稳定性。',
    next_action: '搜索最近 30 天 TikTok Shop seller policy 更新。',
  },
];

const defaultTrend = [
  { time: '04:00', spend: 820, gmv: 3260, roas: 3.98 },
  { time: '06:00', spend: 1090, gmv: 5100, roas: 4.68 },
  { time: '08:00', spend: 3120, gmv: 14300, roas: 4.58 },
  { time: '10:00', spend: 3840, gmv: 17100, roas: 4.45 },
  { time: '12:00', spend: 2120, gmv: 8460, roas: 3.99 },
  { time: '14:00', spend: 2380, gmv: 9280, roas: 3.9 },
  { time: '16:00', spend: 1920, gmv: 6540, roas: 3.41 },
  { time: '18:00', spend: 2460, gmv: 11200, roas: 4.55 },
  { time: '20:00', spend: 3560, gmv: 15600, roas: 4.38 },
  { time: '22:00', spend: 4100, gmv: 17200, roas: 4.19 },
  { time: '00:00', spend: 1480, gmv: 4680, roas: 3.16 },
];

const loopSteps = [
  { id: 'observe', label: 'Observe' },
  { id: 'plan', label: 'Plan' },
  { id: 'act', label: 'Act' },
  { id: 'verify', label: 'Verify' },
];

const formatCurrency = (value) => `¥${Number(value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`;

const toolNames = {
  get_realtime_metrics: '实时数据',
  get_metrics_trend: '趋势曲线',
  get_campaigns: '投放计划',
  get_diagnosis: '智能诊断',
  get_product_ads: '商品投放',
  get_creative_library: '素材库',
  search_business_clues: '经营线索',
  create_campaign_preview: '计划预览',
};

function StatusDot({ tone = 'blue' }) {
  const color = {
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    amber: 'bg-amber-500',
    red: 'bg-rose-500',
  }[tone];
  return <span className={`h-2 w-2 rounded-full ${color}`} />;
}

function MetricTile({ icon: Icon, label, value, delta, tone = 'blue' }) {
  const toneClass = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    rose: 'bg-rose-50 text-rose-600',
  }[tone];

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${toneClass}`}>
          <Icon className="h-5 w-5" />
        </div>
        <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-600">{delta}</span>
      </div>
      <div className="mt-4 text-sm font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tracking-normal text-slate-950">{value}</div>
    </div>
  );
}

function ProjectSidebar({ selectedProjectId, selectedSessionId, onSelectProject, onSelectSession, collapsed, onToggleCollapsed }) {
  const selectedProject = projects.find((project) => project.id === selectedProjectId) || projects[0];

  if (collapsed) {
    return (
      <aside className="flex h-screen w-16 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="flex h-[73px] items-center justify-center border-b border-slate-200">
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white hover:bg-blue-700"
            aria-label="展开左侧栏"
            title="展开左侧栏"
          >
            <Sparkles className="h-5 w-5" />
          </button>
        </div>

        <div className="flex min-h-0 flex-1 flex-col items-center gap-2 overflow-y-auto py-4">
          {projects.map((project) => {
            const active = project.id === selectedProjectId;
            return (
              <button
                key={project.id}
                type="button"
                title={project.name}
                onClick={() => {
                  onSelectProject(project.id);
                  onSelectSession(project.sessions[0]?.id);
                }}
                className={`flex h-10 w-10 items-center justify-center rounded-lg transition ${
                  active ? 'bg-slate-950 text-white' : 'text-slate-500 hover:bg-slate-100'
                }`}
              >
                <FolderKanban className="h-5 w-5" />
              </button>
            );
          })}

          <div className="my-2 h-px w-8 bg-slate-200" />

          {selectedProject.sessions.map((session) => {
            const active = session.id === selectedSessionId;
            const tone = session.health === '优' ? 'green' : session.health === '险' ? 'red' : 'amber';
            return (
              <button
                key={session.id}
                type="button"
                title={session.name}
                onClick={() => onSelectSession(session.id)}
                className={`flex h-10 w-10 items-center justify-center rounded-lg border transition ${
                  active ? 'border-blue-300 bg-blue-50' : 'border-transparent hover:bg-slate-100'
                }`}
              >
                <StatusDot tone={tone} />
              </button>
            );
          })}
        </div>

        <div className="flex h-[65px] items-center justify-center border-t border-slate-200">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">A</div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex h-screen w-72 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-base font-semibold text-slate-950">MaiStream</div>
            <div className="text-xs font-medium text-slate-500">Agent Loop</div>
          </div>
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100"
            aria-label="收起左侧栏"
            title="收起左侧栏"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-4">
        <div className="mb-2 flex items-center justify-between px-2">
          <span className="text-xs font-semibold uppercase tracking-normal text-slate-400">Projects</span>
          <button className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" aria-label="新建项目">
            <Plus className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-1">
          {projects.map((project) => {
            const active = project.id === selectedProjectId;
            return (
              <button
                key={project.id}
                onClick={() => {
                  onSelectProject(project.id);
                  onSelectSession(project.sessions[0]?.id);
                }}
                className={`w-full rounded-lg px-3 py-3 text-left transition ${
                  active ? 'bg-slate-950 text-white' : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-2">
                  <FolderKanban className="h-4 w-4" />
                  <span className="min-w-0 flex-1 truncate text-sm font-semibold">{project.name}</span>
                </div>
                <div className={`mt-1 flex items-center gap-2 text-xs ${active ? 'text-slate-300' : 'text-slate-500'}`}>
                  <span>{project.market}</span>
                  <span className="h-1 w-1 rounded-full bg-current" />
                  <span>{project.status}</span>
                </div>
              </button>
            );
          })}
        </div>

        <div className="mb-2 mt-6 flex items-center justify-between px-2">
          <span className="text-xs font-semibold uppercase tracking-normal text-slate-400">Sessions</span>
          <Radio className="h-4 w-4 text-slate-400" />
        </div>

        <div className="space-y-2">
          {selectedProject.sessions.map((session) => {
            const active = session.id === selectedSessionId;
            const tone = session.health === '优' ? 'green' : session.health === '险' ? 'red' : 'amber';
            return (
              <button
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`w-full rounded-lg border px-3 py-3 text-left transition ${
                  active ? 'border-blue-300 bg-blue-50' : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex items-start gap-2">
                  <StatusDot tone={tone} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold text-slate-950">{session.name}</div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                      <span>{session.market}</span>
                      <span>{session.status}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs">
                  <span className="text-slate-500">GMV</span>
                  <span className="font-semibold text-slate-900">{session.gmv}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="border-t border-slate-200 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">A</div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-slate-900">MCN A</div>
            <div className="truncate text-xs text-slate-500">直播运营</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function AccessMenu({ dataSources, enabledDataSources, onToggleSource, open, onToggleOpen }) {
  const allEnabled = enabledDataSources.length === dataSources.length;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggleOpen}
        className="flex h-9 items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-3 text-sm font-semibold text-orange-700 hover:bg-orange-100"
      >
        <ShieldCheck className="h-4 w-4" />
        <span>{allEnabled ? '完全访问' : `已选 ${enabledDataSources.length}`}</span>
        <ChevronDown className="h-4 w-4" />
      </button>

      {open && (
        <div className="absolute bottom-11 left-0 z-30 w-80 rounded-lg border border-slate-200 bg-white p-2 shadow-xl">
          <div className="px-2 py-2 text-xs font-semibold uppercase tracking-normal text-slate-400">Data Access</div>
          <div className="max-h-72 overflow-y-auto">
            {dataSources.map((source) => {
              const checked = enabledDataSources.includes(source.id);
              return (
                <label key={source.id} className="flex cursor-pointer gap-3 rounded-lg px-2 py-2 hover:bg-slate-50">
                  <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border ${checked ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-300'}`}>
                    {checked && <Check className="h-3.5 w-3.5" />}
                  </span>
                  <input className="sr-only" type="checkbox" checked={checked} onChange={() => onToggleSource(source.id)} />
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold text-slate-900">{source.label}</span>
                    <span className="block text-xs leading-5 text-slate-500">{source.description}</span>
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function ModelMenu({ models, selectedModels, onToggleModel, open, onToggleOpen }) {
  const primary = selectedModels[0] || 'gpt-5';
  const label = selectedModels.length > 1 ? `${primary} +${selectedModels.length - 1}` : primary;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggleOpen}
        className="flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        <Circle className="h-4 w-4 text-slate-400" />
        <Zap className="h-4 w-4 text-slate-500" />
        <span>{label}</span>
        <ChevronDown className="h-4 w-4" />
      </button>

      {open && (
        <div className="absolute bottom-11 right-0 z-30 w-72 rounded-lg border border-slate-200 bg-white p-2 shadow-xl">
          <div className="px-2 py-2 text-xs font-semibold uppercase tracking-normal text-slate-400">Models</div>
          <div className="max-h-72 overflow-y-auto">
            {models.map((model) => {
              const checked = selectedModels.includes(model.id);
              return (
                <label key={model.id} className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-2 hover:bg-slate-50">
                  <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border ${checked ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-300'}`}>
                    {checked && <Check className="h-3.5 w-3.5" />}
                  </span>
                  <input className="sr-only" type="checkbox" checked={checked} onChange={() => onToggleModel(model.id)} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-semibold text-slate-900">{model.label || model.id}</span>
                    <span className="block text-xs text-slate-500">{model.provider || 'Qiji'}{model.enabled_by_default ? ' · 默认' : ''}</span>
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function AgentMessage({ message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-white">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div className={`max-w-[76%] rounded-lg px-4 py-3 text-sm leading-6 ${isUser ? 'bg-blue-600 text-white' : 'border border-slate-200 bg-white text-slate-800'}`}>
        <div className="whitespace-pre-wrap">{message.content}</div>
        {message.streaming && (
          <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>streaming</span>
          </div>
        )}
      </div>
      {isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}

function ToolTimeline({ events, activeStage }) {
  return (
    <div className="border-b border-slate-200 bg-white px-5 py-3">
      <div className="flex items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-2">
          {loopSteps.map((step, index) => {
            const currentIndex = loopSteps.findIndex((item) => item.id === activeStage);
            const active = index <= currentIndex;
            return (
              <div key={step.id} className="flex items-center gap-2">
                <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${active ? 'bg-slate-950 text-white' : 'bg-slate-100 text-slate-400'}`}>
                  {active ? <Check className="h-3.5 w-3.5" /> : index + 1}
                </span>
                <span className={`text-xs font-semibold ${active ? 'text-slate-950' : 'text-slate-400'}`}>{step.label}</span>
                {index < loopSteps.length - 1 && <span className="h-px w-6 bg-slate-200" />}
              </div>
            );
          })}
        </div>
        <div className="hidden min-w-0 items-center gap-2 text-xs text-slate-500 lg:flex">
          <Activity className="h-4 w-4" />
          <span className="truncate">{events[0] ? `${toolNames[events[0].tool] || events[0].tool} · ${events[0].type === 'tool_call' ? '调用中' : '已返回'}` : 'ready'}</span>
        </div>
      </div>
    </div>
  );
}

function PendingAction({ preview, onConfirm, onDismiss }) {
  if (!preview) return null;

  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-blue-900">
          <Target className="h-4 w-4" />
          <span>待确认计划</span>
        </div>
        <button type="button" onClick={onDismiss} className="text-xs font-semibold text-blue-600 hover:text-blue-800">忽略</button>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-xs text-blue-500">名称</div>
          <div className="font-semibold text-slate-950">{preview.name}</div>
        </div>
        <div>
          <div className="text-xs text-blue-500">预算</div>
          <div className="font-semibold text-slate-950">{formatCurrency(preview.budget)}</div>
        </div>
        <div>
          <div className="text-xs text-blue-500">目标出价</div>
          <div className="font-semibold text-slate-950">{formatCurrency(preview.bid)}</div>
        </div>
        <div>
          <div className="text-xs text-blue-500">方式</div>
          <div className="font-semibold text-slate-950">{preview.bid_type}</div>
        </div>
      </div>
      <button type="button" onClick={onConfirm} className="mt-4 flex h-9 w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white hover:bg-blue-700">
        <CheckCircle2 className="h-4 w-4" />
        确认创建
      </button>
    </div>
  );
}

function ContextPanel({ metrics, trendData, campaigns, contextMode, setContextMode, latestToolResult, toolEvents, selectedSession, collapsed, onToggleCollapsed }) {
  const toolData = latestToolResult?.result?.data;
  const hasCampaignTool = latestToolResult?.tool === 'get_campaigns' && Array.isArray(toolData);
  const hasCreativeTool = latestToolResult?.tool === 'get_creative_library' && Array.isArray(toolData);
  const hasProductTool = latestToolResult?.tool === 'get_product_ads' && Array.isArray(toolData);
  const hasTrendTool = latestToolResult?.tool === 'get_metrics_trend' && Array.isArray(toolData);
  const hasBusinessCluesTool = latestToolResult?.tool === 'search_business_clues' && Array.isArray(toolData?.clues);
  const visibleProducts = hasProductTool ? toolData : productAds;
  const visibleCreatives = hasCreativeTool ? toolData : creativeAssets;
  const visibleTrend = hasTrendTool ? toolData : trendData;
  const visibleCampaigns = hasCampaignTool ? toolData : campaigns;
  const visibleClues = hasBusinessCluesTool ? toolData.clues : defaultBusinessClues;
  const contextTabs = [
    { id: 'live', label: '实时', icon: BarChart3 },
    { id: 'products', label: '商品', icon: ShoppingBag },
    { id: 'creatives', label: '素材', icon: Film },
    { id: 'clues', label: '线索', icon: Compass },
    { id: 'tools', label: '工具', icon: Database },
  ];

  if (collapsed) {
    return (
      <aside className="flex h-screen w-16 shrink-0 flex-col items-center border-l border-slate-200 bg-white py-4">
        <button
          type="button"
          onClick={onToggleCollapsed}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
          aria-label="展开右侧栏"
          title="展开右侧栏"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <div className="mt-5 flex flex-col gap-2">
          {contextTabs.map((item) => (
            <button
              key={item.id}
              type="button"
              title={item.label}
              onClick={() => setContextMode(item.id)}
              className={`flex h-10 w-10 items-center justify-center rounded-lg transition ${
                contextMode === item.id ? 'bg-slate-950 text-white' : 'text-slate-500 hover:bg-slate-100'
              }`}
            >
              <item.icon className="h-4 w-4" />
            </button>
          ))}
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex h-screen w-[420px] shrink-0 flex-col border-l border-slate-200 bg-slate-50">
      <div className="border-b border-slate-200 bg-white px-5 py-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-base font-semibold text-slate-950">Context</div>
            <div className="mt-1 text-xs text-slate-500">{selectedSession?.name || '直播间'}</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onToggleCollapsed}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              aria-label="收起右侧栏"
              title="收起右侧栏"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
            <button className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50" aria-label="刷新上下文">
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-5 gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1">
          {contextTabs.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setContextMode(item.id)}
              className={`flex h-8 items-center justify-center gap-1 rounded-lg text-xs font-semibold ${
                contextMode === item.id ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <item.icon className="h-3.5 w-3.5" />
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {contextMode === 'live' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <MetricTile icon={DollarIcon} label="消耗" value={formatCurrency(metrics?.total_spend || 12062)} delta="+12.5%" tone="blue" />
              <MetricTile icon={ShoppingBag} label="GMV" value={formatCurrency(metrics?.total_gmv || 48640)} delta="+24.2%" tone="green" />
              <MetricTile icon={TrendingUp} label="ROI" value={(metrics?.roi || 4.07).toFixed(2)} delta="-1.2%" tone="amber" />
              <MetricTile icon={Activity} label="CTR" value={`${(metrics?.ctr || 2.98).toFixed(2)}%`} delta="+0.4%" tone="green" />
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-4 flex items-center justify-between">
                <div className="text-sm font-semibold text-slate-950">消耗与 GMV</div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-blue-500" />消耗</span>
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-violet-500" />GMV</span>
                </div>
              </div>
              <div className="h-56 overflow-hidden">
                <AreaChart width={340} height={224} data={visibleTrend} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
                  <defs>
                    <linearGradient id="agentSpend" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.16} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="agentGmv" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.16} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={44} />
                  <Tooltip />
                  <Area type="monotone" dataKey="gmv" stroke="#8b5cf6" strokeWidth={2.5} fill="url(#agentGmv)" />
                  <Area type="monotone" dataKey="spend" stroke="#3b82f6" strokeWidth={2.5} fill="url(#agentSpend)" />
                </AreaChart>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
                <div className="text-sm font-semibold text-slate-950">在投计划</div>
                <Eye className="h-4 w-4 text-slate-400" />
              </div>
              <div className="divide-y divide-slate-100">
                {visibleCampaigns.slice(0, 4).map((campaign) => (
                  <div key={campaign.id} className="grid grid-cols-[1fr_auto] gap-3 px-4 py-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold text-blue-600">{campaign.name}</div>
                      <div className="mt-1 text-xs text-slate-500">ROI {campaign.roi} · CTR {campaign.ctr}%</div>
                    </div>
                    <div className="text-right text-sm font-semibold text-slate-900">{formatCurrency(campaign.spend)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {contextMode === 'products' && (
          <div className="space-y-3">
            {visibleProducts.map((product) => (
              <div key={product.id} className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex gap-3">
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                    <Boxes className="h-6 w-6" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold text-slate-950">{product.product}</div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                      <span>{product.market}</span>
                      <span>库存 {product.stock}</span>
                      <span>{product.status}</span>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                      <div><span className="block text-slate-400">消耗</span><span className="font-semibold text-slate-900">{formatCurrency(product.spend)}</span></div>
                      <div><span className="block text-slate-400">GMV</span><span className="font-semibold text-slate-900">{formatCurrency(product.gmv)}</span></div>
                      <div><span className="block text-slate-400">ROAS</span><span className="font-semibold text-emerald-600">{product.roas}</span></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {contextMode === 'creatives' && (
          <div className="space-y-3">
            {visibleCreatives.map((asset) => (
              <div key={asset.id} className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex gap-3">
                  <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-lg ${asset.color || 'bg-slate-100 text-slate-600'}`}>
                    <ImageIcon className="h-6 w-6" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold text-slate-950">{asset.name}</div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                      <span>{asset.type}</span>
                      <span>{asset.status}</span>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                      <div><span className="block text-slate-400">CTR</span><span className="font-semibold text-slate-900">{asset.ctr}%</span></div>
                      <div><span className="block text-slate-400">CVR</span><span className="font-semibold text-slate-900">{asset.cvr}%</span></div>
                      <div><span className="block text-slate-400">疲劳</span><span className="font-semibold text-amber-600">{asset.fatigue}%</span></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {contextMode === 'clues' && (
          <div className="space-y-3">
            {hasBusinessCluesTool && (
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <div className="text-xs font-semibold uppercase tracking-normal text-blue-500">Search Query</div>
                <div className="mt-1 text-sm font-semibold text-blue-950">{toolData.query}</div>
              </div>
            )}
            {visibleClues.map((clue, index) => (
              <div key={`${clue.title}-${index}`} className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-blue-600">{clue.angle}</div>
                    <div className="mt-1 text-sm font-semibold leading-5 text-slate-950">{clue.title}</div>
                  </div>
                  {clue.url && (
                    <a href={clue.url} target="_blank" rel="noreferrer" className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50" aria-label="打开线索来源">
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                </div>
                <div className="mt-2 text-xs text-slate-500">{clue.source}</div>
                <p className="mt-3 text-sm leading-6 text-slate-700">{clue.evidence}</p>
                <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-600">{clue.next_action}</div>
              </div>
            ))}
          </div>
        )}

        {contextMode === 'tools' && (
          <div className="space-y-3">
            {toolEvents.length === 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-500">暂无工具调用</div>
            )}
            {toolEvents.map((event) => (
              <div key={event.id} className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                    {event.type === 'tool_call' ? <Loader2 className="h-4 w-4 animate-spin text-blue-600" /> : <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
                    <span>{toolNames[event.tool] || event.tool}</span>
                  </div>
                  <span className="text-xs text-slate-400">{event.time}</span>
                </div>
                <pre className="mt-3 max-h-36 overflow-auto rounded-lg bg-slate-950 p-3 text-xs leading-5 text-slate-100">
                  {JSON.stringify(event.type === 'tool_call' ? event.arguments : event.result, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function DollarIcon(props) {
  return <span className="text-xl font-semibold leading-none" {...props}>$</span>;
}

export default function AgentLoopPage() {
  const [selectedProjectId, setSelectedProjectId] = useState(projects[0].id);
  const [selectedSessionId, setSelectedSessionId] = useState(projects[0].sessions[0].id);
  const [models, setModels] = useState(fallbackModels);
  const [selectedModels, setSelectedModels] = useState(['gpt-5']);
  const [dataSources, setDataSources] = useState(fallbackDataSources);
  const [enabledDataSources, setEnabledDataSources] = useState(fallbackDataSources.map((source) => source.id));
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: '你好，我是智投星。可以直接问我当前直播间投放表现、问题诊断、商品扩量策略，或让我生成一个待确认的计划。',
    },
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [accessOpen, setAccessOpen] = useState(false);
  const [modelOpen, setModelOpen] = useState(false);
  const [toolEvents, setToolEvents] = useState([]);
  const [latestToolResult, setLatestToolResult] = useState(null);
  const [pendingAction, setPendingAction] = useState(null);
  const [contextMode, setContextMode] = useState('live');
  const [metrics, setMetrics] = useState(null);
  const [trendData, setTrendData] = useState(defaultTrend);
  const [campaigns, setCampaigns] = useState([]);
  const [activeStage, setActiveStage] = useState('observe');
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) || projects[0];
  const selectedSession = selectedProject.sessions.find((session) => session.id === selectedSessionId) || selectedProject.sessions[0];

  useEffect(() => {
    async function loadAgentConfig() {
      try {
        const [modelsResponse, dataSourcesResponse] = await Promise.all([
          api.getAgentModels(),
          api.getAgentDataSources(),
        ]);

        const nextModels = modelsResponse.models?.length ? modelsResponse.models : fallbackModels;
        const nextSources = dataSourcesResponse.data_sources?.length ? dataSourcesResponse.data_sources : fallbackDataSources;

        setModels(nextModels);
        setSelectedModels(nextModels.filter((model) => model.enabled_by_default).map((model) => model.id));
        setDataSources(nextSources);
        setEnabledDataSources(dataSourcesResponse.default_enabled || nextSources.filter((source) => source.enabled_by_default).map((source) => source.id));
      } catch (error) {
        setModels(fallbackModels);
        setDataSources(fallbackDataSources);
      }
    }

    async function loadLiveData() {
      try {
        const [metricsResponse, trendResponse, campaignResponse] = await Promise.all([
          api.getRealtimeMetrics(),
          api.getMetricsTrend(24),
          api.getCampaigns(),
        ]);
        setMetrics(metricsResponse);
        setTrendData(trendResponse);
        setCampaigns(campaignResponse);
      } catch (error) {
        setTrendData(defaultTrend);
      }
    }

    loadAgentConfig();
    loadLiveData();
  }, []);

  const visibleMessages = useMemo(() => messages.slice(-12), [messages]);

  const toggleDataSource = (sourceId) => {
    setEnabledDataSources((current) => (
      current.includes(sourceId)
        ? current.filter((id) => id !== sourceId)
        : [...current, sourceId]
    ));
  };

  const toggleModel = (modelId) => {
    setSelectedModels((current) => (
      current.includes(modelId)
        ? current.filter((id) => id !== modelId)
        : [...current, modelId]
    ));
  };

  const confirmPendingAction = async () => {
    if (!pendingAction) return;
    try {
      await api.createCampaign({
        name: pendingAction.name,
        budget: pendingAction.budget,
        bid: pendingAction.bid,
        target_type: pendingAction.target_type,
        bid_type: pendingAction.bid_type,
      });
      setMessages((current) => [
        ...current,
        {
          id: `confirm-${Date.now()}`,
          role: 'assistant',
          content: `已创建计划「${pendingAction.name}」，预算 ${formatCurrency(pendingAction.budget)}，目标出价 ${formatCurrency(pendingAction.bid)}。`,
        },
      ]);
      setPendingAction(null);
      const campaignResponse = await api.getCampaigns();
      setCampaigns(campaignResponse);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `confirm-error-${Date.now()}`,
          role: 'assistant',
          content: `创建失败：${error.message}`,
        },
      ]);
    }
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    const userMessage = { id: `user-${Date.now()}`, role: 'user', content: text };
    const assistantId = `assistant-${Date.now()}`;
    const nextMessages = [...messages, userMessage];
    const apiMessages = nextMessages
      .filter((message) => ['user', 'assistant'].includes(message.role))
      .slice(-10)
      .map((message) => ({ role: message.role, content: message.content }));

    setInput('');
    setIsStreaming(true);
    setAccessOpen(false);
    setModelOpen(false);
    setActiveStage('plan');
    setToolEvents([]);
    setMessages([...nextMessages, { id: assistantId, role: 'assistant', content: '', streaming: true }]);

    await api.chatWithAgent(
      apiMessages,
      {
        onModel: () => setActiveStage('plan'),
        onToolCall: (tool, argumentsPayload) => {
          setActiveStage('act');
          setToolEvents((current) => [
            {
              id: `call-${Date.now()}-${tool}`,
              type: 'tool_call',
              tool,
              arguments: argumentsPayload,
              time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
            },
            ...current,
          ]);
        },
        onToolResult: (tool, result) => {
          setActiveStage('verify');
          const event = {
            id: `result-${Date.now()}-${tool}`,
            type: 'tool_result',
            tool,
            result,
            time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          };
          setToolEvents((current) => [event, ...current]);
          setLatestToolResult(event);
          if (tool === 'get_product_ads') setContextMode('products');
          if (tool === 'get_creative_library') setContextMode('creatives');
          if (tool === 'search_business_clues') setContextMode('clues');
          if (['get_metrics_trend', 'get_realtime_metrics', 'get_campaigns'].includes(tool)) setContextMode('live');
          if (result?.type === 'campaign_preview' && result?.data) {
            setPendingAction(result.data);
          }
        },
        onMessage: (chunk) => {
          setMessages((current) => current.map((message) => (
            message.id === assistantId
              ? { ...message, content: `${message.content}${chunk}` }
              : message
          )));
        },
        onError: (error) => {
          setMessages((current) => current.map((message) => (
            message.id === assistantId
              ? { ...message, content: message.content ? `${message.content}\n\n${error}` : error, streaming: false }
              : message
          )));
          setIsStreaming(false);
          setActiveStage('observe');
        },
        onDone: () => {
          setMessages((current) => current.map((message) => (
            message.id === assistantId ? { ...message, streaming: false } : message
          )));
          setIsStreaming(false);
          setActiveStage('observe');
        },
      },
      {
        model: selectedModels[0] || 'gpt-5',
        models: selectedModels.length ? selectedModels : ['gpt-5'],
        enabledDataSources,
      },
    );
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100 text-slate-950">
      <ProjectSidebar
        selectedProjectId={selectedProjectId}
        selectedSessionId={selectedSessionId}
        onSelectProject={setSelectedProjectId}
        onSelectSession={setSelectedSessionId}
        collapsed={leftCollapsed}
        onToggleCollapsed={() => setLeftCollapsed((current) => !current)}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-[73px] shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <h1 className="truncate text-lg font-semibold text-slate-950">直播后台管理</h1>
              <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                <StatusDot tone="green" />
                在线
              </span>
            </div>
            <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
              <span>{selectedProject.name}</span>
              <span className="h-1 w-1 rounded-full bg-slate-300" />
              <span>{selectedSession?.name}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50" aria-label="搜索">
              <Search className="h-4 w-4" />
            </button>
            <button className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50" aria-label="设置">
              <SlidersHorizontal className="h-4 w-4" />
            </button>
          </div>
        </header>

        <ToolTimeline events={toolEvents} activeStage={activeStage} />

        <section className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
          <div className="mx-auto flex max-w-4xl flex-col gap-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="grid grid-cols-4 gap-3">
                <div className="rounded-lg bg-slate-50 p-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500"><Clock3 className="h-3.5 w-3.5" />当前场次</div>
                  <div className="mt-2 truncate text-sm font-semibold text-slate-950">{selectedSession?.name}</div>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500"><BarChart3 className="h-3.5 w-3.5" />ROI</div>
                  <div className="mt-2 text-sm font-semibold text-emerald-600">{(metrics?.roi || 4.07).toFixed(2)}</div>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500"><ShoppingBag className="h-3.5 w-3.5" />GMV</div>
                  <div className="mt-2 text-sm font-semibold text-slate-950">{formatCurrency(metrics?.total_gmv || 48640)}</div>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500"><AlertTriangle className="h-3.5 w-3.5" />待处理</div>
                  <div className="mt-2 text-sm font-semibold text-amber-600">3 项</div>
                </div>
              </div>
            </div>

            <PendingAction preview={pendingAction} onConfirm={confirmPendingAction} onDismiss={() => setPendingAction(null)} />

            <div className="space-y-4">
              {visibleMessages.map((message) => (
                <AgentMessage key={message.id} message={message} />
              ))}
            </div>
          </div>
        </section>

        <div className="shrink-0 border-t border-slate-200 bg-white px-6 py-4">
          <div className="mx-auto max-w-4xl rounded-lg border border-slate-200 bg-white shadow-sm">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
              className="h-20 w-full resize-none rounded-lg border-0 px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
              placeholder="询问直播间投放表现、诊断问题，或创建一个待确认计划"
            />
            <div className="flex items-center justify-between border-t border-slate-100 px-3 py-2">
              <div className="flex items-center gap-2">
                <button type="button" className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" aria-label="添加">
                  <Plus className="h-5 w-5" />
                </button>
                <AccessMenu
                  dataSources={dataSources}
                  enabledDataSources={enabledDataSources}
                  onToggleSource={toggleDataSource}
                  open={accessOpen}
                  onToggleOpen={() => {
                    setAccessOpen((current) => !current);
                    setModelOpen(false);
                  }}
                />
              </div>

              <div className="flex items-center gap-2">
                <ModelMenu
                  models={models}
                  selectedModels={selectedModels}
                  onToggleModel={toggleModel}
                  open={modelOpen}
                  onToggleOpen={() => {
                    setModelOpen((current) => !current);
                    setAccessOpen(false);
                  }}
                />
                <button type="button" className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" aria-label="语音">
                  <Mic className="h-4 w-4" />
                </button>
                <button type="button" className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" aria-label="附件">
                  <Paperclip className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={sendMessage}
                  disabled={isStreaming || !input.trim()}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-950 text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                  aria-label="发送"
                >
                  {isStreaming ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowUp className="h-5 w-5" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      <ContextPanel
        metrics={metrics}
        trendData={trendData}
        campaigns={campaigns}
        contextMode={contextMode}
        setContextMode={setContextMode}
        latestToolResult={latestToolResult}
        toolEvents={toolEvents}
        selectedSession={selectedSession}
        collapsed={rightCollapsed}
        onToggleCollapsed={() => setRightCollapsed((current) => !current)}
      />
    </div>
  );
}
