begin;

-- The migration is rerunnable after forced RLS is active. Keep the context transaction-local so
-- it cannot leak into a pooled application connection.
select set_config('app.current_tenant_id', 'xie_wenxian', true);

do $$
begin
  if current_setting('server_version_num')::integer < 150000 then
    raise exception 'Phase 3B requires PostgreSQL 15 or newer';
  end if;
  if current_database() is null then
    raise exception 'database identity is unavailable';
  end if;
end
$$;

create schema if not exists xiewenxian_staging;
revoke all on schema xiewenxian_staging from public;

create table if not exists xiewenxian_staging.tenants (
  id bigint generated always as identity primary key,
  tenant_key text not null unique,
  environment text not null default 'staging',
  created_at timestamptz not null default now(),
  constraint tenants_key_check check (tenant_key = 'xie_wenxian'),
  constraint tenants_environment_check check (environment = 'staging')
);

create table if not exists xiewenxian_staging.principals (
  id bigint generated always as identity primary key,
  tenant_id bigint not null references xiewenxian_staging.tenants(id) on delete restrict,
  source_system text not null,
  principal_kind text not null,
  effective_user_id text not null,
  external_user_id_hash text not null,
  created_at timestamptz not null default now(),
  constraint principals_source_system_check
    check (source_system in ('line', 'partner', 'synthetic')),
  constraint principals_kind_check
    check (principal_kind in ('owner', 'student', 'governor', 'technical_tester')),
  constraint principals_external_hash_check check (length(external_user_id_hash) = 64),
  constraint principals_tenant_effective_unique unique (tenant_id, effective_user_id),
  constraint principals_tenant_source_hash_unique
    unique (tenant_id, source_system, external_user_id_hash),
  constraint principals_id_tenant_unique unique (id, tenant_id),
  constraint principals_id_tenant_kind_unique unique (id, tenant_id, principal_kind)
);

create table if not exists xiewenxian_staging.conversations (
  id bigint generated always as identity primary key,
  tenant_id bigint not null,
  principal_id bigint not null,
  content_digest text not null,
  created_at timestamptz not null default now(),
  constraint conversations_digest_check check (length(content_digest) = 64),
  constraint conversations_principal_fkey
    foreign key (principal_id, tenant_id)
    references xiewenxian_staging.principals(id, tenant_id) on delete cascade
);

create table if not exists xiewenxian_staging.student_memory (
  id bigint generated always as identity primary key,
  tenant_id bigint not null,
  principal_id bigint not null,
  principal_kind text not null default 'student',
  origin text not null default 'student_conversation',
  memory_digest text not null,
  created_at timestamptz not null default now(),
  constraint student_memory_kind_check check (principal_kind = 'student'),
  constraint student_memory_origin_check check (origin = 'student_conversation'),
  constraint student_memory_digest_check check (length(memory_digest) = 64),
  constraint student_memory_principal_fkey
    foreign key (principal_id, tenant_id, principal_kind)
    references xiewenxian_staging.principals(id, tenant_id, principal_kind)
    on delete cascade
);

create table if not exists xiewenxian_staging.prompt_log (
  id bigint generated always as identity primary key,
  tenant_id bigint not null,
  principal_id bigint not null,
  prompt_digest text not null,
  created_at timestamptz not null default now(),
  constraint prompt_log_digest_check check (length(prompt_digest) = 64),
  constraint prompt_log_principal_fkey
    foreign key (principal_id, tenant_id)
    references xiewenxian_staging.principals(id, tenant_id) on delete cascade
);

create table if not exists xiewenxian_staging.owner_evidence (
  id bigint generated always as identity primary key,
  tenant_id bigint not null,
  principal_id bigint not null,
  principal_kind text not null default 'owner',
  candidate_id text not null,
  evidence_digest text not null,
  review_state text not null default 'OWNER_PROVIDED_UNREVIEWED',
  created_at timestamptz not null default now(),
  constraint owner_evidence_kind_check check (principal_kind = 'owner'),
  constraint owner_evidence_candidate_check check (candidate_id like 'xww-v2-%'),
  constraint owner_evidence_digest_check check (length(evidence_digest) = 64),
  constraint owner_evidence_review_state_check
    check (review_state = 'OWNER_PROVIDED_UNREVIEWED'),
  constraint owner_evidence_principal_fkey
    foreign key (principal_id, tenant_id, principal_kind)
    references xiewenxian_staging.principals(id, tenant_id, principal_kind)
    on delete restrict
);

insert into xiewenxian_staging.tenants (tenant_key, environment)
values ('xie_wenxian', 'staging')
on conflict (tenant_key) do nothing;

create index if not exists principals_tenant_kind_idx
  on xiewenxian_staging.principals (tenant_id, principal_kind);
create index if not exists conversations_principal_created_idx
  on xiewenxian_staging.conversations (principal_id, created_at desc);
create index if not exists student_memory_principal_created_idx
  on xiewenxian_staging.student_memory (principal_id, created_at desc);
create index if not exists prompt_log_principal_created_idx
  on xiewenxian_staging.prompt_log (principal_id, created_at desc);
create index if not exists owner_evidence_principal_created_idx
  on xiewenxian_staging.owner_evidence (principal_id, created_at desc);
create index if not exists owner_evidence_candidate_idx
  on xiewenxian_staging.owner_evidence (candidate_id);

