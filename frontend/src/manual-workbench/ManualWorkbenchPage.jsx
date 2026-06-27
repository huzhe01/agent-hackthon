import React, { useMemo, useState } from 'react';
import {
  Activity,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  Database,
  DollarSign,
  Gauge,
  GitCompare,
  Layers3,
  ListChecks,
  Pause,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  Wallet,
} from 'lucide-react';
import { agentModeFallback } from '../agent-mode/agentModeDefaults';

const manualTabs = [
  { id: 'plan', label: '方案规划', icon: Target },
  { id: 'live', label: '直播托管', icon: Activity },
  { id: 'review', label: '复盘核算', icon: GitCompare },
];

function formatMoney(value, currency = '$') {
  const number = Number(value || 0);
  return `${currency}${number.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
}

function parseMoney(value, fallback = 0) {
  if (typeof value === 'number') return value;
  const parsed = Number(String(value || '').replace(/[^\d.-]/g, ''));
  return Number.isFinite(parsed) ? parsed : fallback;
}

function classNames(...items) {
  return items.filter(Boolean).join(' ');
}

function Panel({ children, className = '' }) {
  return (
    <section className={classNames('rounded-lg border border-slate-200 bg-white shadow-sm', className)}>
      {children}
    </section>
  );
}

function ProgressBar({ value = 0, max = 1, tone = 'violet' }) {
  const pct = Math.max(0, Math.min(100, Math.round((Number(value) / Math.max(1, Number(max))) * 100)));
  const color = tone === 'cyan' ? 'bg-cyan-500' : tone === 'amber' ? 'bg-amber-500' : 'bg-violet-600';
  return (
    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
      <div className={classNames('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
    </div>
  );
}

function ProjectSidebar({ projects, activeProjectId, setActiveProjectId, currentProject, currentWorkbench }) {
  return (
    <aside className="flex h-screen w-[286px] shrink-0 flex-col border-r border-slate-200 bg-slate-50">
      <div className="border-b border-slate-200 px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-600 text-base font-black text-white">麦</div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-slate-950">MaiDeal 直播后台</div>
            <div className="truncate text-xs text-slate-500">人工操作台</div>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        <Panel className="p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase text-slate-500">当前预算项目</span>
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
              {currentProject?.status || '进行中'}
            </span>
          </div>
          <div className="text-sm font-semibold leading-6 text-slate-950">{currentProject?.name || currentWorkbench.project?.name}</div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg bg-slate-100 p-2">
              <div className="text-slate-500">预算</div>
              <div className="mt-1 font-semibold text-slate-950">{currentProject?.budget || currentWorkbench.project?.totalBudget}</div>
            </div>
            <div className="rounded-lg bg-slate-100 p-2">
              <div className="text-slate-500">目标</div>
              <div className="mt-1 font-semibold text-slate-950">ROAS {currentProject?.roas || currentWorkbench.project?.targetRoas}</div>
            </div>
          </div>
        </Panel>

        <Panel className="mt-3 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase text-slate-500">预算项目历史</span>
            <span className="rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-semibold text-violet-700">{projects.length} 项</span>
          </div>
          <div className="space-y-1.5">
            {projects.map((project) => {
              const active = project.id === activeProjectId;
              return (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => setActiveProjectId(project.id)}
                  className={classNames(
                    'flex h-9 w-full items-center rounded-lg border px-2.5 text-left text-xs font-semibold transition',
                    active
                      ? 'border-violet-300 bg-violet-50 text-violet-900'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-violet-200 hover:bg-violet-50/60',
                  )}
                >
                  <span className="truncate">{project.name}</span>
                </button>
              );
            })}
          </div>
        </Panel>

        <Panel className="mt-3 p-3">
          <div className="mb-2 text-[11px] font-semibold uppercase text-slate-500">人工操作清单</div>
          <div className="space-y-2 text-xs">
            {['确认预算与 ROAS', '选择直播间方案', '设置预算护栏', '审批高风险动作'].map((item, index) => (
              <div key={item} className="flex items-center gap-2 rounded-lg bg-slate-100 px-2.5 py-2 text-slate-700">
                <span className={classNames('flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold', index < 2 ? 'bg-emerald-500 text-white' : 'bg-white text-slate-400')}>
                  {index < 2 ? '✓' : index + 1}
                </span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </aside>
  );
}

function Header({ activeTab, setActiveTab, project, frame, totalBudget, usedBudget }) {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5">
      <nav className="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
        {manualTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={classNames(
              'flex h-9 min-w-[104px] items-center justify-center gap-2 rounded-lg px-3 text-sm font-semibold transition',
              activeTab === tab.id ? 'bg-violet-600 text-white shadow-sm' : 'text-slate-600 hover:bg-white hover:text-slate-950',
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="flex items-center gap-5 text-xs">
        <div className="flex items-center gap-2 text-slate-500">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span>直播中 · {frame?.elapsed || '00:00:00'}</span>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-slate-500">总预算 / 已消耗</div>
          <div className="font-semibold text-slate-950">
            {formatMoney(totalBudget)} <span className="text-slate-300">/</span> <span className="text-amber-600">{formatMoney(usedBudget)}</span>
          </div>
        </div>
        <a
          href="/agent-mode"
          className="rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-xs font-semibold text-violet-700 hover:bg-violet-100"
        >
          切换 Agent Mode
        </a>
      </div>
    </header>
  );
}

function Metric({ label, value, badge, icon: Icon }) {
  return (
    <Panel className="p-4">
      <div className="mb-4 flex items-start justify-between">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-700">
          <Icon className="h-4 w-4" />
        </div>
        {badge && <span className="rounded-full bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700">{badge}</span>}
      </div>
      <div className="text-xs font-semibold text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-950">{value}</div>
    </Panel>
  );
}

function PlanView({ workbench, selectedRoomId, setSelectedRoomId, selectedPlan, setSelectedPlan }) {
  const rooms = workbench.live_rooms || [];
  const activeRoom = rooms.find((room) => room.id === selectedRoomId) || rooms.find((room) => room.recommended) || rooms[0];
  const planOptions = activeRoom?.plan_options?.length ? activeRoom.plan_options : workbench.plan_options || [];

  return (
    <div className="space-y-4">
      <Panel className="p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-violet-700">
          <Target className="h-4 w-4" />
          项目摘要
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          {[workbench.project?.product, workbench.project?.market, `预算 ${workbench.project?.totalBudget}`, `ROAS ${workbench.project?.targetRoas}`, workbench.project?.channels, workbench.project?.liveWindow]
            .filter(Boolean)
            .map((item) => (
              <span key={item} className="rounded-lg bg-slate-100 px-3 py-1.5 font-semibold text-slate-700">{item}</span>
            ))}
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
        <Panel className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-sm font-semibold text-slate-950">直播间 / 渠道</div>
            <ListChecks className="h-4 w-4 text-slate-400" />
          </div>
          <div className="space-y-2">
            {rooms.map((room) => {
              const active = room.id === selectedRoomId;
              return (
                <button
                  key={room.id}
                  type="button"
                  onClick={() => setSelectedRoomId(room.id)}
                  className={classNames(
                    'w-full rounded-lg border p-3 text-left transition',
                    active ? 'border-violet-300 bg-violet-50' : 'border-slate-200 bg-white hover:bg-slate-50',
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold text-slate-950">{room.name}</div>
                      <div className="mt-1 text-xs text-slate-500">{room.market}</div>
                    </div>
                    {room.recommended && <span className="rounded-full bg-violet-600 px-2 py-0.5 text-[10px] font-semibold text-white">推荐</span>}
                  </div>
                </button>
              );
            })}
          </div>
        </Panel>

        <Panel className="p-4">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-950">{activeRoom?.name || '请选择直播间'}</div>
              <div className="mt-1 text-xs text-slate-500">{activeRoom?.channel}</div>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">人工选择方案</span>
          </div>

          <div className="grid gap-3 xl:grid-cols-3">
            {planOptions.map((plan) => (
              <button
                key={plan.id}
                type="button"
                onClick={() => setSelectedPlan(plan.id)}
                className={classNames(
                  'relative rounded-lg border p-4 text-left transition',
                  selectedPlan === plan.id ? 'border-violet-400 bg-violet-50' : 'border-slate-200 bg-white hover:bg-slate-50',
                )}
              >
                {plan.recommended && <span className="absolute -top-2 right-3 rounded-full bg-violet-600 px-2 py-1 text-[10px] font-bold text-white">推荐</span>}
                <div className="text-lg font-semibold text-slate-950">{plan.title}</div>
                <div className="mt-3 space-y-2 text-sm text-slate-600">
                  {(plan.lines || []).map((line) => <div key={line}>· {line}</div>)}
                </div>
                <div className={classNames('mt-4 flex h-9 items-center justify-center rounded-lg text-sm font-semibold', selectedPlan === plan.id ? 'bg-violet-600 text-white' : 'bg-slate-100 text-slate-700')}>
                  选择{plan.title}
                </div>
              </button>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function LiveView({ workbench, frame, playing, setPlaying }) {
  const metrics = frame?.metrics || {};
  const pool = frame?.budget_pool || [];
  const skuAds = frame?.sku_ads || [];
  const events = frame?.events || [];
  const alert = frame?.alerts?.[0];

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">直播托管控制台</h1>
          <p className="mt-1 text-sm text-slate-500">人工按数据判断调仓、审批预算动作，并记录操作结果。</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPlaying(!playing)}
            className={classNames('flex h-9 items-center gap-2 rounded-lg border px-3 text-xs font-semibold', playing ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-600')}
          >
            {playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            {playing ? '暂停播放' : '继续播放'}
          </button>
          <button type="button" className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600">
            人工接管
          </button>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-3">
        <Metric label="收入" value={formatMoney(metrics.revenue)} badge="+动态" icon={DollarSign} />
        <Metric label="毛利润" value={formatMoney(metrics.profit)} badge="+实时" icon={Wallet} />
        <Metric label="实时 ROAS" value={metrics.roas?.toFixed ? metrics.roas.toFixed(1) : metrics.roas || '0.0'} badge={metrics.roas >= 3 ? '达标' : '预警'} icon={Gauge} />
        <Metric label="CPA" value={formatMoney(metrics.cpa)} badge={metrics.cpa > 10 ? '关注' : '安全'} icon={Target} />
        <Metric label="库存" value={`${metrics.inventory || 0} 件`} badge="安全" icon={Database} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <Panel className="p-4">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-950">
            <Wallet className="h-4 w-4 text-violet-700" />
            手动预算分配
          </div>
          <div className="space-y-4">
            {pool.map((item) => (
              <div key={item.id}>
                <div className="mb-2 flex justify-between text-xs">
                  <span className="font-semibold text-slate-700">{item.label}</span>
                  <span className="text-slate-500">{formatMoney(item.spent)} / {formatMoney(item.total)}</span>
                </div>
                <ProgressBar value={item.spent} max={item.total} tone={item.tone} />
              </div>
            ))}
          </div>
        </Panel>

        <Panel className={classNames('p-4', alert ? 'border-amber-200 bg-amber-50' : 'border-emerald-200 bg-emerald-50')}>
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-950">
            <ShieldCheck className="h-4 w-4 text-emerald-700" />
            人工审批队列
          </div>
          {alert ? (
            <div className="text-sm leading-6 text-slate-700">
              <div className="font-semibold text-amber-700">{alert.title}</div>
              <p className="mt-1">{alert.message}</p>
              <p className="mt-1">{alert.recommendation}</p>
              <div className="mt-4 flex gap-2">
                {(alert.actions || ['批准', '继续观察']).map((action) => (
                  <button key={action} type="button" className="h-9 flex-1 rounded-lg bg-violet-600 text-sm font-semibold text-white">{action}</button>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm leading-6 text-slate-700">当前无高风险动作。预算调整在护栏内，可按人工策略继续推进。</p>
          )}
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel className="p-4">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-950">
            <Clock3 className="h-4 w-4 text-cyan-600" />
            操作记录
          </div>
          <div className="space-y-3 text-sm">
            {events.map((event, index) => (
              <div key={`${event.time}-${event.text}-${index}`} className="grid grid-cols-[48px_72px_1fr] gap-2 rounded-lg bg-slate-50 p-2">
                <span className="text-slate-500">{event.time}</span>
                <span className="font-semibold text-violet-700">{event.agent}</span>
                <span className="text-slate-700">{event.text}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel className="p-4">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-950">
            <Layers3 className="h-4 w-4 text-violet-700" />
            商品 SKU 投放
          </div>
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  <th className="px-3 py-2 text-left">SKU</th>
                  <th className="py-2 text-left">消耗</th>
                  <th className="py-2 text-left">GMV</th>
                  <th className="py-2 text-left">ROI</th>
                  <th className="px-3 py-2 text-right">状态</th>
                </tr>
              </thead>
              <tbody>
                {skuAds.map((sku) => (
                  <tr key={sku.id} className="border-t border-slate-100">
                    <td className="px-3 py-3">
                      <div className="font-semibold text-slate-950">{sku.name}</div>
                      <div className="mt-1 text-xs text-slate-500">{sku.sku}</div>
                    </td>
                    <td>{formatMoney(sku.spend)}</td>
                    <td>{formatMoney(sku.gmv)}</td>
                    <td className={sku.roi >= 3 ? 'font-semibold text-emerald-700' : 'font-semibold text-amber-700'}>{sku.roi}</td>
                    <td className="px-3 text-right text-slate-600">{sku.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function ReviewView({ workbench }) {
  const benchmarks = workbench.review_benchmarks || [];
  const actions = workbench.review_actions || [];
  const leads = workbench.lead_rows || [];

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">复盘核算</h1>
          <p className="mt-1 text-sm text-slate-500">把线索资产、关键动作和增量收益放在同一个人工复盘页。</p>
        </div>
        <button type="button" className="flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700">
          <ClipboardCheck className="h-4 w-4" />
          导出复盘
        </button>
      </div>

      <Panel className="p-4">
        <div className="mb-4 text-sm font-semibold text-slate-950">相对固定预算基线的增量</div>
        <div className="grid gap-3 md:grid-cols-3">
          {benchmarks.map((item) => (
            <div key={item.title} className={classNames('rounded-lg border p-4', item.highlight ? 'border-emerald-200 bg-emerald-50' : 'border-slate-200 bg-white')}>
              <div className="text-xs text-slate-500">{item.title}</div>
              <div className="mt-3 text-xl font-semibold text-slate-950">{item.metric}</div>
              <div className="mt-2 text-sm text-slate-600">{item.sub}</div>
              <div className="mt-3 text-sm font-semibold text-emerald-700">{item.note}</div>
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel className="p-4">
          <div className="mb-4 text-sm font-semibold text-slate-950">关键动作回顾</div>
          <div className="space-y-2">
            {actions.map((action) => (
              <div key={`${action.time}-${action.action}`} className="grid grid-cols-[56px_1fr_72px_48px] gap-3 rounded-lg border border-slate-200 p-3 text-sm">
                <span className="text-slate-500">{action.time}</span>
                <span className="text-slate-700">{action.action}</span>
                <span className="font-semibold text-emerald-700">{action.result}</span>
                <span className="text-xs text-slate-500">{action.type}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel className="p-4">
          <div className="mb-4 text-sm font-semibold text-slate-950">线索资产</div>
          <div className="space-y-2">
            {leads.slice(0, 5).map((lead) => (
              <div key={lead.user} className="grid grid-cols-[1fr_70px_48px_64px] gap-3 rounded-lg border border-slate-200 p-3 text-sm">
                <span className="font-semibold text-slate-950">{lead.user}</span>
                <span className="text-violet-700">{lead.channel}</span>
                <span className="font-semibold text-emerald-700">{lead.score}</span>
                <span className="text-slate-500">{lead.status}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function OperatorPanel({ workbench, selectedPlan, selectedRoom, frame }) {
  const guardLimit = workbench.guard_limit || '15';
  const threshold = workbench.approval_threshold || '800';
  return (
    <aside className="flex h-screen w-[360px] shrink-0 flex-col border-l border-slate-200 bg-slate-50">
      <div className="border-b border-slate-200 px-4 py-4">
        <div className="flex items-center gap-2 font-semibold text-slate-950">
          <SlidersHorizontal className="h-4 w-4 text-violet-700" />
          操作面板
        </div>
        <p className="mt-1 text-xs text-slate-500">人工调整预算、护栏与审批动作。</p>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
        <Panel className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-950">当前选择</span>
            <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">在线</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg bg-slate-100 p-2">
              <div className="text-slate-500">Plan</div>
              <div className="mt-1 font-semibold text-slate-950">{selectedPlan}</div>
            </div>
            <div className="rounded-lg bg-slate-100 p-2">
              <div className="text-slate-500">主直播间</div>
              <div className="mt-1 truncate font-semibold text-slate-950">{selectedRoom?.name || '—'}</div>
            </div>
          </div>
        </Panel>

        <Panel className="p-4">
          <div className="mb-4 text-sm font-semibold text-slate-950">预算护栏</div>
          <div className="space-y-4">
            <label className="block">
              <div className="mb-2 flex justify-between text-xs">
                <span className="text-slate-500">单次调仓上限</span>
                <span className="font-semibold text-slate-950">{guardLimit}%</span>
              </div>
              <input type="range" value={guardLimit} min="5" max="30" readOnly className="w-full accent-violet-600" />
            </label>
            <label className="block">
              <div className="mb-2 flex justify-between text-xs">
                <span className="text-slate-500">审批金额阈值</span>
                <span className="font-semibold text-slate-950">{formatMoney(threshold)}</span>
              </div>
              <input type="range" value={threshold} min="200" max="2000" readOnly className="w-full accent-violet-600" />
            </label>
          </div>
        </Panel>

        <Panel className="p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-950">
            <Search className="h-4 w-4 text-violet-700" />
            人工排查
          </div>
          <div className="space-y-2 text-sm">
            {['查看低效 SKU', '调整直播间预算', '审批追加预算', '记录复盘备注'].map((item) => (
              <button key={item} type="button" className="flex h-10 w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-3 text-left font-semibold text-slate-700 hover:bg-slate-50">
                {item}
                <ChevronRight className="h-4 w-4 text-slate-400" />
              </button>
            ))}
          </div>
        </Panel>

        <Panel className="p-4">
          <div className="mb-3 text-sm font-semibold text-slate-950">实时备注</div>
          <textarea
            className="h-24 w-full resize-none rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-violet-300"
            placeholder={`当前 ${frame?.time || '直播中'}：记录本轮人工判断...`}
          />
          <button type="button" className="mt-3 h-10 w-full rounded-lg bg-violet-600 text-sm font-semibold text-white">
            保存操作记录
          </button>
        </Panel>
      </div>
    </aside>
  );
}

export default function ManualWorkbenchPage() {
  const budget_projects = agentModeFallback.budget_projects || [];
  const projects = budget_projects.length ? budget_projects : [{ id: 'fallback', name: agentModeFallback.project.name, workbench: agentModeFallback }];
  const [activeProjectId, setActiveProjectId] = useState(projects[0]?.id);
  const [activeTab, setActiveTab] = useState('live');
  const [selectedRoomId, setSelectedRoomId] = useState(projects[0]?.workbench?.selected_room_id || agentModeFallback.selected_room_id);
  const [selectedPlan, setSelectedPlan] = useState(projects[0]?.workbench?.selected_plan || agentModeFallback.selected_plan);
  const [liveIndex, setLiveIndex] = useState(2);
  const [playing, setPlaying] = useState(false);

  const activeProject = projects.find((project) => project.id === activeProjectId) || projects[0];
  const workbench = activeProject?.workbench || agentModeFallback;
  const frames = workbench.live_demo?.frames?.length ? workbench.live_demo.frames : agentModeFallback.live_demo.frames;
  const frame = frames[Math.min(liveIndex, frames.length - 1)] || frames[0];
  const totalBudget = parseMoney(workbench.project?.totalBudgetValue || workbench.project?.totalBudget || activeProject?.budget, 5000);
  const usedBudget = Number(frame?.metrics?.spend || 0);
  const selectedRoom = useMemo(
    () => (workbench.live_rooms || []).find((room) => room.id === selectedRoomId) || (workbench.live_rooms || []).find((room) => room.recommended) || (workbench.live_rooms || [])[0],
    [workbench.live_rooms, selectedRoomId],
  );

  React.useEffect(() => {
    const nextWorkbench = activeProject?.workbench || agentModeFallback;
    setSelectedRoomId(nextWorkbench.selected_room_id || nextWorkbench.live_rooms?.find((room) => room.recommended)?.id || nextWorkbench.live_rooms?.[0]?.id || 'brand');
    setSelectedPlan(nextWorkbench.selected_plan || 'balanced');
    setLiveIndex(Math.min(2, Math.max(0, (nextWorkbench.live_demo?.frames || []).length - 1)));
  }, [activeProjectId]);

  React.useEffect(() => {
    if (!playing || !frames.length) return undefined;
    const timer = window.setInterval(() => {
      setLiveIndex((index) => (index + 1) % frames.length);
    }, workbench.live_demo?.tick_interval_ms || 10000);
    return () => window.clearInterval(timer);
  }, [playing, frames.length, workbench.live_demo?.tick_interval_ms]);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100 text-slate-900">
      <ProjectSidebar
        projects={projects}
        activeProjectId={activeProjectId}
        setActiveProjectId={setActiveProjectId}
        currentProject={activeProject}
        currentWorkbench={workbench}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          project={workbench.project}
          frame={frame}
          totalBudget={totalBudget}
          usedBudget={usedBudget}
        />

        <main className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
          {activeTab === 'plan' && (
            <PlanView
              workbench={workbench}
              selectedRoomId={selectedRoomId}
              setSelectedRoomId={setSelectedRoomId}
              selectedPlan={selectedPlan}
              setSelectedPlan={setSelectedPlan}
            />
          )}
          {activeTab === 'live' && (
            <LiveView
              workbench={workbench}
              frame={frame}
              playing={playing}
              setPlaying={setPlaying}
            />
          )}
          {activeTab === 'review' && <ReviewView workbench={workbench} />}
        </main>
      </div>

      <OperatorPanel
        workbench={workbench}
        selectedPlan={selectedPlan}
        selectedRoom={selectedRoom}
        frame={frame}
      />
    </div>
  );
}
