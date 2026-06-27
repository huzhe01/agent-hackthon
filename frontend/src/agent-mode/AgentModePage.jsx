import React, { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowUp,
  BarChart3,
  Bot,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ChevronsLeftRight,
  CircleDollarSign,
  ClipboardCheck,
  Compass,
  Database,
  FileCheck2,
  Film,
  Gauge,
  GitCompare,
  Layers3,
  Loader2,
  MessageSquareText,
  Mic,
  PanelLeftClose,
  PanelRightClose,
  Paperclip,
  Pause,
  Play,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Moon,
  Sun,
  Target,
  Users,
  Wallet,
  Wand2,
  Zap,
} from 'lucide-react';
import * as api from '../services/api';
import { agentModeFallback, fallbackDataSources, fallbackModels } from './agentModeDefaults';

const stageTabs = [
  { id: 'plan', label: '投放方案', icon: Target },
  { id: 'live', label: '在线看板', icon: Activity },
  { id: 'review', label: '盘后迭代', icon: GitCompare },
];

function formatMoney(value, currency = '$') {
  const number = Number(value || 0);
  return `${currency}${number.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
}

function parseMoneyValue(value, fallback = 0) {
  if (typeof value === 'number') return value;
  const cleaned = String(value || '').replace(/[^\d.-]/g, '');
  if (!cleaned) return fallback;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function mergeWorkbench(nextWorkbench = {}) {
  return {
    ...agentModeFallback,
    ...nextWorkbench,
    project: {
      ...agentModeFallback.project,
      ...(nextWorkbench.project || {}),
    },
    layout: {
      ...agentModeFallback.layout,
      ...(nextWorkbench.layout || {}),
    },
  };
}

function deepMerge(base, patch) {
  if (!patch || typeof patch !== 'object') return base;
  const result = { ...base };
  for (const key of Object.keys(patch)) {
    const pv = patch[key];
    const bv = base[key];
    if (
      Array.isArray(bv) &&
      pv &&
      typeof pv === 'object' &&
      !Array.isArray(pv)
    ) {
      result[key] = bv.map((item) => {
        const update = pv[item?.id];
        return update ? { ...item, ...update } : item;
      });
    } else if (
      pv &&
      typeof pv === 'object' &&
      !Array.isArray(pv) &&
      bv &&
      typeof bv === 'object' &&
      !Array.isArray(bv)
    ) {
      result[key] = deepMerge(bv, pv);
    } else {
      result[key] = pv;
    }
  }
  return result;
}

const BRIEF_FIELD_LABELS = {
  budget: '投放总预算',
  target_roas: '目标 ROAS',
  channels: '投放渠道',
  products: '投放商品',
  market: '目标市场',
  live_window: '直播时间',
  inventory: '库存',
  margin: '毛利率',
  constraints: '约束条件',
};
const BRIEF_CORE_FIELDS = ['budget', 'target_roas', 'products', 'market', 'channels'];

function workbenchReducer(state, action) {
  switch (action.type) {
    case 'INIT':
      return mergeWorkbench(action.workbench);
    case 'WORKBENCH_PATCH':
      return deepMerge(state, action.patch);
    case 'PHASE_CHANGE':
      return { ...state, phase: action.phase };
    case 'VIEW_SWITCH':
      return state;
    case 'AGENT_ACTION':
      return {
        ...state,
        left_timeline: [...(state.left_timeline || []), action.event],
      };
    case 'SET_FIELD':
      return { ...state, [action.field]: action.value };
    case 'SET_PROJECT':
      return { ...state, project: { ...state.project, ...action.patch } };
    case 'SELECT_BUDGET_PROJECT': {
      const budgetProjects = state.budget_projects || [];
      const selectedProject = budgetProjects.find((project) => project.id === action.projectId);
      if (!selectedProject?.workbench) {
        return { ...state, active_project_id: action.projectId };
      }
      return mergeWorkbench({
        ...state,
        ...selectedProject.workbench,
        active_project_id: action.projectId,
        budget_projects: budgetProjects,
        layout: state.layout,
      });
    }
    case 'RESET':
      return mergeWorkbench(agentModeFallback);
    default:
      return state;
  }
}

function toneClass(tone) {
  const map = {
    violet: 'bg-violet-400 text-violet-300 border-violet-500/30',
    indigo: 'bg-indigo-400 text-indigo-300 border-indigo-500/30',
    cyan: 'bg-cyan-400 text-cyan-300 border-cyan-500/30',
    amber: 'bg-amber-400 text-amber-300 border-amber-500/30',
    emerald: 'bg-emerald-400 text-emerald-300 border-emerald-500/30',
    rose: 'bg-rose-400 text-rose-300 border-rose-500/30',
  };
  return map[tone] || map.violet;
}

function StatusDot({ tone = 'emerald', pulse = true }) {
  const color = toneClass(tone).split(' ')[0];
  return <span className={`h-2 w-2 rounded-full ${color} ${pulse ? 'animate-pulse' : ''}`} />;
}

function ThemeToggle({ theme, setTheme }) {
  const options = [
    { id: 'light', label: '浅色', icon: Sun, ariaLabel: '切换为浅色主题' },
    { id: 'dark', label: '深色', icon: Moon, ariaLabel: '切换为深色主题' },
  ];

  return (
    <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 p-1">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          onClick={() => setTheme(option.id)}
          aria-label={option.ariaLabel}
          title={option.ariaLabel}
          className={`flex h-8 items-center gap-1.5 rounded-md px-2.5 text-xs font-semibold transition ${
            theme === option.id
              ? 'bg-white text-slate-950 shadow-sm'
              : 'text-slate-500 hover:bg-white/5 hover:text-white'
          }`}
        >
          <option.icon className="h-3.5 w-3.5" />
          {option.label}
        </button>
      ))}
    </div>
  );
}

function GlassCard({ children, className = '' }) {
  return (
    <div className={`rounded-lg border border-white/10 bg-white/[0.035] shadow-[0_20px_70px_rgba(0,0,0,0.18)] ${className}`}>
      {children}
    </div>
  );
}

function FocusModeButton({ focusMode, onToggleFocus }) {
  return (
    <button
      type="button"
      onClick={onToggleFocus}
      className="flex h-8 items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 text-xs font-semibold text-slate-300 hover:bg-white/10"
      aria-label={focusMode ? '退出专注模式' : '进入专注模式'}
    >
      <ChevronsLeftRight className="h-4 w-4" />
      {focusMode ? '退出专注' : '专注模式'}
    </button>
  );
}

function StageTabs({ activeStage, setActiveStage }) {
  return (
    <nav className="flex items-center gap-1 rounded-lg bg-white/5 p-1">
      {stageTabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => setActiveStage(tab.id)}
          className={`flex h-9 min-w-[104px] items-center justify-center gap-2 rounded-lg px-3 text-sm font-semibold transition ${
            activeStage === tab.id
              ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-950/40'
              : 'text-slate-400 hover:bg-white/5 hover:text-white'
          }`}
        >
          <tab.icon className="h-4 w-4" />
          {tab.label}
        </button>
      ))}
    </nav>
  );
}

function TopBar({ activeStage, setActiveStage, totalBudget, usedBudget, theme, setTheme, liveElapsed = '00:00:00' }) {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 bg-[#0d1320] px-5">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-blue-600 text-base font-black text-white">麦</div>
        <div className="min-w-0">
          <div className="truncate text-base font-semibold text-white">MaiDeal工作台</div>
        </div>
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>

      <StageTabs activeStage={activeStage} setActiveStage={setActiveStage} />

      <div className="flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <StatusDot tone="emerald" />
          <span>直播中 · {liveElapsed}</span>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-slate-500">总预算 / 已消耗</div>
          <div className="font-semibold text-white">
            {formatMoney(totalBudget)} <span className="text-slate-600">/</span> <span className="text-amber-400">{formatMoney(usedBudget)}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

function LeftPanel({
  collapsed,
  onToggleCollapsed,
  goal,
  leftPanelWidth,
  onResizePointerDown,
  onReset,
  agentRoster = [],
  budgetProjects = [],
  activeBudgetProjectId,
  onSelectBudgetProject,
}) {
  const projectBrief = goal?.name || `${goal?.product || '项目'} · ${goal?.market || '市场'}`;
  const activeProject = budgetProjects.find((project) => project.id === activeBudgetProjectId);

  if (collapsed) {
    return (
      <aside className="flex h-[calc(100vh-4rem)] w-16 shrink-0 flex-col items-center border-r border-white/10 bg-[#0d1320] py-4">
        <button
          type="button"
          onClick={onToggleCollapsed}
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-600 text-white hover:bg-violet-500"
          aria-label="展开左侧栏"
          title="展开左侧栏"
        >
          <Sparkles className="h-5 w-5" />
        </button>
        <div className="mt-6 flex flex-col items-center gap-2 text-slate-500">
          <Wallet className="h-5 w-5" />
          <span className="rounded-full bg-white/10 px-2 py-1 text-[10px] font-semibold">
            {budgetProjects.length}
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside
      className="relative flex h-[calc(100vh-4rem)] shrink-0 flex-col border-r border-white/10 bg-[#0d1320]"
      style={{ width: leftPanelWidth, minWidth: 240, maxWidth: 420 }}
    >
      <div
        role="separator"
        aria-label="拖动调整左侧栏宽度"
        title="拖动调整左侧栏宽度"
        onPointerDown={onResizePointerDown}
        className="absolute right-[-3px] top-0 z-30 h-full w-2 cursor-col-resize touch-none bg-transparent transition hover:bg-violet-400/40"
      />
      <div className="flex h-14 items-center justify-between border-b border-white/10 px-4">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-violet-400" />
          <span className="font-semibold text-white">预算项目</span>
        </div>
        <button
          type="button"
          onClick={onToggleCollapsed}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-white/5 hover:text-white"
          aria-label="收起左侧栏"
          title="收起左侧栏"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      <div className="min-h-0 flex flex-1 flex-col overflow-y-auto p-3">
        <GlassCard className="p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div className="text-xs font-semibold uppercase tracking-normal text-slate-500">当前预算项目</div>
            <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
              {activeProject?.status || '进行中'}
            </span>
          </div>
          <div className="text-sm font-semibold leading-6 text-slate-100">
            {projectBrief}
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg bg-white/5 p-2">
              <div className="text-slate-500">预算</div>
              <div className="mt-1 font-semibold text-white">{goal?.totalBudget || activeProject?.budget || '—'}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-2">
              <div className="text-slate-500">目标</div>
              <div className="mt-1 font-semibold text-white">ROAS {goal?.targetRoas || activeProject?.roas || '—'}</div>
            </div>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="mt-3 flex h-8 w-full items-center justify-center gap-1.5 rounded-lg border border-white/10 bg-white/5 text-xs font-semibold text-slate-400 hover:bg-white/10 hover:text-white"
          >
            <RefreshCw className="h-3 w-3" />
            重置项目
          </button>
        </GlassCard>

        <BudgetProjectHistoryList
          budgetProjects={budgetProjects}
          activeBudgetProjectId={activeBudgetProjectId}
          onSelectBudgetProject={onSelectBudgetProject}
        />
      </div>

      <AgentStatusDock agentRoster={agentRoster} />
    </aside>
  );
}

function BudgetProjectHistoryList({ budgetProjects = [], activeBudgetProjectId, onSelectBudgetProject }) {
  if (!budgetProjects.length) return null;

  return (
    <GlassCard className="mt-3 flex-1 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase tracking-normal text-slate-500">预算项目历史</div>
        <span className="rounded-full bg-violet-500/10 px-2 py-0.5 text-[10px] font-semibold text-violet-600">
          {budgetProjects.length} 个项目
        </span>
      </div>
      <div className="space-y-1.5">
        {budgetProjects.map((project) => {
          const active = project.id === activeBudgetProjectId;
          return (
            <button
              key={project.id}
              type="button"
              onClick={() => onSelectBudgetProject?.(project.id)}
              aria-pressed={active}
              title={project.name}
              className={`flex h-9 w-full items-center rounded-lg border px-2.5 text-left text-xs transition ${
                active
                  ? 'border-violet-500/60 bg-violet-500/10'
                  : 'border-white/10 bg-white/[0.035] hover:border-violet-300/60 hover:bg-white/10'
              }`}
            >
              <span className="min-w-0 flex-1 truncate font-semibold text-white">{project.name}</span>
            </button>
          );
        })}
      </div>
    </GlassCard>
  );
}

function AgentStatusDock({ agentRoster = [] }) {
  if (!agentRoster.length) return null;

  return (
    <div className="border-t border-white/10 p-3">
      <GlassCard className="p-3">
        <div className="mb-2 flex items-center justify-between">
          <div className="text-xs font-semibold uppercase tracking-normal text-slate-500">子 Agent 状态</div>
          <span className="rounded-full bg-violet-500/10 px-2 py-0.5 text-[10px] font-semibold text-violet-600">共享状态</span>
        </div>
        <div className="space-y-1.5">
          {agentRoster.map((agent) => (
            <div key={agent.id} className="flex items-center gap-2 text-xs">
              <StatusDot tone={agent.tone} pulse={agent.status !== '待命'} />
              <span className="min-w-0 flex-1 truncate font-semibold text-white">{agent.name}</span>
              <span className="text-slate-500">{agent.status}</span>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}

function MetricPill({ label, value, delta, tone = 'emerald', icon: Icon = BarChart3 }) {
  const color = {
    emerald: 'text-emerald-300',
    violet: 'text-violet-300',
    cyan: 'text-cyan-300',
    amber: 'text-amber-300',
    rose: 'text-rose-300',
  }[tone];
  return (
    <GlassCard className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5">
          <Icon className={`h-4 w-4 ${color}`} />
        </div>
        <span className={`rounded-full bg-white/5 px-2 py-1 text-xs font-semibold ${color}`}>{delta}</span>
      </div>
      <div className="mt-4 text-xs font-semibold text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-white">{value}</div>
    </GlassCard>
  );
}

function GoalField({ label, value, onChange }) {
  return (
    <label className="rounded-lg border border-white/10 bg-white/[0.035] p-3">
      <span className="block text-[11px] font-semibold text-slate-500">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full bg-transparent text-sm font-semibold text-white outline-none placeholder:text-slate-600"
      />
    </label>
  );
}

function LiveRoomCard({ room, selected, onSelect }) {
  const pct = Math.min(100, Math.round((room.spent / room.budget) * 100));
  return (
    <button
      type="button"
      onClick={() => onSelect(room.id)}
      className={`min-w-0 rounded-lg border p-4 text-left transition ${
        selected
          ? 'border-violet-500/70 bg-gradient-to-b from-violet-500/20 to-white/[0.025] shadow-lg shadow-violet-950/30'
          : 'border-white/10 bg-white/[0.035] hover:border-white/20 hover:bg-white/[0.055]'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-base font-semibold text-white">{room.name}</h3>
          <p className="mt-1 text-xs text-slate-500">{room.market}</p>
        </div>
        {room.recommended && <span className="rounded-full bg-violet-500 px-2 py-1 text-[10px] font-bold text-white">推荐</span>}
      </div>
      <p className="mt-3 text-sm text-slate-300">{room.role}</p>
      <div className="mt-4 space-y-2 text-xs text-slate-400">
        <div className="flex justify-between"><span>预算建议</span><b className="text-white">{formatMoney(room.budget)}</b></div>
        <div className="flex justify-between"><span>预估 ROAS</span><b className="text-emerald-300">{room.roas}</b></div>
        <div className="flex justify-between"><span>渠道</span><b className="text-slate-200">{room.channel}</b></div>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-400" style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-3 flex items-center justify-between text-xs">
        <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-slate-300">{room.status}</span>
        <span className="text-slate-500">{room.risk}</span>
      </div>
    </button>
  );
}

