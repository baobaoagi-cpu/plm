\set ON_ERROR_STOP on

-- Gate DB-1 uses synthetic identifiers and digests only.
set role xiewenxian_staging_app;
select set_config('app.current_tenant_id', 'xie_wenxian', false);

select set_config(
  'app.current_effective_user_id',
  'xie_wenxian:synthetic:student-a',
  false
);
insert into xiewenxian_staging.principals (
  tenant_id,
  source_system,
  principal_kind,
  effective_user_id,
  external_user_id_hash
)
select
  id,
  'synthetic',
  'student',
  'xie_wenxian:synthetic:student-a',
  repeat('a', 64)
from xiewenxian_staging.tenants
where tenant_key = 'xie_wenxian';

insert into xiewenxian_staging.conversations (
  tenant_id,
  principal_id,
  content_digest
)
select tenant_id, id, repeat('1', 64)
from xiewenxian_staging.principals;

insert into xiewenxian_staging.student_memory (
  tenant_id,
  principal_id,
  memory_digest
)
select tenant_id, id, repeat('2', 64)
from xiewenxian_staging.principals;

insert into xiewenxian_staging.prompt_log (
  tenant_id,
  principal_id,
  prompt_digest
)
select tenant_id, id, repeat('3', 64)
from xiewenxian_staging.principals;

select set_config(
  'app.current_effective_user_id',
  'xie_wenxian:synthetic:student-b',
  false
);
insert into xiewenxian_staging.principals (
  tenant_id,
  source_system,
  principal_kind,
  effective_user_id,
  external_user_id_hash
)
select
  id,
  'synthetic',
  'student',
  'xie_wenxian:synthetic:student-b',
  repeat('b', 64)
from xiewenxian_staging.tenants
where tenant_key = 'xie_wenxian';

insert into xiewenxian_staging.conversations (
  tenant_id,
  principal_id,
  content_digest
)
select tenant_id, id, repeat('4', 64)
from xiewenxian_staging.principals;

insert into xiewenxian_staging.student_memory (
  tenant_id,
  principal_id,
  memory_digest
)
select tenant_id, id, repeat('5', 64)
from xiewenxian_staging.principals;

insert into xiewenxian_staging.prompt_log (
  tenant_id,
  principal_id,
  prompt_digest
)
select tenant_id, id, repeat('6', 64)
from xiewenxian_staging.principals;

select set_config(
  'app.current_effective_user_id',
  'xie_wenxian:synthetic:owner',
  false
);
insert into xiewenxian_staging.principals (
  tenant_id,
  source_system,
  principal_kind,
  effective_user_id,
  external_user_id_hash
)
select
  id,
  'synthetic',
  'owner',
  'xie_wenxian:synthetic:owner',
  repeat('c', 64)
from xiewenxian_staging.tenants
where tenant_key = 'xie_wenxian';

insert into xiewenxian_staging.owner_evidence (
  tenant_id,
  principal_id,
  candidate_id,
  evidence_digest
)
select tenant_id, id, 'xww-v2-synthetic-proof', repeat('7', 64)
from xiewenxian_staging.principals;

do $proof$
declare
  visible_count bigint;
begin
  select count(*) into visible_count from xiewenxian_staging.principals;
  if visible_count <> 1 then
    raise exception 'owner principal scope leaked: % rows', visible_count;
  end if;

  select count(*) into visible_count from xiewenxian_staging.owner_evidence;
  if visible_count <> 1 then
    raise exception 'owner evidence scope failed: % rows', visible_count;
  end if;

  select count(*) into visible_count from xiewenxian_staging.student_memory;
  if visible_count <> 0 then
    raise exception 'owner can see student memory: % rows', visible_count;
  end if;

  begin
    insert into xiewenxian_staging.student_memory (
      tenant_id,
      principal_id,
      principal_kind,
      origin,
      memory_digest
    )
    select tenant_id, id, 'student', 'student_conversation', repeat('8', 64)
    from xiewenxian_staging.principals;
    raise exception 'owner evidence principal entered student memory';
  exception
    when insufficient_privilege or foreign_key_violation or check_violation then
      null;
  end;
