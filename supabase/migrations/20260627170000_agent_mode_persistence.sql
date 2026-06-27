create extension if not exists pgcrypto;

create table if not exists public.agent_budget_projects (
  id uuid primary key default gen_random_uuid(),
  tenant_key text not null default 'demo',
  name text not null,
  product text not null,
  market text not null,
  currency text not null default 'USD',
  budget numeric not null default 0,
  target_roas numeric not null default 0,
  channels jsonb not null default '[]'::jsonb,
  brief jsonb not null default '{}'::jsonb,
  status text not null default 'draft',
  active_plan_version_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_plan_versions (
  id uuid primary key default gen_random_uuid(),
  tenant_key text not null default 'demo',
  project_id uuid not null references public.agent_budget_projects(id) on delete cascade,
  version_number integer not null,
  selected_mode text not null default 'balanced',
  recommended_mode text not null default 'balanced',
  brief_snapshot jsonb not null default '{}'::jsonb,
  plan_options jsonb not null default '[]'::jsonb,
  channel_pools jsonb not null default '[]'::jsonb,
  guardrails jsonb not null default '{}'::jsonb,
  live_rooms jsonb not null default '[]'::jsonb,
  simulator_seed text,
  created_at timestamptz not null default now(),
  unique(project_id, version_number)
);

create table if not exists public.agent_project_skus (
  id uuid primary key default gen_random_uuid(),
  tenant_key text not null default 'demo',
  project_id uuid not null references public.agent_budget_projects(id) on delete cascade,
  plan_version_id uuid not null references public.agent_plan_versions(id) on delete cascade,
  sku_code text not null,
  name text not null,
  category text not null,
  price numeric not null,
  base_inventory integer not null,
  margin_rate numeric not null,
  attributes jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_live_frames (
  id uuid primary key default gen_random_uuid(),
  tenant_key text not null default 'demo',
  project_id uuid not null references public.agent_budget_projects(id) on delete cascade,
  plan_version_id uuid not null references public.agent_plan_versions(id) on delete cascade,
  frame_index integer not null,
  frame_time text not null,
  elapsed_seconds integer not null default 0,
  metrics jsonb not null default '{}'::jsonb,
  budget_pool jsonb not null default '[]'::jsonb,
  sku_ads jsonb not null default '[]'::jsonb,
  steps jsonb not null default '[]'::jsonb,
  alerts jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique(plan_version_id, frame_index)
);

create table if not exists public.agent_events (
  id uuid primary key default gen_random_uuid(),
  tenant_key text not null default 'demo',
  project_id uuid not null references public.agent_budget_projects(id) on delete cascade,
  plan_version_id uuid not null references public.agent_plan_versions(id) on delete cascade,
  frame_index integer,
  agent text not null,
  event_type text not null default 'signal',
  text text not null,
  tone text not null default 'cyan',
  action_id uuid,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_live_actions (
  id uuid primary key default gen_random_uuid(),
  tenant_key text not null default 'demo',
  project_id uuid not null references public.agent_budget_projects(id) on delete cascade,
  plan_version_id uuid not null references public.agent_plan_versions(id) on delete cascade,
  frame_index integer not null,
  type text not null,
  source text,
  target text,
  amount numeric not null default 0,
  reason text,
  expected_impact text,
  risk text,
  status text not null default 'recommended',
  decision text,
  decided_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_reviews (
  id uuid primary key default gen_random_uuid(),
  tenant_key text not null default 'demo',
  project_id uuid not null references public.agent_budget_projects(id) on delete cascade,
  plan_version_id uuid not null references public.agent_plan_versions(id) on delete cascade,
  expected_roas numeric not null default 0,
  actual_roas numeric not null default 0,
  baseline_roas numeric not null default 0,
  incremental_profit numeric not null default 0,
  key_actions jsonb not null default '[]'::jsonb,
  lead_assets jsonb not null default '[]'::jsonb,
  strategy_notes jsonb not null default '[]'::jsonb,
  api_trace jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.agent_budget_projects enable row level security;
alter table public.agent_plan_versions enable row level security;
alter table public.agent_project_skus enable row level security;
alter table public.agent_live_frames enable row level security;
alter table public.agent_events enable row level security;
alter table public.agent_live_actions enable row level security;
alter table public.agent_reviews enable row level security;

create index if not exists agent_budget_projects_tenant_created_idx on public.agent_budget_projects(tenant_key, created_at);
create index if not exists agent_plan_versions_project_version_idx on public.agent_plan_versions(project_id, version_number);
create index if not exists agent_project_skus_version_idx on public.agent_project_skus(plan_version_id);
create index if not exists agent_live_frames_version_frame_idx on public.agent_live_frames(plan_version_id, frame_index);
create index if not exists agent_events_version_created_idx on public.agent_events(plan_version_id, created_at);
create index if not exists agent_live_actions_version_frame_idx on public.agent_live_actions(plan_version_id, frame_index);
create index if not exists agent_reviews_version_idx on public.agent_reviews(plan_version_id);
