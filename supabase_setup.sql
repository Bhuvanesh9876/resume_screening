-- Enable Vector Support
create extension if not exists vector;

-- Create Job Configs Table
create table if not exists public.job_configs (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  job_title text not null,
  job_description text not null,
  required_qualification text,
  required_experience int,
  must_have_skills text[],
  good_to_have_skills text[],
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Ensure columns exist (in case table already existed without them)
alter table public.job_configs add column if not exists required_qualification text;
alter table public.job_configs add column if not exists required_experience int;
alter table public.job_configs add column if not exists must_have_skills text[];
alter table public.job_configs add column if not exists good_to_have_skills text[];

-- Create Screening History Table
create table if not exists public.screening_history (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  job_config_id uuid references public.job_configs(id),
  job_title text,
  threshold float,
  shortlisted_count int,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Ensure columns exist for screening_history
alter table public.screening_history add column if not exists job_title text;
alter table public.screening_history add column if not exists job_config_id uuid references public.job_configs(id);

-- Create Shortlisted Candidates Table
create table if not exists public.shortlisted_candidates (
  id uuid default gen_random_uuid() primary key,
  history_id uuid references public.screening_history(id) on delete cascade not null,
  candidate_name text,
  candidate_email text,
  candidate_phone text,
  final_score float,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Ensure columns exist (in case table already existed without them)
alter table public.shortlisted_candidates add column if not exists candidate_phone text;
alter table public.shortlisted_candidates add column if not exists embedding vector(384);

-- Enable RLS
alter table public.job_configs enable row level security;
alter table public.screening_history enable row level security;
alter table public.shortlisted_candidates enable row level security;

-- Policies (Drop first to avoid errors if they exist)
drop policy if exists "Users can manage their own job configs" on public.job_configs;
create policy "Users can manage their own job configs" 
on public.job_configs for all 
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can manage their own history" on public.screening_history;
create policy "Users can manage their own history" 
on public.screening_history for all 
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can manage candidates via history" on public.shortlisted_candidates;
create policy "Users can manage candidates via history" 
on public.shortlisted_candidates for all 
to authenticated
using (
  exists (
    select 1 from public.screening_history 
    where id = shortlisted_candidates.history_id 
    and user_id = auth.uid()
  )
)
with check (
  exists (
    select 1 from public.screening_history 
    where id = shortlisted_candidates.history_id 
    and user_id = auth.uid()
  )
);