end
$proof$;

select set_config(
  'app.current_effective_user_id',
  'xie_wenxian:synthetic:student-a',
  false
);
do $proof$
declare
  visible_count bigint;
begin
  select count(*) into visible_count from xiewenxian_staging.principals;
  if visible_count <> 1 then
    raise exception 'student A principal scope leaked: % rows', visible_count;
  end if;

  select count(*) into visible_count from xiewenxian_staging.conversations;
  if visible_count <> 1 then
    raise exception 'student A conversation scope leaked: % rows', visible_count;
  end if;

  select count(*) into visible_count from xiewenxian_staging.student_memory;
  if visible_count <> 1 then
    raise exception 'student A memory scope leaked: % rows', visible_count;
  end if;

  select count(*) into visible_count from xiewenxian_staging.prompt_log;
  if visible_count <> 1 then
    raise exception 'student A prompt scope leaked: % rows', visible_count;
  end if;

  select count(*) into visible_count from xiewenxian_staging.owner_evidence;
  if visible_count <> 0 then
    raise exception 'student A can see owner evidence: % rows', visible_count;
  end if;

  begin
    insert into xiewenxian_staging.owner_evidence (
      tenant_id,
      principal_id,
      principal_kind,
      candidate_id,
      evidence_digest
    )
    select tenant_id, id, 'owner', 'xww-v2-synthetic-rejected', repeat('9', 64)
    from xiewenxian_staging.principals;
    raise exception 'student principal entered owner evidence';
  exception
    when insufficient_privilege or foreign_key_violation or check_violation then
      null;
  end;

  begin
    insert into xiewenxian_staging.conversations (
      tenant_id,
      principal_id,
      content_digest
    )
    select tenant_id, id, repeat('0', 64)
    from xiewenxian_staging.principals
    where effective_user_id = 'xie_wenxian:synthetic:student-b';
    if found then
      raise exception 'student A wrote a student B conversation';
    end if;
  exception
    when insufficient_privilege or foreign_key_violation or check_violation then
      null;
  end;
end
$proof$;

reset app.current_effective_user_id;
do $proof$
declare
  visible_count bigint;
begin
  select count(*) into visible_count from xiewenxian_staging.principals;
  if visible_count <> 0 then
    raise exception 'missing identity context did not fail closed: % rows', visible_count;
  end if;
end
$proof$;

reset role;
set role xiewenxian_staging_owner;
select set_config('app.current_tenant_id', 'xie_wenxian', false);
select set_config(
  'app.current_effective_user_id',
  'xie_wenxian:synthetic:student-a',
  false
);
do $proof$
declare
  visible_count bigint;
begin
  select count(*) into visible_count from xiewenxian_staging.principals;
  if visible_count <> 1 then
    raise exception 'forced RLS did not constrain table owner: % rows', visible_count;
  end if;
end
$proof$;

reset role;
set role xiewenxian_staging_admin_readonly;
select set_config('app.current_tenant_id', 'xie_wenxian', false);
select set_config(
  'app.current_effective_user_id',
  'xie_wenxian:synthetic:student-b',
  false
);
do $proof$
declare
  visible_count bigint;
begin
  select count(*) into visible_count from xiewenxian_staging.student_memory;
  if visible_count <> 1 then
    raise exception 'readonly admin RLS scope failed: % rows', visible_count;
  end if;

  begin
    insert into xiewenxian_staging.prompt_log (
      tenant_id,
      principal_id,
      prompt_digest
    ) values (1, 1, repeat('d', 64));
    raise exception 'readonly admin unexpectedly wrote a prompt log';
  exception
    when insufficient_privilege then
      null;
  end;
end
$proof$;

reset role;
select
  'gate_db1_rls_proof' as proof,
  'PASS' as result,
  15 as asserted_behaviors;
