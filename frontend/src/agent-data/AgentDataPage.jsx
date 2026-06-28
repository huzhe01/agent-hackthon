import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Cloud,
  Database,
  FileText,
  Gauge,
  GitBranch,
  Globe2,
  Layers3,
  LineChart,
  LockKeyhole,
  RadioTower,
  RefreshCw,
  Search,
  ServerCog,
  ShieldCheck,
  Sigma,
  SlidersHorizontal,
  Sparkles,
  Store,
  TrendingUp,
  Wallet,
  Zap,
} from 'lucide-react';

const pipelineSteps = [
  {
    id: 'auth',
    title: '授权接入',
    subtitle: 'OAuth / API Key / 店铺授权',
    detail: '客户授权媒体 API、店铺 API 和内部经营系统，权限只读优先。',
    icon: LockKeyhole,
    color: '#7c3aed',
  },
  {
    id: 'ingest',
    title: '数据流入',
    subtitle: '定时拉取 + Webhook',
    detail: '拉取消耗、曝光、点击、订单、库存、评论、素材和线索。',
    icon: Cloud,
    color: '#0ea5e9',
  },
  {
    id: 'normalize',
    title: '标准化',
    subtitle: '字段映射 / 口径统一',
    detail: '把不同平台字段统一成 spend、gmv、roi、sku、channel 等核心对象。',
    icon: Database,
    color: '#10b981',
  },
  {
    id: 'features',
    title: '特征计算',
    subtitle: '实时窗口 / 历史基线',
    detail: '计算渠道效率、SKU 弹性、人群质量、库存风险和直播阶段特征。',
    icon: Sigma,
    color: '#f59e0b',
  },
  {
    id: 'model',
    title: '模型预估',
    subtitle: 'ROI / GMV / CPA / 库存',
    detail: '模型预估不同预算分配下的收益、风险、库存消耗和置信度。',
    icon: BrainCircuit,
    color: '#8b5cf6',
  },
  {
    id: 'agent',
    title: 'Agent 编排',
    subtitle: '策略生成 / 护栏校验',
    detail: 'Analysis、Planning、Orchestrator、Delivery 协同生成可执行计划。',
    icon: Bot,
    color: '#2563eb',
  },
  {
    id: 'writeback',
    title: '执行回写',
    subtitle: '审批 / 投放 / 复盘',
    detail: '写回预算动作、审批记录、效果验证和下一场策略记忆。',
    icon: GitBranch,
    color: '#059669',
  },
];

const dataSources = [
  {
    title: '媒体 API',
    status: '可授权接入',
    icon: RadioTower,
    description: 'TikTok Ads、Meta、Amazon Ads、巨量、聚光等投放平台。',
    fields: ['spend', 'impressions', 'clicks', 'campaign', 'audience'],
    accent: 'bg-blue-50 text-blue-700 border-blue-100',
  },
  {
    title: '客户授权 API',
    status: '客户侧授权',
    icon: Store,
    description: 'Shopify、TikTok Shop、Shopee、Lazada、ERP、库存系统。',
    fields: ['orders', 'gmv', 'sku', 'inventory', 'margin'],
    accent: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  },
  {
    title: '外部知识',
    status: '可搜索补充',
    icon: Search,
    description: '新闻、趋势、竞品、达人内容和历史生意线索。',
    fields: ['trend', 'competitor', 'news', 'category', 'memory'],
    accent: 'bg-amber-50 text-amber-700 border-amber-100',
  },
  {
    title: '模拟器兜底',
    status: 'Demo / 冷启动',
    icon: SlidersHorizontal,
    description: '没有真实授权时，按预算、渠道、SKU、库存关系生成可解释轨迹。',
    fields: ['budget_pool', 'sku_ads', 'events', 'alerts', 'review'],
    accent: 'bg-violet-50 text-violet-700 border-violet-100',
  },
];

