from __future__ import annotations

from pathlib import Path

from pglast import parse_sql

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    PROJECT_ROOT / "migrations" / "phase3b" / "001_xiewenxian_staging_identity.sql"
)
ROLLBACK = MIGRATION.with_name("001_xiewenxian_staging_identity.down.sql")


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").casefold()


def test_up_and_down_migrations_parse_as_postgresql() -> None:
    assert parse_sql(MIGRATION.read_text(encoding="utf-8"))
    assert parse_sql(ROLLBACK.read_text(encoding="utf-8"))


def test_migration_is_staging_scoped_and_provider_role_safe() -> None:
    sql = _sql()

    assert "create schema if not exists xiewenxian_staging" in sql
    assert "set_config('app.current_tenant_id', 'xie_wenxian', true)" in sql
    assert "current_database()" in sql
    assert "server_version_num" in sql
    assert "from pg_roles where rolname = 'xiewenxian_staging_app'" in sql
    assert "from pg_roles where rolname = 'xiewenxian_staging_admin_readonly'" in sql
    assert " anon" not in sql
    assert " authenticated" not in sql


def test_required_phase3b_tables_exist() -> None:
    sql = _sql()

    for table in (
        "tenants",
        "principals",
        "conversations",
        "student_memory",
        "prompt_log",
        "owner_evidence",
    ):
        assert f"xiewenxian_staging.{table}" in sql


def test_principal_and_tenant_foreign_keys_are_composite() -> None:
    sql = _sql()

    assert "unique (id, tenant_id)" in sql
    assert "foreign key (principal_id, tenant_id)" in sql
    assert "unique (id, tenant_id, principal_kind)" in sql
    assert "foreign key (principal_id, tenant_id, principal_kind)" in sql


def test_owner_evidence_cannot_become_student_memory_in_schema() -> None:
    sql = _sql()

    assert "student_memory_kind_check check (principal_kind = 'student')" in sql
    assert "student_memory_origin_check check (origin = 'student_conversation')" in sql
    assert "owner_evidence_kind_check check (principal_kind = 'owner')" in sql
    assert "owner_provided_unreviewed" in sql


def test_all_tables_enable_and_force_rls() -> None:
    sql = _sql()

    assert sql.count(" enable row level security") == 6
    assert sql.count(" force row level security") == 6
    assert sql.count("create policy ") == 6
    assert "app.current_effective_user_id" in sql
    assert "app.current_tenant_id" in sql


def test_foreign_keys_and_rls_filter_columns_are_indexed() -> None:
    sql = _sql()

    for index in (
        "principals_tenant_kind_idx",
        "conversations_principal_created_idx",
        "student_memory_principal_created_idx",
        "prompt_log_principal_created_idx",
        "owner_evidence_principal_created_idx",
        "owner_evidence_candidate_idx",
    ):
        assert index in sql


def test_privileges_are_fail_closed_and_least_privilege() -> None:
    sql = _sql()

    assert "revoke all on schema xiewenxian_staging from public" in sql
    assert "revoke all on all tables in schema xiewenxian_staging from public" in sql
    assert "grant all" not in sql
    assert "superuser" not in sql
    assert "bypassrls" not in sql


def test_rollback_refuses_non_staging_environment() -> None:
    rollback = ROLLBACK.read_text(encoding="utf-8").casefold()

    assert "app.environment" in rollback
    assert "is distinct from 'staging'" in rollback
    assert "refusing to remove phase 3b schema outside staging" in rollback
    assert "drop schema if exists xiewenxian_staging cascade" in rollback


def test_migration_contains_no_other_persona_or_secret_value() -> None:
    sql = _sql()

    for forbidden in (
        "tracy",
        "laitingting",
        "賴婷婷",
        "api_key=",
        "access_token=",
        "password=",
        "livekit",
        "minimax",
    ):
        assert forbidden not in sql