alter table xiewenxian_staging.tenants enable row level security;
alter table xiewenxian_staging.tenants force row level security;
alter table xiewenxian_staging.principals enable row level security;
alter table xiewenxian_staging.principals force row level security;
alter table xiewenxian_staging.conversations enable row level security;
alter table xiewenxian_staging.conversations force row level security;
alter table xiewenxian_staging.student_memory enable row level security;
alter table xiewenxian_staging.student_memory force row level security;
alter table xiewenxian_staging.prompt_log enable row level security;
alter table xiewenxian_staging.prompt_log force row level security;
alter table xiewenxian_staging.owner_evidence enable row level security;
alter table xiewenxian_staging.owner_evidence force row level security;

do $migration$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'xiewenxian_staging' and tablename = 'tenants'
      and policyname = 'tenants_staging_scope'
  ) then
    execute $policy$
      create policy tenants_staging_scope on xiewenxian_staging.tenants
      for all
      using (tenant_key = current_setting('app.current_tenant_id', true))
      with check (tenant_key = current_setting('app.current_tenant_id', true))
    $policy$;
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'xiewenxian_staging' and tablename = 'principals'
      and policyname = 'principals_effective_user_scope'
  ) then
    execute $policy$
      create policy principals_effective_user_scope on xiewenxian_staging.principals
      for all
      using (
        tenant_id = (
          select id from xiewenxian_staging.tenants
          where tenant_key = current_setting('app.current_tenant_id', true)
        )
        and effective_user_id = current_setting('app.current_effective_user_id', true)
      )
      with check (
        tenant_id = (
          select id from xiewenxian_staging.tenants
          where tenant_key = current_setting('app.current_tenant_id', true)
        )
        and effective_user_id = current_setting('app.current_effective_user_id', true)
      )
    $policy$;
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'xiewenxian_staging' and tablename = 'conversations'
      and policyname = 'conversations_effective_user_scope'
  ) then
    execute $policy$
      create policy conversations_effective_user_scope on xiewenxian_staging.conversations
      for all
      using (exists (
        select 1 from xiewenxian_staging.principals p
        where p.id = conversations.principal_id
          and p.tenant_id = conversations.tenant_id
          and p.effective_user_id = current_setting('app.current_effective_user_id', true)
      ))
      with check (exists (
        select 1 from xiewenxian_staging.principals p
        where p.id = conversations.principal_id
          and p.tenant_id = conversations.tenant_id
          and p.effective_user_id = current_setting('app.current_effective_user_id', true)
      ))
    $policy$;
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'xiewenxian_staging' and tablename = 'student_memory'
      and policyname = 'student_memory_effective_user_scope'
  ) then
    execute $policy$
      create policy student_memory_effective_user_scope on xiewenxian_staging.student_memory
      for all
      using (exists (
        select 1 from xiewenxian_staging.principals p
        where p.id = student_memory.principal_id
          and p.tenant_id = student_memory.tenant_id
          and p.principal_kind = 'student'
          and p.effective_user_id = current_setting('app.current_effective_user_id', true)
      ))
      with check (exists (
        select 1 from xiewenxian_staging.principals p
        where p.id = student_memory.principal_id
          and p.tenant_id = student_memory.tenant_id
          and p.principal_kind = 'student'
          and p.effective_user_id = current_setting('app.current_effective_user_id', true)
      ))
    $policy$;
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'xiewenxian_staging' and tablename = 'prompt_log'
      and policyname = 'prompt_log_effective_user_scope'
  ) then
    execute $policy$
      create policy prompt_log_effective_user_scope on xiewenxian_staging.prompt_log
      for all
      using (exists (
        select 1 from xiewenxian_staging.principals p
        where p.id = prompt_log.principal_id
          and p.tenant_id = prompt_log.tenant_id
          and p.effective_user_id = current_setting('app.current_effective_user_id', true)
      ))
      with check (exists (
        select 1 from xiewenxian_staging.principals p
        where p.id = prompt_log.principal_id
          and p.tenant_id = prompt_log.tenant_id
          and p.effective_user_id = current_setting('app.current_effective_user_id', true)
      ))
    $policy$;
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'xiewenxian_staging' and tablename = 'owner_evidence'
      and policyname = 'owner_evidence_owner_scope'
  ) then
    execute $policy$
      create policy owner_evidence_owner_scope on xiewenxian_staging.owner_evidence
      for all
      using (exists (
        select 1 from xiewenxian_staging.principals p
        where p.id = owner_evidence.principal_id
          and p.tenant_id = owner_evidence.tenant_id
          and p.principal_kind = 'owner'
          and p.effective_user_id = current_setting('app.current_effective_user_id', true)
      ))
      with check (exists (
        select 1 from xiewenxian_staging.principals p
        where p.id = owner_evidence.principal_id
          and p.tenant_id = owner_evidence.tenant_id
          and p.principal_kind = 'owner'
          and p.effective_user_id = current_setting('app.current_effective_user_id', true)
      ))
    $policy$;
  end if;
end
$migration$;

revoke all on all tables in schema xiewenxian_staging from public;
revoke all on all sequences in schema xiewenxian_staging from public;
alter default privileges in schema xiewenxian_staging revoke all on tables from public;
alter default privileges in schema xiewenxian_staging revoke all on sequences from public;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'xiewenxian_staging_app') then
    execute 'grant usage on schema xiewenxian_staging to xiewenxian_staging_app';
    execute 'grant select, insert on all tables in schema xiewenxian_staging '
      'to xiewenxian_staging_app';
    execute 'grant usage, select on all sequences in schema xiewenxian_staging '
      'to xiewenxian_staging_app';
  end if;
  if exists (
    select 1 from pg_roles where rolname = 'xiewenxian_staging_admin_readonly'
  ) then
    execute 'grant usage on schema xiewenxian_staging '
      'to xiewenxian_staging_admin_readonly';
    execute 'grant select on all tables in schema xiewenxian_staging '
      'to xiewenxian_staging_admin_readonly';
  end if;
end
$$;

commit;