const modelCards = [
  {
    title: '流量预估模型',
    value: '1.28M',
    unit: '预测曝光',
    change: '+18%',
    detail: '结合渠道历史 CTR、直播时段、素材质量和市场热度。',
    icon: LineChart,
  },
  {
    title: '转化率预估',
    value: '3.7%',
    unit: 'CVR',
    change: '+0.6pp',
    detail: '按 SKU 价格带、库存、评论意向和直播间承接能力校准。',
    icon: Gauge,
  },
  {
    title: '预算分配模型',
    value: '42%',
    unit: 'TikTok 推荐占比',
    change: '线性规划',
    detail: '在预算、渠道上限、ROI 预估和库存约束下求解。',
    icon: Wallet,
  },
  {
    title: '经营结果预估',
    value: '4.8',
    unit: '预计 ROAS',
    change: '高置信',
    detail: '输出 GMV、Spend、毛利润、CPA、库存消耗和风险区间。',
    icon: TrendingUp,
  },
];

const agentLoops = [
  { name: 'Analysis Agent', role: '识别变化并归因', status: '读取实时窗口', icon: Activity },
  { name: 'Planning Agent', role: '生成预算与人群策略', status: '产出方案', icon: BrainCircuit },
  { name: 'Orchestrator', role: '校验目标与护栏', status: '检查权限', icon: ShieldCheck },
  { name: 'Delivery Agent', role: '执行或等待审批', status: '写回动作', icon: Zap },
  { name: 'Review Agent', role: '验证效果与沉淀记忆', status: '生成复盘', icon: FileText },
];

const eventTemplates = [
  '媒体 API 返回 15 分钟窗口消耗与点击数据',
  '客户授权 API 同步 5 个 SKU 的订单、库存和毛利',
  '标准化层完成 TikTok / Meta / Shopee 字段映射',
  '特征层生成渠道 ROI、SKU 弹性和高意向线索分',
  '模型预估预算分配：TikTok 42%，Meta 33%，Shopee 25%',
  'Agent 编排生成投中策略，并写入审批与复盘事件',
];

function cx(...classes) {
  return classes.filter(Boolean).join(' ');
}

function FlowPacket({ delay = '0s', color = '#7c3aed', path = 'primary' }) {
  const animationName = path === 'lower' ? 'agent-data-flow-lower' : 'agent-data-flow-primary';
  return (
    <span
      className="pointer-events-none absolute h-2.5 w-2.5 rounded-full shadow-[0_0_18px_currentColor]"
      style={{
        color,
        backgroundColor: color,
        animation: `${animationName} 6.5s linear infinite`,
        animationDelay: delay,
      }}
    />
  );
}

function StageBadge({ step, active }) {
  const Icon = step.icon;
  return (
    <div
      className={cx(
        'min-w-[150px] rounded-lg border px-3 py-2 transition-all',
        active
          ? 'border-violet-200 bg-violet-50 shadow-sm'
          : 'border-slate-200 bg-white',
      )}
    >
      <div className="flex items-center gap-2">
        <span
          className="flex h-7 w-7 items-center justify-center rounded-lg text-white"
          style={{ backgroundColor: step.color }}
        >
          <Icon className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-slate-900">{step.title}</div>
          <div className="truncate text-[11px] text-slate-500">{step.subtitle}</div>
        </div>
      </div>
    </div>
  );
}

function SourceCard({ source, active }) {
  const Icon = source.icon;
  return (
    <div className={cx('rounded-lg border bg-white p-4 shadow-sm transition-all', active ? 'border-violet-200 shadow-md' : 'border-slate-200')}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100">
            <Icon className="h-5 w-5 text-slate-700" />
          </div>
          <div>
            <div className="font-semibold text-slate-950">{source.title}</div>
            <div className={cx('mt-1 inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold', source.accent)}>
              {source.status}
            </div>
          </div>
        </div>
        {active && <RefreshCw className="h-4 w-4 animate-spin text-violet-500" />}
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{source.description}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {source.fields.map((field) => (
          <span key={field} className="rounded-md bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-600">
            {field}
          </span>
        ))}
      </div>
    </div>
  );
}

function MetricFormula({ label, formula, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="text-xs font-semibold text-slate-500">{label}</div>
      <div className="mt-2 font-mono text-sm font-semibold text-slate-950">{formula}</div>
      <div className="mt-2 text-xs text-emerald-600">{value}</div>
    </div>
  );
}