function BudgetBar({ label, spent, total, tone = 'violet' }) {
  const pct = Math.min(100, Math.round((Number(spent || 0) / Number(total || 1)) * 100));
  const gradient = tone === 'cyan' ? 'from-cyan-400 to-blue-500' : tone === 'amber' ? 'from-amber-400 to-orange-500' : 'from-violet-500 to-indigo-500';
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs">
        <span className="font-semibold text-slate-300">{label}</span>
        <span className="text-slate-500">{formatMoney(spent)} / {formatMoney(total)}</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-white/10">
        <div className={`h-full rounded-full bg-gradient-to-r ${gradient}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function ProcessSteps({ descriptions = [] }) {
  return (
    <div className="grid grid-cols-4 gap-3">
      {stageTabs.map((tab, index) => (
        <div key={tab.id} className="rounded-lg border border-white/10 bg-white/[0.035] p-3">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5">
              <tab.icon className="h-4 w-4 text-violet-300" />
            </div>
            <span className="text-xs font-semibold text-slate-600">0{index + 1}</span>
          </div>
          <div className="font-semibold text-white">{tab.label}</div>
          <p className="mt-2 text-xs leading-5 text-slate-500">
            {descriptions[index] || ''}
          </p>
        </div>
      ))}
    </div>
  );
}

function BriefingCanvas({ briefFields = {}, focusMode, onToggleFocus }) {
  const fields = Object.entries(BRIEF_FIELD_LABELS);
  const coreSet = new Set(BRIEF_CORE_FIELDS);
  const filledCore = BRIEF_CORE_FIELDS.filter((k) => briefFields[k] != null).length;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-white">项目 Brief</h1>
            <p className="mt-2 text-sm text-slate-500">
              请在右侧对话框描述您的经营目标，MaiDeal 将自动提取关键字段 ·
              核心字段收集完成后自动生成三套投放方案
            </p>
          </div>
          <FocusModeButton focusMode={focusMode} onToggleFocus={onToggleFocus} />
        </div>
      </div>

      <GlassCard className="p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold text-violet-300">
            <ClipboardCheck className="h-4 w-4" />
            经营信息收集
          </div>
          <span className="rounded-full bg-violet-500/15 px-3 py-1 text-xs font-semibold text-violet-300">
            {filledCore}/{BRIEF_CORE_FIELDS.length} 核心字段
          </span>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {fields.map(([key, label]) => {
            const value = briefFields[key];
            const filled = value != null;
            const isCore = coreSet.has(key);
            return (
              <div
                key={key}
                className={`rounded-lg p-4 transition-all ${
                  filled
                    ? 'border border-violet-500/40 bg-violet-500/10'
                    : 'border border-dashed border-white/15 bg-white/[0.02]'
                }`}
              >
                <div className={`text-xs ${filled ? 'text-violet-300' : 'text-slate-600'}`}>
                  {label}{isCore ? ' *' : ''}
                </div>
                <div className={`mt-2 text-lg font-semibold ${filled ? 'text-white' : 'text-slate-700'}`}>
                  {filled
                    ? (typeof value === 'number' ? `$${value.toLocaleString()}` : String(value))
                    : '—'}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 transition-all duration-500"
            style={{ width: `${(filledCore / BRIEF_CORE_FIELDS.length) * 100}%` }}
          />
        </div>
        <p className="mt-3 text-xs text-slate-500">
          * 标记为核心字段，收集完成后将自动生成投放方案。您可以在右侧对话框中自然描述，如
          「我要给便携榨汁杯做一场美国直播，预算 5000 美金，目标 ROAS 3.0」
        </p>
      </GlassCard>
    </div>
  );
}

function PlanCanvas({
  goal,
  selectedRoomId,
  setSelectedRoomId,
  selectedPlan,
  setSelectedPlan,
  guardLimit,
  onGuardLimitChange,
  approvalThreshold,
  onApprovalThresholdChange,
  onStartManagedDelivery,
  liveRooms = [],
  planOptions = [],
  disabledActions = [],
  phase,
  briefFields,
  focusMode,
  onToggleFocus,
}) {
  if (phase === 'briefing') {
    return <BriefingCanvas briefFields={briefFields} focusMode={focusMode} onToggleFocus={onToggleFocus} />;
  }
  const activeRoom = liveRooms.find((room) => room.id === selectedRoomId) || liveRooms.find((room) => room.recommended) || liveRooms[0] || null;
  const roomPlanOptions = activeRoom?.plan_options?.length ? activeRoom.plan_options : planOptions;

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">投放方案</h1>
          <p className="mt-2 text-sm text-slate-500">规划模块输出 · 直播间矩阵预算拆分 · 当前推荐均衡方案</p>
        </div>
        <FocusModeButton focusMode={focusMode} onToggleFocus={onToggleFocus} />
      </div>

      {liveRooms.length > 0 && (
        <ChannelPlanSelector
          liveRooms={liveRooms}
          activeRoom={activeRoom}
          selectedRoomId={selectedRoomId}
          setSelectedRoomId={setSelectedRoomId}
          planOptions={roomPlanOptions}
          selectedPlan={selectedPlan}
          setSelectedPlan={setSelectedPlan}
        />
      )}

      <GlassCard className="p-5">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
          <ShieldCheck className="h-4 w-4 text-emerald-300" />
          预算托管护栏
        </div>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="mb-2 flex justify-between text-sm">
              <span className="text-slate-400">单次自动调仓上限</span>
              <span className="font-semibold text-white">{guardLimit}%</span>
            </div>
            <input
              type="range"
              min="5"
              max="30"
              value={guardLimit}
              onChange={(event) => onGuardLimitChange(event.target.value)}
              className="w-full accent-violet-500"
            />
          </div>
          <div>
            <div className="mb-2 flex justify-between text-sm">
              <span className="text-slate-400">单次审批金额阈值</span>
              <span className="font-semibold text-white">{formatMoney(approvalThreshold)}</span>
            </div>
            <input
              type="range"
              min="200"
              max="2000"
              step="100"
              value={approvalThreshold}
              onChange={(event) => onApprovalThresholdChange(event.target.value)}
              className="w-full accent-violet-500"
            />
          </div>
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-2 text-sm">
          <span className="mr-2 text-slate-500">禁用动作</span>
          {disabledActions.map((item) => (
            <span key={item} className="rounded-lg border border-rose-500/30 bg-rose-500/15 px-3 py-1.5 text-xs font-semibold text-rose-200">禁用 {item}</span>
          ))}
          <span className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-400">需审批 修改目标ROAS</span>
        </div>
      </GlassCard>

      {planOptions.length > 0 && (
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onStartManagedDelivery}
            className="flex h-11 items-center gap-2 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 px-5 text-sm font-semibold text-white shadow-lg shadow-violet-950/40"
          >
            <Play className="h-4 w-4" />
            批准并启动托管
          </button>
        </div>
      )}
    </div>
  );
}

function ChannelPlanSelector({
  liveRooms = [],
  activeRoom,
  selectedRoomId,
  setSelectedRoomId,
  planOptions = [],
  selectedPlan,
  setSelectedPlan,
}) {
  return (
    <GlassCard className="p-4">
      <div className="grid gap-4 md:grid-cols-[240px_minmax(0,1fr)]">
        <div>
          <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-violet-300">
            <Film className="h-3.5 w-3.5" />
            渠道 / 直播间
          </div>
          <div className="space-y-2">
            {liveRooms.map((room) => {
              const active = room.id === selectedRoomId;
              return (
                <button
                  key={room.id}
                  type="button"
                  onClick={() => setSelectedRoomId(room.id)}
                  className={`w-full rounded-lg border p-3 text-left transition ${
                    active
                      ? 'border-violet-500/60 bg-violet-500/10'
                      : 'border-white/10 bg-white/[0.035] hover:border-violet-300/60 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`h-2 w-2 rounded-full ${active ? 'bg-violet-500' : 'bg-slate-300'}`} />
                    <span className="min-w-0 flex-1 truncate text-sm font-semibold text-white">{room.name}</span>
                    {room.recommended && <span className="rounded-full bg-violet-500 px-2 py-0.5 text-[10px] font-bold text-white">推荐</span>}
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-2 text-xs text-slate-500">
                    <span className="truncate">{room.market}</span>
                    <span>{room.status}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="min-w-0">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="text-xs font-semibold text-violet-300">模式方案</div>
              <div className="mt-1 truncate text-base font-semibold text-white">{activeRoom?.name || '请选择直播间'}</div>
            </div>
            {activeRoom && (
              <span className="rounded-full bg-white/5 px-3 py-1 text-xs font-semibold text-slate-500">
                {activeRoom.channel}
              </span>
            )}
          </div>

          {activeRoom && (
            <div className="mb-4 grid gap-3 text-xs md:grid-cols-3">
              <div className="rounded-lg bg-white/5 p-3">
                <div className="text-slate-500">预算建议</div>
                <div className="mt-1 font-semibold text-white">{formatMoney(activeRoom.budget)}</div>
              </div>
              <div className="rounded-lg bg-white/5 p-3">
                <div className="text-slate-500">预估 ROAS</div>
                <div className="mt-1 font-semibold text-emerald-300">{activeRoom.roas}</div>
              </div>
              <div className="rounded-lg bg-white/5 p-3">
                <div className="text-slate-500">角色</div>
                <div className="mt-1 truncate font-semibold text-white">{activeRoom.role}</div>
              </div>
            </div>
          )}

          {planOptions.length > 0 && (
            <div className="grid gap-3 xl:grid-cols-3">
              {planOptions.map((plan) => (
                <button
                  key={plan.id}
                  type="button"
                  onClick={() => setSelectedPlan(plan.id)}
                  className={`relative rounded-lg border p-4 text-left transition ${
                    selectedPlan === plan.id
                      ? 'border-violet-500/70 bg-gradient-to-b from-violet-500/20 to-white/[0.025]'
                      : 'border-white/10 bg-white/[0.035] hover:border-white/20'
                  }`}
                >
                  {plan.recommended && <span className="absolute -top-2 right-3 rounded-full bg-violet-500 px-2 py-1 text-[10px] font-bold text-white">推荐</span>}
                  <div className="text-lg font-semibold text-white">{plan.title}</div>
                  <div className="mt-3 space-y-2 text-sm text-slate-400">
                    {plan.lines.map((line) => <div key={line}>· {line}</div>)}
                  </div>
                  <div className={`mt-4 flex h-9 items-center justify-center rounded-lg text-sm font-semibold ${
                    selectedPlan === plan.id ? 'bg-violet-500 text-white' : 'bg-white/5 text-slate-300'
                  }`}>
                    选择{plan.title}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );
}

const liveLoopStepFallback = [
  { id: 'signal', agent: '经营信号', status: 'idle', summary: '等待下一轮经营信号采集。' },
  { id: 'analysis', agent: '效果分析', status: 'idle', summary: '等待识别变化并归因。' },
  { id: 'planning', agent: '方案规划', status: 'idle', summary: '等待生成预算/人群调整策略。' },
  { id: 'orchestrator', agent: '调度中心', status: 'idle', summary: '等待校验经营目标与护栏。' },
  { id: 'delivery', agent: '投放执行', status: 'idle', summary: '等待执行或进入审批。' },
  { id: 'verification', agent: '效果验证', status: 'idle', summary: '等待验证效果并沉淀经验。' },
];

function loopStatusText(status) {
  return {
    idle: '待巡检',
    running: '运行中',
    pending_approval: '待审批',
    executed: '已执行',
    verifying: '验证中',
    completed: '已完成',
    rejected: '已拒绝',
  }[status] || status || '待巡检';
}

function loopStepClasses(status) {
  if (status === 'done') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700';
  if (status === 'waiting' || status === 'pending') return 'border-amber-500/30 bg-amber-500/10 text-amber-700';
  if (status === 'skipped') return 'border-slate-300 bg-slate-100 text-slate-500';
  return 'border-slate-200 bg-white/70 text-slate-500';
}

function LiveLoopPanel({
  liveLoop = agentModeFallback.live_loop,
  currentLiveFrame,
  acknowledgedAlerts = {},
  onAcknowledgeAlert,
}) {
  const steps = currentLiveFrame?.steps?.length
    ? currentLiveFrame.steps
    : liveLoop?.steps?.length
      ? liveLoop.steps
      : liveLoopStepFallback;
  const activeAlert = (currentLiveFrame?.alerts || []).find((alert) => !acknowledgedAlerts[alert.id]);
  const verification = liveLoop?.verification;

  return (
    <GlassCard className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Activity className="h-4 w-4 text-violet-300" />
            持续策略与执行闭环
          </div>
          <p className="mt-1 text-xs text-slate-500">效果变化识别 → 策略生成 → 护栏校验 → 执行/审批 → 验证回写</p>
        </div>
      </div>

      <div className="grid grid-cols-6 gap-2">
        {steps.map((step, index) => (
          <div key={step.id || index} className={`rounded-lg border p-3 ${loopStepClasses(step.status)}`}>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[11px] font-semibold">{String(index + 1).padStart(2, '0')}</span>
              {step.status === 'done' && <CheckCircle2 className="h-4 w-4" />}
              {(step.status === 'waiting' || step.status === 'pending') && <Loader2 className="h-4 w-4 animate-spin" />}
            </div>
            <div className="text-sm font-semibold text-slate-900">{step.agent}</div>
            <p className="mt-2 line-clamp-3 text-xs leading-5 text-slate-500">{step.summary}</p>
          </div>
        ))}
      </div>

      {activeAlert && (
        <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
          <div className="mb-2 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-amber-200">
              <AlertTriangle className="h-4 w-4" />
              {activeAlert.title || '自动预警'}
            </div>
            <span className="rounded-full bg-amber-500/15 px-2 py-1 text-[11px] font-semibold text-amber-700">
              {activeAlert.severity === 'critical' ? '需要人工审批' : '建议确认'}
            </span>
          </div>
          <div className="grid gap-3 text-sm md:grid-cols-[1fr_1.1fr]">
            <p className="rounded-lg bg-white/50 p-3 leading-6 text-slate-700">{activeAlert.message}</p>
            <p className="rounded-lg bg-white/50 p-3 leading-6 text-slate-700">{activeAlert.recommendation}</p>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            {(activeAlert.actions || ['同意建议', '暂不调整']).map((action, index) => (
              <button
                key={action}
                type="button"
                onClick={() => onAcknowledgeAlert(activeAlert.id, action)}
                className={`h-9 rounded-lg px-4 text-sm font-semibold ${
                  index === 0
                    ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                    : 'border border-white/10 bg-white/60 text-slate-700 hover:bg-white'
                }`}
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      )}

      {verification && (
        <div className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
            <CheckCircle2 className="h-4 w-4" />
            验证结果
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-700">{verification.summary}</p>
          <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
            <div className="rounded-lg bg-white/60 p-2"><span className="text-slate-500">ROAS</span><b className="ml-2 text-emerald-700">{verification.roas_delta}</b></div>
            <div className="rounded-lg bg-white/60 p-2"><span className="text-slate-500">毛利</span><b className="ml-2 text-emerald-700">{verification.profit_delta}</b></div>
            <div className="rounded-lg bg-white/60 p-2"><span className="text-slate-500">下一步</span><b className="ml-2 text-slate-700">继续观察</b></div>
          </div>
        </div>
      )}
    </GlassCard>
  );
}

function LiveCanvas({
  metrics,
  totalBudget,
  usedBudget,
  liveLoop = agentModeFallback.live_loop,
  currentLiveFrame,
  liveDemoEvents = [],
  liveDemoPlaying,
  onToggleLiveDemo,
  acknowledgedAlerts,
  onAcknowledgeAlert,
  focusMode,
  onToggleFocus,
}) {
  const frameMetrics = currentLiveFrame?.metrics || {};
  const liveSpend = Number(frameMetrics.spend ?? usedBudget ?? 0);
  const liveRevenue = Number(frameMetrics.revenue ?? metrics?.total_gmv ?? 0);
  const liveProfit = Number(frameMetrics.profit ?? Math.round(liveRevenue * 0.55));
  const liveRoas = Number(frameMetrics.roas ?? (liveSpend ? liveRevenue / liveSpend : 0));
  const liveCpa = Number(frameMetrics.cpa ?? 0);
  const liveInventory = Number(frameMetrics.inventory ?? 0);
  const budgetPool = currentLiveFrame?.budget_pool?.length
    ? currentLiveFrame.budget_pool
    : [
      { id: 'tiktok', label: 'TikTok Ads', spent: 0, total: Math.round(totalBudget * 0.5), tone: 'cyan' },
      { id: 'meta', label: 'Meta Ads', spent: 0, total: Math.round(totalBudget * 0.35), tone: 'violet' },
      { id: 'reserve', label: '直播间尾场保留', spent: 0, total: Math.round(totalBudget * 0.15), tone: 'amber' },
    ];
  const skuAds = currentLiveFrame?.sku_ads || [];
  const activeAlert = (currentLiveFrame?.alerts || []).find((alert) => !acknowledgedAlerts[alert.id]);
  const recentEvent = liveDemoEvents[liveDemoEvents.length - 1];

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">直播托管控制台</h1>
          <p className="mt-2 text-sm text-slate-500">投放执行中 · 数据按时间推进 · 预算不足或 ROI 异常自动预警</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onToggleLiveDemo}
            className="flex h-9 items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 text-xs font-semibold text-emerald-700"
          >
            {liveDemoPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            {liveDemoPlaying ? '直播中' : '已暂停'} {currentLiveFrame?.elapsed || '00:00:00'}
          </button>
          <FocusModeButton focusMode={focusMode} onToggleFocus={onToggleFocus} />
        </div>
      </div>

      <div className="grid grid-cols-5 gap-3">
        <MetricPill label="收入" value={formatMoney(liveRevenue)} delta={liveRevenue ? '+动态' : '待启动'} tone="emerald" icon={CircleDollarSign} />
        <MetricPill label="毛利润" value={formatMoney(liveProfit)} delta={liveProfit ? '+实时' : '待启动'} tone="cyan" icon={Wallet} />
        <MetricPill label="实时 ROAS" value={liveRoas ? liveRoas.toFixed(1) : '0.0'} delta={liveRoas >= 3 ? '达标' : '预警'} tone={liveRoas >= 3 ? 'violet' : 'amber'} icon={Gauge} />
        <MetricPill label="CPA" value={liveCpa ? formatMoney(liveCpa) : '$0'} delta={liveCpa && liveCpa <= 9 ? '健康' : '关注'} tone={liveCpa && liveCpa <= 9 ? 'emerald' : 'amber'} icon={Target} />
        <MetricPill label="库存" value={`${liveInventory || 0} 件`} delta={liveInventory > 850 ? '安全' : '紧张'} tone={liveInventory > 850 ? 'emerald' : 'amber'} icon={Database} />
      </div>

      <GlassCard className="p-5">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
          <Wallet className="h-4 w-4 text-violet-300" />
          统一预算池
        </div>
        <div className="grid grid-cols-[1.2fr_0.8fr] gap-6">
          <div className="space-y-4">
            {budgetPool.map((item) => (
              <BudgetBar key={item.id || item.label} label={item.label} spent={item.spent} total={item.total} tone={item.tone} />
            ))}
            <div className="flex justify-between border-t border-white/10 pt-3 text-xs text-slate-500">
              <span>已消耗 {formatMoney(liveSpend)} · 余额 <b className={totalBudget - liveSpend > 900 ? 'text-emerald-300' : 'text-amber-500'}>{formatMoney(Math.max(0, totalBudget - liveSpend))}</b></span>
              <span>总预算 {formatMoney(totalBudget)}</span>
            </div>
          </div>
          <div className={`rounded-lg border p-4 ${activeAlert ? 'border-amber-500/30 bg-amber-500/10' : 'border-emerald-500/30 bg-emerald-500/10'}`}>
            <div className={`mb-2 flex items-center gap-2 text-sm font-semibold ${activeAlert ? 'text-amber-700' : 'text-emerald-700'}`}>
              {activeAlert ? <AlertTriangle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
              {activeAlert ? '自动预警' : '当前托管动作'}
            </div>
            <p className="text-sm leading-6 text-slate-700">
              {activeAlert
                ? `${activeAlert.message} ${activeAlert.recommendation}`
                : recentEvent?.text || '系统正在持续观察经营信号，预算池会随时间推进。'}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {activeAlert ? (activeAlert.actions || ['同意建议', '暂不调整']).map((action, index) => (
                <button
                  key={action}
                  type="button"
                  onClick={() => onAcknowledgeAlert(activeAlert.id, action)}
                  className={`h-9 rounded-lg px-4 text-sm font-semibold ${
                    index === 0 ? 'bg-emerald-500 text-white' : 'border border-white/10 bg-white/60 text-slate-700'
                  }`}
                >
                  {action}
                </button>
              )) : (
                <span className="rounded-full bg-white/60 px-3 py-1 text-xs font-semibold text-slate-600">{currentLiveFrame?.state_label || '自动托管中'}</span>
              )}
            </div>
          </div>
        </div>
      </GlassCard>

      <LiveLoopPanel
        liveLoop={liveLoop}
        currentLiveFrame={currentLiveFrame}
        acknowledgedAlerts={acknowledgedAlerts}
        onAcknowledgeAlert={onAcknowledgeAlert}
      />

      <div className="grid grid-cols-2 gap-4">
        <GlassCard className="p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
            <Activity className="h-4 w-4 text-cyan-300" />
            事件时间线
          </div>
          <div className="space-y-4 text-sm">
            {liveDemoEvents.map((event, index) => (
              <div key={`${event.time}-${event.agent}-${index}`} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <StatusDot tone={event.tone} pulse={false} />
                  <span className="mt-2 h-full w-px bg-white/10" />
                </div>
                <div>
                  <div className="flex gap-2 text-xs">
                    <span className="text-slate-500">{event.time}</span>
                    <span className={toneClass(event.tone).split(' ')[1]}>{event.agent}</span>
                  </div>
                  <div className="mt-1 text-slate-300">{event.text}</div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
            <FileCheck2 className="h-4 w-4 text-emerald-300" />
            商品 SKU 投放
          </div>
          <div className="space-y-3">
            {skuAds.map((sku) => (
              <div key={sku.id || sku.sku} className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.035] p-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-violet-300">
                  <Layers3 className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-semibold text-white">{sku.name}</div>
                  <div className="mt-1 text-xs text-slate-500">{sku.sku} · ROI {Number(sku.roi || 0).toFixed(1)} · GMV {formatMoney(sku.gmv || 0)} · {sku.units || 0} 件</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-white">{formatMoney(sku.spend || 0)}</div>
                  <div className="mt-1 text-xs text-slate-500">{sku.status}</div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

function LeadsCanvas({ leadRows = [] }) {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      <div>
        <h1 className="text-2xl font-semibold text-white">线索中心</h1>
        <p className="mt-2 text-sm text-slate-500">线索模块实时建档 · 线索质量进入预算判断，但不直接触发大额调仓</p>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <MetricPill label="有效线索" value="148" delta="+22" tone="emerald" icon={Users} />
        <MetricPill label="意向率" value="31%" delta="+4%" tone="cyan" icon={Compass} />
        <MetricPill label="有效线索成本" value="$3.1" delta="-8%" tone="emerald" icon={CircleDollarSign} />
        <MetricPill label="线索成交率" value="18%" delta="达标" tone="violet" icon={CheckCircle2} />
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <GlassCard className="overflow-hidden">
          <div className="flex items-center gap-2 border-b border-white/10 px-5 py-4 text-sm font-semibold text-white">
            <Users className="h-4 w-4 text-cyan-300" />
            线索档案
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white/[0.035] text-xs text-slate-500">
                <tr>
                  <th className="px-5 py-3 text-left">用户</th>
                  <th className="py-3 text-left">来源渠道</th>
                  <th className="py-3 text-left">意向分</th>
                  <th className="py-3 text-left">最近互动</th>
                  <th className="py-3 text-left">跟进状态</th>
                  <th className="px-5 py-3 text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {leadRows.map((lead) => (
                  <tr key={lead.user} className="border-t border-white/5 text-slate-300">
                    <td className="px-5 py-4 font-semibold text-white">{lead.user}</td>
                    <td className={lead.channel === 'Meta' ? 'text-violet-300' : 'text-cyan-300'}>{lead.channel}</td>
                    <td className={lead.score >= 80 ? 'font-semibold text-emerald-300' : 'font-semibold text-amber-300'}>{lead.score}</td>
                    <td>{lead.action}</td>
                    <td><span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs">{lead.status}</span></td>
                    <td className="px-5 text-right text-violet-300">回复 · 转人工</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="mb-4 text-sm font-semibold text-white">渠道质量分</div>
          <div className="space-y-4">
            <BudgetBar label="Meta" spent={82} total={100} tone="violet" />
            <BudgetBar label="TikTok" spent={61} total={100} tone="cyan" />
          </div>
          <p className="mt-5 text-xs leading-6 text-slate-500">质量分 = 短期投放效率 + 线索质量 + 利润贡献 + 数据可信度。经营信号汇总后输出给效果分析，影响预算判断。</p>
        </GlassCard>
      </div>
    </div>
  );
}

function ReviewCanvas({
  reviewBenchmarks = [],
  reviewActions = [],
  strategyNotes = [],
  leadRows = [],
  goal = {},
  totalBudget = 0,
  usedBudget = 0,
  currentLiveFrame,
  focusMode,
  onToggleFocus,
}) {
  const [reviewReportText, setReviewReportText] = useState('');
  const [reviewReportStreaming, setReviewReportStreaming] = useState(false);
  const [reviewReportError, setReviewReportError] = useState('');
  const apiAudit = [
    { endpoint: '/api/agent-mode/workbench', usage: '读取 live_demo、线索资产、托管动作和复盘基线。' },
    { endpoint: '/api/metrics/realtime', usage: '读取实时消耗、GMV、ROI 与库存摘要。' },
    { endpoint: '/api/metrics/trend?hours=24', usage: '读取投放趋势，校验调仓前后的变化。' },
    { endpoint: '/api/campaigns', usage: '读取在线计划和 SKU 维度投放消耗。' },
    { endpoint: '/api/orchestrator/chat', usage: '触发方案生成、审批回写和下一场策略草案。' },
  ];
  const highIntentLeads = leadRows.filter((lead) => Number(lead.score || 0) >= 80);
  const generateReviewReport = async () => {
    if (reviewReportStreaming) return;
    setReviewReportText('');
    setReviewReportError('');
    setReviewReportStreaming(true);

    const reportContext = {
      project: goal,
      budget: { total: totalBudget, used: usedBudget },
      final_frame: currentLiveFrame,
      api_trace: apiAudit,
      benchmarks: reviewBenchmarks,
      key_actions: reviewActions,
      strategy_notes: strategyNotes,
      lead_assets: leadRows,
    };
    const prompt = [
      '请生成一份面向广告主的盘后复盘报告，用中文输出。',
      '报告必须覆盖：API 调用链、关键动作、策略更新、线索资产、相对固定预算的增量效果，以及下一场建议。',
      '请避免营销口吻，直接说明数据证据、动作原因和可复用策略。',
      `工作台数据：${JSON.stringify(reportContext)}`,
    ].join('\n');

    try {
      await api.chatWithOrchestrator(
        [{ role: 'user', content: prompt }],
        {
          onMessage: (chunk) => {
            setReviewReportText((current) => `${current}${chunk}`);
          },
          onError: (error) => {
            setReviewReportError(error || '复盘报告生成失败');
            setReviewReportStreaming(false);
          },
          onDone: () => {
            setReviewReportStreaming(false);
          },
        },
      );
    } catch (error) {
      setReviewReportError(error?.message || '复盘报告生成失败');
      setReviewReportStreaming(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">盘后迭代</h1>
          <p className="mt-2 text-sm text-slate-500">复盘模块输出 · 数据资产归档 · 写入下一场策略记忆</p>
        </div>
        <div className="flex gap-2">
          <button type="button" className="flex h-10 items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 text-sm font-semibold text-slate-300">
            <ClipboardCheck className="h-4 w-4" />
            导出复盘
          </button>
          <FocusModeButton focusMode={focusMode} onToggleFocus={onToggleFocus} />
        </div>
      </div>

      <GlassCard className="p-5">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
          <GitCompare className="h-4 w-4 text-violet-300" />
          相对固定预算基线的增量
        </div>
        <div className="grid grid-cols-3 gap-4">
          {reviewBenchmarks.map((benchmark) => (
            <div key={benchmark.title} className={`rounded-lg border p-4 ${benchmark.highlight ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-white/10 bg-white/[0.035]'}`}>
              <div className="text-xs text-slate-500">{benchmark.title}</div>
              <div className="mt-3 text-xl font-semibold text-white">{benchmark.line1}</div>
              <div className="mt-2 text-sm text-slate-300">{benchmark.line2}</div>
              <div className={benchmark.highlight ? 'mt-3 text-sm font-semibold text-emerald-300' : 'mt-3 text-sm text-slate-500'}>{benchmark.line3}</div>
            </div>
          ))}
        </div>
      </GlassCard>

      <GlassCard className="p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Database className="h-4 w-4 text-violet-300" />
            数据资产
          </div>
          <span className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-semibold text-violet-700">线索资产已并入复盘</span>
        </div>
        <div className="grid grid-cols-[1fr_320px] gap-4">
          <div className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.035]">
            <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3 text-sm font-semibold text-white">
              <Users className="h-4 w-4 text-cyan-300" />
              线索资产
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-white/[0.035] text-xs text-slate-500">
                  <tr>
                    <th className="px-4 py-3 text-left">用户</th>
                    <th className="py-3 text-left">渠道</th>
                    <th className="py-3 text-left">意向分</th>
                    <th className="py-3 text-left">互动</th>
                    <th className="px-4 py-3 text-right">状态</th>
                  </tr>
                </thead>
                <tbody>
                  {leadRows.map((lead) => (
                    <tr key={lead.user} className="border-t border-white/5 text-slate-300">
                      <td className="px-4 py-3 font-semibold text-white">{lead.user}</td>
                      <td className={lead.channel === 'Meta' ? 'text-violet-300' : 'text-cyan-300'}>{lead.channel}</td>
                      <td className={lead.score >= 80 ? 'font-semibold text-emerald-300' : 'font-semibold text-amber-300'}>{lead.score}</td>
                      <td>{lead.action}</td>
                      <td className="px-4 text-right"><span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs">{lead.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
            <div className="text-sm font-semibold text-white">线索质量摘要</div>
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-white/60 p-3">
                <div className="text-slate-500">有效线索</div>
                <div className="mt-1 text-lg font-semibold text-slate-900">{leadRows.length}</div>
              </div>
              <div className="rounded-lg bg-white/60 p-3">
                <div className="text-slate-500">高意向</div>
                <div className="mt-1 text-lg font-semibold text-emerald-700">{highIntentLeads.length}</div>
              </div>
              <div className="rounded-lg bg-white/60 p-3">
                <div className="text-slate-500">Meta 线索</div>
                <div className="mt-1 text-lg font-semibold text-violet-700">{leadRows.filter((lead) => lead.channel === 'Meta').length}</div>
              </div>
              <div className="rounded-lg bg-white/60 p-3">
                <div className="text-slate-500">TikTok 线索</div>
                <div className="mt-1 text-lg font-semibold text-cyan-700">{leadRows.filter((lead) => lead.channel === 'TikTok').length}</div>
              </div>
            </div>
            <p className="mt-4 text-xs leading-6 text-slate-500">线索资产会进入复盘报告，用来解释预算调仓是否带来更高质量的评论、加购和私信。</p>
          </div>
        </div>
      </GlassCard>

      <div className="grid grid-cols-2 gap-4">
        <GlassCard className="p-5">
          <div className="mb-4 text-sm font-semibold text-white">关键动作回顾</div>
          <div className="space-y-3">
            {reviewActions.map((item) => (
              <div key={`${item.time}-${item.action}`} className="grid grid-cols-[56px_1fr_88px_48px] items-center gap-3 rounded-lg border border-white/10 bg-white/[0.035] p-3 text-sm">
                <span className="text-slate-500">{item.time}</span>
                <span className="text-slate-200">{item.action}</span>
                <span className={item.type === '审批' ? 'font-semibold text-amber-300' : 'font-semibold text-emerald-300'}>{item.result}</span>
                <span className="text-xs text-slate-500">{item.type}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
            <Wand2 className="h-4 w-4 text-cyan-300" />
            策略学习
          </div>
          <ul className="space-y-3 text-sm leading-6 text-slate-300">
            {strategyNotes.map((note) => (
              <li key={note}>· {note}</li>
            ))}
          </ul>
          <button
            type="button"
            onClick={generateReviewReport}
            disabled={reviewReportStreaming}
            className="mt-5 flex h-10 items-center gap-2 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70"
          >
            {reviewReportStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
            {reviewReportStreaming ? '正在生成复盘报告' : '基于本场生成下一场草案'}
          </button>
        </GlassCard>
      </div>

      {(reviewReportStreaming || reviewReportText || reviewReportError) && (
        <GlassCard className="p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                {reviewReportStreaming ? <Loader2 className="h-4 w-4 animate-spin text-violet-300" /> : <FileCheck2 className="h-4 w-4 text-emerald-300" />}
                AI 复盘报告
              </div>
              <p className="mt-1 text-xs text-slate-500">通过 /api/orchestrator/chat 流式生成，数据来自当前预算项目、直播帧、动作和线索资产。</p>
            </div>
            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700">
              {reviewReportStreaming ? '生成中' : '可用于下一场草案'}
            </span>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
            {reviewReportError ? (
              <div className="text-sm leading-6 text-rose-600">{reviewReportError}</div>
            ) : (
              <div className="whitespace-pre-wrap text-sm leading-7 text-slate-700">
                {reviewReportText || '正在调用模型整理复盘报告...'}
                {reviewReportStreaming && <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded bg-violet-400 align-middle" />}
              </div>
            )}
          </div>
        </GlassCard>
      )}
    </div>
  );
}

function MainCanvas(props) {
  return (
    <main className="flex min-w-0 flex-1 flex-col bg-[#070b13]">
      <section className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        {props.activeStage === 'plan' && (
          <PlanCanvas
            goal={props.goal}
            selectedRoomId={props.selectedRoomId}
            setSelectedRoomId={props.setSelectedRoomId}
            selectedPlan={props.selectedPlan}
            setSelectedPlan={props.setSelectedPlan}
            guardLimit={props.guardLimit}
            onGuardLimitChange={props.onGuardLimitChange}
            approvalThreshold={props.approvalThreshold}
            onApprovalThresholdChange={props.onApprovalThresholdChange}
            onStartManagedDelivery={props.onStartManagedDelivery}
            liveRooms={props.liveRooms}
            planOptions={props.planOptions}
            disabledActions={props.disabledActions}
            phase={props.phase}
            briefFields={props.briefFields}
            focusMode={props.focusMode}
            onToggleFocus={props.onToggleFocus}
          />
        )}
        {props.activeStage === 'live' && (
          <LiveCanvas
            metrics={props.metrics}
            totalBudget={props.totalBudget}
            usedBudget={props.usedBudget}
            liveLoop={props.liveLoop}
            currentLiveFrame={props.currentLiveFrame}
            liveDemoEvents={props.liveDemoEvents}
            liveDemoPlaying={props.liveDemoPlaying}
            onToggleLiveDemo={props.onToggleLiveDemo}
            acknowledgedAlerts={props.acknowledgedAlerts}
            onAcknowledgeAlert={props.onAcknowledgeAlert}
            focusMode={props.focusMode}
            onToggleFocus={props.onToggleFocus}
          />
        )}
        {props.activeStage === 'review' && (
          <ReviewCanvas
            reviewBenchmarks={props.reviewBenchmarks}
            reviewActions={props.reviewActions}
            strategyNotes={props.strategyNotes}
            leadRows={props.leadRows}
            goal={props.goal}
            totalBudget={props.totalBudget}
            usedBudget={props.usedBudget}
            currentLiveFrame={props.currentLiveFrame}
            focusMode={props.focusMode}
            onToggleFocus={props.onToggleFocus}
          />
        )}
      </section>
    </main>
  );
}

function DropdownShell({ open, children }) {
  if (!open) return null;
  return (
    <div className="absolute bottom-11 right-0 z-30 max-h-80 w-72 overflow-y-auto rounded-lg border border-white/10 bg-[#111827] p-2 shadow-2xl shadow-black/40">
      {children}
    </div>
  );
}

function ModelMenu({ models, selectedModels, onToggleModel, open, onToggleOpen }) {
  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggleOpen}
        className="flex h-9 items-center gap-2 rounded-lg border border-white/10 bg-white/[0.035] px-3 text-xs font-semibold text-slate-200 hover:bg-white/10"
      >
        <Zap className="h-3.5 w-3.5 text-violet-300" />
        {selectedModels[0] || 'gpt-5'}
        <ChevronRight className={`h-3.5 w-3.5 transition ${open ? 'rotate-90' : ''}`} />
      </button>
      <DropdownShell open={open}>
        <div className="px-2 pb-2 text-xs font-semibold uppercase tracking-normal text-slate-500">Models</div>
        <div className="space-y-1">
          {models.slice(0, 24).map((model) => {
            const checked = selectedModels.includes(model.id);
            return (
              <label key={model.id} className="flex cursor-pointer items-start gap-2 rounded-lg px-2 py-2 hover:bg-white/5">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onToggleModel(model.id)}
                  className="mt-0.5 accent-violet-500"
                />
                <span className="min-w-0">
                  <span className="block truncate text-xs font-semibold text-slate-200">{model.label || model.id}</span>
                  <span className="text-[11px] text-slate-500">{model.provider || 'Qiji'}{model.enabled_by_default ? ' · 默认' : ''}</span>
                </span>
              </label>
            );
          })}
        </div>
      </DropdownShell>
    </div>
  );
}

function DataSourceMenu({ dataSources, enabledDataSources, onToggleSource, open, onToggleOpen }) {
  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggleOpen}
        className="flex h-9 items-center gap-2 rounded-lg border border-white/10 bg-white/[0.035] px-3 text-xs font-semibold text-slate-200 hover:bg-white/10"
      >
        <ShieldCheck className="h-3.5 w-3.5 text-amber-300" />
        完全访问
        <ChevronRight className={`h-3.5 w-3.5 transition ${open ? 'rotate-90' : ''}`} />
      </button>
      <DropdownShell open={open}>
        <div className="px-2 pb-2 text-xs font-semibold uppercase tracking-normal text-slate-500">数据源</div>
        <div className="space-y-1">
          {dataSources.map((source) => (
            <label key={source.id} className="flex cursor-pointer items-start gap-2 rounded-lg px-2 py-2 hover:bg-white/5">
              <input
                type="checkbox"
                checked={enabledDataSources.includes(source.id)}
                onChange={() => onToggleSource(source.id)}
                className="mt-0.5 accent-violet-500"
              />
              <span className="min-w-0">
                <span className="block truncate text-xs font-semibold text-slate-200">{source.label}</span>
                <span className="text-[11px] text-slate-500">{source.description || source.id}</span>
              </span>
            </label>
          ))}
        </div>
      </DropdownShell>
    </div>
  );
}

function BudgetSummary({ totalBudget, usedBudget, selectedPlan, selectedRoom }) {
  const pct = Math.min(100, Math.round((usedBudget / totalBudget) * 100));
  const planLabel = { steady: '保守', balanced: '均衡', aggressive: '进取' }[selectedPlan] || '均衡';
  return (
    <GlassCard className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Wallet className="h-4 w-4 text-violet-300" />
          预算与目标
        </div>
        <span className="rounded-full bg-emerald-500/15 px-2 py-1 text-xs font-semibold text-emerald-300">在线</span>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs text-slate-500">已消耗比例</div>
          <div className="mt-1 text-2xl font-semibold text-white">{pct}%</div>
        </div>
        <div className="text-right text-xs text-slate-500">
          <div>总预算 {formatMoney(totalBudget)}</div>
          <div className="mt-1 text-amber-300">已消耗 {formatMoney(usedBudget)}</div>
        </div>
      </div>
      <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-400" style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-white/5 p-2">
          <div className="text-slate-500">当前 Plan</div>
          <div className="mt-1 font-semibold text-white">{planLabel}</div>
        </div>
        <div className="rounded-lg bg-white/5 p-2">
          <div className="text-slate-500">主直播间</div>
          <div className="mt-1 truncate font-semibold text-white">{selectedRoom?.name?.replace('直播间 ', '')}</div>
        </div>
      </div>
      <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.035] p-3 text-xs leading-5 text-slate-400">
        目标：ROAS ≥ 3.0 · 毛利优先 · 不超总预算 · 自动动作受护栏约束。
      </div>
    </GlassCard>
  );
}

function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[86%] rounded-lg px-3 py-2 text-sm leading-6 ${
        isUser
          ? 'bg-violet-600 text-white'
          : 'border border-white/10 bg-white/[0.055] text-slate-200'
      }`}>
        {message.content || (message.streaming ? '正在思考...' : '')}
        {message.streaming && <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded bg-violet-300 align-middle" />}
      </div>
    </div>
  );
}

function RightPanel({
  collapsed,
  onToggleCollapsed,
  totalBudget,
  usedBudget,
  selectedPlan,
  selectedRoom,
  chatMessages,
  input,
  setInput,
  isStreaming,
  sendMessage,
  models,
  selectedModels,
  toggleModel,
  modelOpen,
  setModelOpen,
  dataSources,
  enabledDataSources,
  toggleDataSource,
  accessOpen,
  setAccessOpen,
  rightPanelWidth,
  onResizePointerDown,
}) {
  if (collapsed) {
    return (
      <aside className="flex h-[calc(100vh-4rem)] w-16 shrink-0 flex-col items-center border-l border-white/10 bg-[#0d1320] py-4">
        <button
          type="button"
          onClick={onToggleCollapsed}
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/[0.035] text-slate-300 hover:bg-white/10"
          aria-label="展开右侧栏"
          title="展开右侧栏"
        >
          <MessageSquareText className="h-5 w-5" />
        </button>
        <div className="mt-6 flex flex-col gap-3">
          <Wallet className="h-5 w-5 text-violet-300" />
          <Bot className="h-5 w-5 text-cyan-300" />
          <Send className="h-5 w-5 text-emerald-300" />
        </div>
      </aside>
    );
  }

  return (
    <aside
      className="relative flex h-[calc(100vh-4rem)] shrink-0 flex-col border-l border-white/10 bg-[#0d1320]"
      style={{ width: rightPanelWidth, minWidth: 320, maxWidth: 560 }}
    >
      <div
        role="separator"
        aria-label="拖动调整右侧栏宽度"
        title="拖动调整右侧栏宽度"
        onPointerDown={onResizePointerDown}
        className="absolute left-[-3px] top-0 z-30 h-full w-2 cursor-col-resize touch-none bg-transparent transition hover:bg-violet-400/40"
      />
      <div className="flex h-14 items-center justify-between border-b border-white/10 px-4">
        <div className="flex items-center gap-2">
          <MessageSquareText className="h-4 w-4 text-violet-300" />
          <span className="font-semibold text-white">托管顾问</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-white/5 hover:text-white"
            aria-label="收起右侧栏"
            title="收起右侧栏"
          >
            <PanelRightClose className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <BudgetSummary totalBudget={totalBudget} usedBudget={usedBudget} selectedPlan={selectedPlan} selectedRoom={selectedRoom} />

        <div className="mt-4 flex min-h-[420px] flex-col overflow-hidden rounded-lg border border-white/10 bg-white/[0.035]">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <div>
              <div className="text-sm font-semibold text-white">投放顾问</div>
              <div className="mt-0.5 text-xs text-slate-500">可调整预算、目标、护栏并生成 plan</div>
            </div>
            <RefreshCw className="h-4 w-4 text-slate-500" />
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {chatMessages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </div>

          <div className="border-t border-white/10 p-3">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
              className="h-20 w-full resize-none rounded-lg border border-white/10 bg-[#0b111c] px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-600"
              placeholder="询问预算、修改目标、生成 plan..."
            />
            <div className="mt-2 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DataSourceMenu
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
                <button type="button" className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-white/5" aria-label="语音">
                  <Mic className="h-4 w-4" />
                </button>
                <button type="button" className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-white/5" aria-label="附件">
                  <Paperclip className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={sendMessage}
                  disabled={isStreaming || !input.trim()}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-600 text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:bg-slate-700"
                  aria-label="发送"
                >
                  {isStreaming ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowUp className="h-5 w-5" />}
                </button>
              </div>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setInput('我要给便携榨汁杯做一场美国市场直播，预算 5000 美元，目标 ROAS 3.0')}
          className="mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 text-sm font-semibold text-white shadow-lg shadow-violet-950/40"
        >
          <Sparkles className="h-4 w-4" />
          快速开始（示例）
        </button>
      </div>
    </aside>
  );
}

export default function AgentModePage() {
  const [wb, dispatch] = useReducer(workbenchReducer, agentModeFallback, mergeWorkbench);

  const [activeStage, setActiveStage] = useState('plan');
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [theme, setTheme] = useState('light');
  const [leftPanelWidth, setLeftPanelWidth] = useState(agentModeFallback.layout.left_panel_width);
  const [rightPanelWidth, setRightPanelWidth] = useState(agentModeFallback.layout.right_panel_width);
  const [models, setModels] = useState(fallbackModels);
  const [selectedModels, setSelectedModels] = useState(['gpt-5']);
  const [dataSources, setDataSources] = useState(fallbackDataSources);
  const [enabledDataSources, setEnabledDataSources] = useState(fallbackDataSources.map((s) => s.id));
  const [metrics, setMetrics] = useState(null);
  const [trendData, setTrendData] = useState(agentModeFallback.default_trend);
  const [campaigns, setCampaigns] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [modelOpen, setModelOpen] = useState(false);
  const [accessOpen, setAccessOpen] = useState(false);
  const [liveDemoIndex, setLiveDemoIndex] = useState(0);
  const [liveDemoPlaying, setLiveDemoPlaying] = useState(true);
  const [acknowledgedAlerts, setAcknowledgedAlerts] = useState({});
  const [chatMessages, setChatMessages] = useState([
    { id: 'welcome', role: 'assistant', content: agentModeFallback.chat_welcome },
  ]);
  const chatEndRef = useRef(null);
  const approvalPauseRef = useRef(false);

  const goal = wb.project;
  const selectedRoomId = wb.selected_room_id;
  const selectedPlan = wb.selected_plan;
  const guardLimit = wb.guard_limit;
  const approvalThreshold = wb.approval_threshold;
  const phase = wb.phase || 'briefing';
  const briefFields = wb.brief_fields || {};

  useEffect(() => {
    async function loadConfig() {
      try {
        const [modelsResponse, dataSourcesResponse] = await Promise.all([
          api.getAgentModels(),
          api.getAgentDataSources(),
        ]);
        const nextModels = modelsResponse.models?.length ? modelsResponse.models : fallbackModels;
        const nextSources = dataSourcesResponse.data_sources?.length ? dataSourcesResponse.data_sources : fallbackDataSources;
        setModels(nextModels);
        setSelectedModels(nextModels.filter((m) => m.enabled_by_default).map((m) => m.id));
        setDataSources(nextSources);
        setEnabledDataSources(dataSourcesResponse.default_enabled || nextSources.filter((s) => s.enabled_by_default).map((s) => s.id));
      } catch {
        setModels(fallbackModels);
        setDataSources(fallbackDataSources);
      }
    }

    async function loadBusinessData() {
      try {
        const [workbenchResponse, metricsResponse, trendResponse, campaignsResponse] = await Promise.all([
          api.getAgentModeWorkbench(),
          api.getRealtimeMetrics(),
          api.getMetricsTrend(24),
          api.getCampaigns(),
        ]);
        dispatch({ type: 'INIT', workbench: workbenchResponse });
        const wb = mergeWorkbench(workbenchResponse);
        setLeftPanelWidth(Number(wb.layout?.left_panel_width || agentModeFallback.layout.left_panel_width));
        setRightPanelWidth(Number(wb.layout?.right_panel_width || agentModeFallback.layout.right_panel_width));
        setChatMessages((current) =>
          current.length === 1 && current[0].id === 'welcome'
            ? [{ ...current[0], content: wb.chat_welcome || agentModeFallback.chat_welcome }]
            : current,
        );
        setMetrics(metricsResponse);
        setTrendData(Array.isArray(trendResponse) && trendResponse.length ? trendResponse : wb.default_trend);
        setCampaigns(Array.isArray(campaignsResponse) ? campaignsResponse : []);
      } catch {
        setTrendData(agentModeFallback.default_trend);
        setCampaigns([]);
      }
    }

    loadConfig();
    loadBusinessData();
  }, []);

  const currentLiveRooms = wb.live_rooms || [];
  const currentPlanOptions = wb.plan_options || [];
  const currentProcessSteps = wb.process_steps?.length ? wb.process_steps : agentModeFallback.process_steps;
  const currentLeadRows = wb.lead_rows?.length ? wb.lead_rows : agentModeFallback.lead_rows;
  const currentFallbackCampaigns = wb.fallback_campaigns?.length ? wb.fallback_campaigns : agentModeFallback.fallback_campaigns;
  const currentManagedEvents = wb.managed_events?.length ? wb.managed_events : agentModeFallback.managed_events;
  const currentLiveLoop = wb.live_loop || agentModeFallback.live_loop;
  const currentReviewBenchmarks = wb.review_benchmarks?.length ? wb.review_benchmarks : agentModeFallback.review_benchmarks;
  const currentReviewActions = wb.review_actions?.length ? wb.review_actions : agentModeFallback.review_actions;
  const currentStrategyNotes = wb.strategy_notes?.length ? wb.strategy_notes : agentModeFallback.strategy_notes;
  const currentDisabledActions = wb.disabled_actions?.length ? wb.disabled_actions : agentModeFallback.disabled_actions;
  const currentBudgetProjects = wb.budget_projects?.length ? wb.budget_projects : agentModeFallback.budget_projects;
  const currentAgentRoster = wb.agent_roster?.length ? wb.agent_roster : agentModeFallback.agent_roster;
  const activeBudgetProjectId = wb.active_project_id || null;
  const currentLiveDemo = wb.live_demo?.frames?.length ? wb.live_demo : agentModeFallback.live_demo;
  const liveDemoFrames = currentLiveDemo.frames || [];
  const liveDemoInterval = currentLiveDemo.tick_interval_ms || 1800;
  const currentLiveFrame = liveDemoFrames[liveDemoIndex] || liveDemoFrames[0] || null;
  const currentActiveAlert = useMemo(
    () => (currentLiveFrame?.alerts || []).find((alert) => !acknowledgedAlerts[alert.id]) || null,
    [currentLiveFrame, acknowledgedAlerts],
  );
  const liveDemoEvents = useMemo(
    () => liveDemoFrames.slice(0, liveDemoIndex + 1).flatMap((frame) => frame.events || []).slice(-8),
    [liveDemoFrames, liveDemoIndex],
  );

  useEffect(() => {
    if (activeStage === 'live' && liveDemoPlaying && currentActiveAlert) {
      approvalPauseRef.current = true;
      setLiveDemoPlaying(false);
    }
  }, [activeStage, liveDemoPlaying, currentActiveAlert]);

  useEffect(() => {
    if (activeStage !== 'live' || !liveDemoPlaying || liveDemoFrames.length <= 1) return undefined;
    const timer = window.setInterval(() => {
      setLiveDemoIndex((index) => (index + 1) % liveDemoFrames.length);
    }, liveDemoInterval);
    return () => window.clearInterval(timer);
  }, [activeStage, liveDemoPlaying, liveDemoFrames.length, liveDemoInterval]);

  const selectedRoom = useMemo(
    () => currentLiveRooms.find((r) => r.id === selectedRoomId) || currentLiveRooms[1] || currentLiveRooms[0] || {},
    [currentLiveRooms, selectedRoomId],
  );
  const totalBudget = parseMoneyValue(goal.totalBudgetValue || goal.totalBudget, 5000);
  const usedBudget = Math.min(totalBudget, Math.round(currentLiveFrame?.metrics?.spend ?? metrics?.total_cost ?? 0));

  const toggleModel = (modelId) => {
    setSelectedModels((c) => (c.includes(modelId) ? c.filter((id) => id !== modelId) : [...c, modelId]));
  };
  const toggleDataSource = (sourceId) => {
    setEnabledDataSources((c) => (c.includes(sourceId) ? c.filter((id) => id !== sourceId) : [...c, sourceId]));
  };

  const setSelectedRoomIdAction = useCallback((id) => dispatch({ type: 'SET_FIELD', field: 'selected_room_id', value: id }), []);
  const setSelectedPlanAction = useCallback((id) => dispatch({ type: 'SET_FIELD', field: 'selected_plan', value: id }), []);
  const onGuardLimitChange = useCallback((v) => dispatch({ type: 'SET_FIELD', field: 'guard_limit', value: v }), []);
  const onApprovalThresholdChange = useCallback((v) => dispatch({ type: 'SET_FIELD', field: 'approval_threshold', value: v }), []);

  const onStartManagedDelivery = () => {
    setActiveStage('live');
    dispatch({ type: 'PHASE_CHANGE', phase: 'live' });
    setChatMessages((c) => [...c, {
      id: `assistant-note-${Date.now()}`,
      role: 'assistant',
      content: '已批准并启动托管。投放执行模块将按护栏自动调仓；超过审批阈值的动作会进入人工审批。',
    }]);
  };

  const onReset = async () => {
    try {
      const response = await api.resetWorkbench();
      dispatch({ type: 'INIT', workbench: response.workbench });
      setActiveStage('plan');
      approvalPauseRef.current = false;
      setChatMessages([
        { id: 'welcome', role: 'assistant', content: response.workbench.chat_welcome || agentModeFallback.chat_welcome },
      ]);
    } catch {
      dispatch({ type: 'RESET' });
      setActiveStage('plan');
      approvalPauseRef.current = false;
      setChatMessages([
        { id: 'welcome', role: 'assistant', content: agentModeFallback.chat_welcome },
      ]);
    }
  };

  const onSelectBudgetProject = useCallback((projectId) => {
    const selectedProject = (currentBudgetProjects || []).find((project) => project.id === projectId);
    if (!selectedProject) return;

    dispatch({ type: 'SELECT_BUDGET_PROJECT', projectId });
    setLiveDemoIndex(0);
    setLiveDemoPlaying(false);
    approvalPauseRef.current = false;
    setAcknowledgedAlerts({});
    setActiveStage(selectedProject.workbench?.phase === 'review' ? 'review' : 'plan');
    setChatMessages([
      {
        id: `project-switch-${projectId}`,
        role: 'assistant',
        content: `已切换到历史预算项目「${selectedProject.name}」。你可以查看方案、直播托管过程和复盘数据。`,
      },
    ]);

    api.getAgentModeWorkbench(projectId)
      .then((response) => {
        if (response?.active_project_id === projectId) {
          dispatch({ type: 'INIT', workbench: response });
          setActiveStage(response.phase === 'review' ? 'review' : 'plan');
        }
      })
      .catch(() => {});

    api.updateAgentModeWorkbench({
      ...(selectedProject.workbench || {}),
      active_project_id: projectId,
    }).catch(() => {});
  }, [currentBudgetProjects]);

  const createResizePointerDown = (side) => (event) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = side === 'left' ? leftPanelWidth : rightPanelWidth;
    const setWidth = side === 'left' ? setLeftPanelWidth : setRightPanelWidth;
    const minWidth = side === 'left' ? 240 : 320;
    const maxWidth = side === 'left' ? 420 : 560;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    const handlePointerMove = (moveEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const direction = side === 'left' ? 1 : -1;
      setWidth(clamp(startWidth + deltaX * direction, minWidth, maxWidth));
    };
    const handlePointerUp = () => {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };
    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp, { once: true });
  };

  const runOrchestratorCommand = async (commandText, { echoUser = true } = {}) => {
    const text = String(commandText || '').trim();
    if (!text || isStreaming) return;

    const userMessage = { id: `user-${Date.now()}`, role: 'user', content: text };
    const assistantId = `assistant-${Date.now()}`;

    const apiMessages = [
      ...chatMessages
        .filter((m) => ['user', 'assistant'].includes(m.role))
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content })),
      { role: 'user', content: text },
    ];

    setInput('');
    setModelOpen(false);
    setAccessOpen(false);
    setIsStreaming(true);
    setChatMessages((c) => [
      ...c,
      ...(echoUser ? [userMessage] : []),
      { id: assistantId, role: 'assistant', content: '', streaming: true },
    ]);

    try {
      await api.chatWithOrchestrator(apiMessages, {
        onToolCall: (tool) => {
          setChatMessages((c) => c.map((m) =>
            m.id === assistantId && !m.content
              ? { ...m, content: `正在调用 ${tool}...\n\n` }
              : m,
          ));
        },
        onToolResult: () => {},
        onMessage: (chunk) => {
          setChatMessages((c) => c.map((m) =>
            m.id === assistantId
              ? { ...m, content: `${m.content}${chunk}` }
              : m,
          ));
        },
        onWorkbenchPatch: (patch) => {
          dispatch({ type: 'WORKBENCH_PATCH', patch });
        },
        onViewSwitch: (view) => {
          setActiveStage(view);
        },
        onPhaseChange: (newPhase) => {
          dispatch({ type: 'PHASE_CHANGE', phase: newPhase });
          if (newPhase === 'live') setActiveStage('live');
        },
        onAgentAction: (event) => {
          dispatch({ type: 'AGENT_ACTION', event });
        },
        onError: (error) => {
          setChatMessages((c) => c.map((m) =>
            m.id === assistantId
              ? { ...m, content: m.content ? `${m.content}\n\n${error}` : error, streaming: false }
              : m,
          ));
          setIsStreaming(false);
        },
        onDone: () => {
          setChatMessages((c) => c.map((m) =>
            m.id === assistantId ? { ...m, streaming: false } : m,
          ));
          setIsStreaming(false);
        },
      });
    } catch (error) {
      const message = error?.message || 'Orchestrator 请求失败';
      setChatMessages((c) => c.map((m) =>
        m.id === assistantId
          ? { ...m, content: m.content ? `${m.content}\n\n${message}` : message, streaming: false }
          : m,
      ));
      setIsStreaming(false);
    }
  };

  const sendMessage = async () => {
    await runOrchestratorCommand(input.trim());
  };

  const onToggleLiveDemo = useCallback(() => {
    setLiveDemoPlaying((current) => !current);
  }, []);

  const onAcknowledgeAlert = useCallback((alertId, action) => {
    if (!alertId) return;
    setAcknowledgedAlerts((current) => ({ ...current, [alertId]: action || true }));
    if (approvalPauseRef.current && activeStage === 'live') {
      approvalPauseRef.current = false;
      setLiveDemoPlaying(true);
    }
    setChatMessages((current) => [
      ...current,
      {
        id: `alert-ack-${alertId}-${Date.now()}`,
        role: 'assistant',
        content: `已记录你的选择：${action}。系统会继续按直播实时数据推进预算托管。`,
      },
    ]);
  }, [activeStage]);

  const canvasProps = {
    activeStage,
    setActiveStage,
    focusMode,
    onToggleFocus: () => setFocusMode((c) => !c),
    goal,
    selectedRoomId,
    setSelectedRoomId: setSelectedRoomIdAction,
    selectedPlan,
    setSelectedPlan: setSelectedPlanAction,
    guardLimit,
    onGuardLimitChange,
    approvalThreshold,
    onApprovalThresholdChange,
    onStartManagedDelivery,
    liveRooms: currentLiveRooms,
    planOptions: currentPlanOptions,
    processSteps: currentProcessSteps,
    leadRows: currentLeadRows,
    fallbackCampaigns: currentFallbackCampaigns,
    managedEvents: currentManagedEvents,
    liveLoop: currentLiveLoop,
    reviewBenchmarks: currentReviewBenchmarks,
    reviewActions: currentReviewActions,
    strategyNotes: currentStrategyNotes,
    disabledActions: currentDisabledActions,
    currentLiveFrame,
    liveDemoEvents,
    liveDemoPlaying,
    onToggleLiveDemo,
    acknowledgedAlerts,
    onAcknowledgeAlert,
    metrics,
    totalBudget,
    usedBudget,
    phase,
    briefFields,
  };
  const themeClass = theme === 'light' ? 'agent-mode-light' : 'agent-mode-dark';

  return (
    <div className={`agent-mode-shell ${themeClass} h-screen overflow-hidden bg-[#070b13] text-slate-100`}>
      <TopBar
        activeStage={activeStage}
        setActiveStage={setActiveStage}
        totalBudget={totalBudget}
        usedBudget={usedBudget}
        theme={theme}
        setTheme={setTheme}
        liveElapsed={currentLiveFrame?.elapsed || '00:00:00'}
      />
      <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
        {!focusMode && (
          <LeftPanel
            collapsed={leftCollapsed}
            onToggleCollapsed={() => setLeftCollapsed((c) => !c)}
            goal={goal}
            leftPanelWidth={leftPanelWidth}
            onResizePointerDown={createResizePointerDown('left')}
            onReset={onReset}
            agentRoster={currentAgentRoster}
            budgetProjects={currentBudgetProjects}
            activeBudgetProjectId={activeBudgetProjectId}
            onSelectBudgetProject={onSelectBudgetProject}
          />
        )}

        <MainCanvas {...canvasProps} />

        {!focusMode && (
          <RightPanel
            collapsed={rightCollapsed}
            onToggleCollapsed={() => setRightCollapsed((c) => !c)}
            totalBudget={totalBudget}
            usedBudget={usedBudget}
            selectedPlan={selectedPlan}
            selectedRoom={selectedRoom}
            chatMessages={chatMessages}
            input={input}
            setInput={setInput}
            isStreaming={isStreaming}
            sendMessage={sendMessage}
            models={models}
            selectedModels={selectedModels}
            toggleModel={toggleModel}
            modelOpen={modelOpen}
            setModelOpen={setModelOpen}
            dataSources={dataSources}
            enabledDataSources={enabledDataSources}
            toggleDataSource={toggleDataSource}
            accessOpen={accessOpen}
            setAccessOpen={setAccessOpen}
            rightPanelWidth={rightPanelWidth}
            onResizePointerDown={createResizePointerDown('right')}
          />
        )}
      </div>
    </div>
  );
}
