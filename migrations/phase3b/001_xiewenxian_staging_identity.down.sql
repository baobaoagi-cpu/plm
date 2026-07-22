begin;

do $$
begin
  if current_setting('app.environment', true) is distinct from 'staging' then
    raise exception 'refusing to remove Phase 3B schema outside staging';
  end if;
  if current_database() is null then
    raise exception 'database identity is unavailable';
  end if;
end
$$;

drop schema if exists xiewenxian_staging cascade;

commit;