function ModelCard({ card, active }) {
  const Icon = card.icon;
  return (
    <div className={cx('rounded-lg border bg-white p-4 shadow-sm transition-all', active ? 'border-violet-300 ring-2 ring-violet-100' : 'border-slate-200')}>
      <div className="flex items-start justify-between">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50">
          <Icon className="h-5 w-5 text-violet-600" />
        </div>
        <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">{card.change}</span>
      </div>
      <div className="mt-4 text-sm font-medium text-slate-500">{card.title}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-3xl font-bold text-slate-950">{card.value}</span>
        <span className="text-sm font-semibold text-slate-500">{card.unit}</span>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500">{card.detail}</p>
    </div>
  );
}

function AgentCard({ agent, active }) {
  const Icon = agent.icon;
  return (
    <div className={cx('rounded-lg border p-3 transition-all', active ? 'border-blue-200 bg-blue-50' : 'border-slate-200 bg-white')}>
      <div className="flex items-center gap-2">
        <div className={cx('flex h-8 w-8 items-center justify-center rounded-lg', active ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600')}>
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-slate-900">{agent.name}</div>
          <div className="truncate text-xs text-slate-500">{agent.role}</div>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2 text-xs">
        <span className={cx('h-2 w-2 rounded-full', active ? 'animate-pulse bg-blue-500' : 'bg-slate-300')} />
        <span className={active ? 'font-semibold text-blue-700' : 'text-slate-500'}>{active ? agent.status : '等待上游数据'}</span>
      </div>
    </div>
  );
}

function DataFlowMap({ activeStep }) {
  return (
    <div className="relative overflow-hidden rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-base font-semibold text-slate-950">
            <GitBranch className="h-5 w-5 text-violet-600" />
            数据流入与模型预估链路
          </div>
          <p className="mt-1 text-sm text-slate-500">媒体、店铺、客户系统与模拟器进入同一数据契约，再交给模型和 Agent 使用。</p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          当前步骤：{pipelineSteps[activeStep].title}
        </span>
      </div>

      <div className="relative h-[360px] rounded-lg bg-gradient-to-br from-slate-50 to-white">
        <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1000 360" role="img" aria-label="agent data flow diagram">
          <defs>
            <linearGradient id="flowGradient" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0%" stopColor="#7c3aed" />
              <stop offset="45%" stopColor="#0ea5e9" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>
          </defs>
          <path d="M70 90 C190 90 180 180 300 180 L700 180 C820 180 810 90 930 90" fill="none" stroke="#dbeafe" strokeWidth="18" strokeLinecap="round" />
          <path d="M70 270 C190 270 180 180 300 180" fill="none" stroke="#ede9fe" strokeWidth="18" strokeLinecap="round" />
          <path d="M300 180 L700 180" fill="none" stroke="url(#flowGradient)" strokeWidth="4" strokeDasharray="12 10" strokeLinecap="round" />
          <path d="M700 180 C820 180 810 270 930 270" fill="none" stroke="#dcfce7" strokeWidth="18" strokeLinecap="round" />
        </svg>

        <FlowPacket color="#7c3aed" delay="0s" />
        <FlowPacket color="#0ea5e9" delay="1.4s" />
        <FlowPacket color="#10b981" delay="2.8s" />
        <FlowPacket color="#f59e0b" delay="4.2s" path="lower" />

        <div className="absolute left-8 top-8 w-52 rounded-lg border border-blue-100 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
            <RadioTower className="h-4 w-4 text-blue-600" />
            媒体 API
          </div>
          <div className="mt-3 space-y-2 text-xs text-slate-500">
            <div>TikTok / Meta / Amazon</div>
            <div>巨量引擎 / 聚光</div>
            <div>消耗、曝光、点击、转化</div>
          </div>
        </div>

        <div className="absolute bottom-8 left-8 w-52 rounded-lg border border-emerald-100 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
            <Store className="h-4 w-4 text-emerald-600" />
            客户授权 API
          </div>
          <div className="mt-3 space-y-2 text-xs text-slate-500">
            <div>Shopify / TikTok Shop / Shopee</div>
            <div>订单、GMV、库存、毛利</div>
          </div>
        </div>

        <div className="absolute left-[38%] top-[104px] w-64 rounded-lg border border-violet-100 bg-white p-4 shadow-md">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
            <ServerCog className="h-4 w-4 text-violet-600" />
            统一数据契约
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
            {['spend', 'gmv', 'sku', 'inventory', 'margin', 'channel'].map((field) => (
              <span key={field} className="rounded-md bg-slate-100 px-2 py-1 text-center font-medium text-slate-600">{field}</span>
            ))}
          </div>
        </div>

        <div className="absolute right-8 top-8 w-52 rounded-lg border border-violet-100 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
            <BrainCircuit className="h-4 w-4 text-violet-600" />
            模型预估
          </div>
          <div className="mt-3 space-y-2 text-xs text-slate-500">
            <div>ROI / GMV / CPA</div>
            <div>SKU 库存风险</div>
            <div>预算分配模型</div>
          </div>
        </div>

        <div className="absolute bottom-8 right-8 w-52 rounded-lg border border-blue-100 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
            <Bot className="h-4 w-4 text-blue-600" />
            Agent 编排
          </div>
          <div className="mt-3 space-y-2 text-xs text-slate-500">
            <div>策略生成、护栏校验</div>
            <div>执行审批、复盘回写</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TimelineLog({ activeStep }) {
  const visibleEvents = useMemo(() => {
    const end = Math.min(eventTemplates.length, activeStep + 2);
    return eventTemplates.slice(0, end);
  }, [activeStep]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold text-slate-950">
          <Activity className="h-4 w-4 text-cyan-600" />
          实时数据事件
        </div>
        <span className="rounded-full bg-cyan-50 px-2 py-1 text-xs font-semibold text-cyan-700">streaming</span>
      </div>
      <div className="space-y-3">
        {visibleEvents.map((event, index) => (
          <div key={event} className="flex gap-3 text-sm">
            <div className="flex flex-col items-center">
              <span className={cx('h-2.5 w-2.5 rounded-full', index === visibleEvents.length - 1 ? 'animate-pulse bg-cyan-500' : 'bg-emerald-500')} />
              {index < visibleEvents.length - 1 && <span className="mt-1 h-8 w-px bg-slate-200" />}
            </div>
            <div>
              <div className="text-xs font-medium text-slate-400">T+{String(index * 15).padStart(2, '0')}s</div>
              <div className="mt-0.5 text-slate-700">{event}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AgentDataPage() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveStep((step) => (step + 1) % pipelineSteps.length);
    }, 1800);
    return () => window.clearInterval(timer);
  }, []);

  const activeModelIndex = activeStep >= 4 ? (activeStep - 4) % modelCards.length : -1;
  const agentIndex = Math.max(0, activeStep - 4);

  return (
    <div className="min-h-screen bg-[#f7f7f8] text-slate-900">
      <style>
        {`
          @keyframes agent-data-flow-primary {
            0% { transform: translate(72px, 86px); opacity: 0; }
            8% { opacity: 1; }
            32% { transform: translate(300px, 176px); }
            62% { transform: translate(700px, 176px); }
            92% { opacity: 1; }
            100% { transform: translate(930px, 86px); opacity: 0; }
          }
          @keyframes agent-data-flow-lower {
            0% { transform: translate(72px, 266px); opacity: 0; }
            10% { opacity: 1; }
            38% { transform: translate(300px, 176px); }
            66% { transform: translate(700px, 176px); }
            100% { transform: translate(930px, 266px); opacity: 0; }
          }
        `}
      </style>

      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1480px] items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-600 text-lg font-black text-white">麦</div>
            <div>
              <div className="text-lg font-bold text-slate-950">MaiDeal 数据系统</div>
              <div className="text-xs text-slate-500">展示数据源接入、模型预估与 Agent 编排如何组成后端闭环</div>
            </div>
          </div>
          <div className="hidden items-center gap-2 md:flex">
            {pipelineSteps.map((step, index) => (
              <button
                key={step.id}
                type="button"
                onClick={() => setActiveStep(index)}
                className={cx(
                  'rounded-lg px-3 py-2 text-sm font-semibold transition',
                  index === activeStep ? 'bg-violet-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100',
                )}
              >
                {step.title}
              </button>
            ))}
          </div>
          <a
            href="/agent-mode"
            className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            回到工作台
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </header>

      <main className="mx-auto flex max-w-[1480px] flex-col gap-5 px-6 py-5">
        <section className="grid gap-4 lg:grid-cols-[360px_minmax(0,1fr)_360px]">
          <aside className="space-y-3">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 font-semibold text-slate-950">
                <Layers3 className="h-5 w-5 text-violet-600" />
                数据源矩阵
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Demo 中没有客户真实授权时使用模拟器兜底；客户接入后，同一页面会展示真实 API 的授权、拉取、计算和回写状态。
              </p>
            </div>
            {dataSources.map((source, index) => (
              <SourceCard key={source.title} source={source} active={activeStep === index || (source.title === '模拟器兜底' && activeStep >= 3)} />
            ))}
          </aside>

          <div className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-slate-950">
                  <Sparkles className="h-5 w-5 text-violet-600" />
                  后端数据流入总线
                </div>
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                  可替换真实授权数据
                </span>
              </div>
              <div className="flex gap-3 overflow-x-auto pb-1">
                {pipelineSteps.map((step, index) => (
                  <StageBadge key={step.id} step={step} active={index === activeStep} />
                ))}
              </div>
            </div>

            <DataFlowMap activeStep={activeStep} />

            <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
              <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <div className="mb-3 flex items-center gap-2 font-semibold text-slate-950">
                  <Sigma className="h-5 w-5 text-violet-600" />
                  计算口径与特征层
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <MetricFormula label="成交口径" formula="GMV = Σ SKU 成交额" value="订单 API 与直播间商品点击归因后汇总" />
                  <MetricFormula label="效率口径" formula="ROAS = GMV / Spend" value="媒体消耗和订单成交按时间窗口对齐" />
                  <MetricFormula label="利润口径" formula="Profit = GMV × 毛利率 - Spend" value="毛利率来自客户 ERP 或人工输入" />
                  <MetricFormula label="库存口径" formula="Inventory = 初始库存 - Σ 成交件数" value="低库存触发护栏和预算降速" />
                </div>
              </div>
              <TimelineLog activeStep={activeStep} />
            </div>
          </div>

          <aside className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-slate-950">
                  <BrainCircuit className="h-5 w-5 text-violet-600" />
                  模型预估输出
                </div>
                <BadgeCheck className="h-5 w-5 text-emerald-500" />
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                模型不会替代业务判断，而是给 Agent 提供可解释的收益、风险和预算约束。
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              {modelCards.map((card, index) => (
                <ModelCard key={card.title} card={card} active={index === activeModelIndex} />
              ))}
            </div>
          </aside>
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_420px]">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 text-base font-semibold text-slate-950">
                  <Bot className="h-5 w-5 text-blue-600" />
                  Agent 编排如何消费这些数据
                </div>
                <p className="mt-1 text-sm text-slate-500">Agent 只看统一后的业务对象，不直接依赖某个平台字段。</p>
              </div>
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                orchestration runtime
              </span>
            </div>
            <div className="grid gap-3 md:grid-cols-5">
              {agentLoops.map((agent, index) => (
                <AgentCard key={agent.name} agent={agent} active={index === Math.min(agentLoops.length - 1, agentIndex)} />
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 text-base font-semibold text-slate-950">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              对嘉宾可解释的价值
            </div>
            <div className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
              <div className="flex gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                <span>没有真实授权时，模拟器按业务公式生成单调消耗和投放轨迹，用来验证决策闭环。</span>
              </div>
              <div className="flex gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                <span>真实上线时替换为客户授权 API，模型和 Agent 编排逻辑不变。</span>
              </div>
              <div className="flex gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                <span>商业价值来自跨平台数据统一、预算分配模型、投中预警和审批闭环。</span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
