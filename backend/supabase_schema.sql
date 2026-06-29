create extension if not exists pgcrypto;

create table if not exists api_users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  api_key_hash text not null unique,
  api_key_preview text,
  plan text not null default 'Free',
  monthly_limit integer not null default 500,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_used_at timestamptz
);

create table if not exists api_usage (
  id bigserial primary key,
  user_id uuid not null references api_users(id) on delete cascade,
  endpoint text not null,
  method text not null,
  status_code integer not null,
  response_time_ms integer not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_api_usage_user_created_at
  on api_usage (user_id, created_at desc);

create index if not exists idx_api_usage_endpoint
  on api_usage (endpoint);

create index if not exists idx_api_usage_created_at
  on api_usage (created_at desc);

create table if not exists feedback_submissions (
  id uuid primary key default gen_random_uuid(),
  feedback text not null default '',
  next_features jsonb not null default '[]'::jsonb,
  email text,
  page text,
  ip text,
  user_agent text,
  submitted_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists idx_feedback_submissions_submitted_at
  on feedback_submissions (submitted_at desc);

create index if not exists idx_feedback_submissions_email
  on feedback_submissions (email);
