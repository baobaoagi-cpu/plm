param(
    [string]$Image = "postgres:15-alpine"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ContainerName = "plm-gate-db1-$([guid]::NewGuid().ToString('N').Substring(0, 12))"
$DatabaseName = "plm_gate_db1"
$DatabasePassword = [guid]::NewGuid().ToString("N")
$StartedAt = [System.Diagnostics.Stopwatch]::StartNew()

function Invoke-DockerChecked {
    param([string[]]$Arguments)

    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker command failed with exit code $LASTEXITCODE"
    }
}

try {
    Invoke-DockerChecked @(
        "run", "--detach",
        "--name", $ContainerName,
        "--network", "none",
        "--tmpfs", "/var/lib/postgresql/data:rw,noexec,nosuid,size=256m",
        "--env", "POSTGRES_PASSWORD=$DatabasePassword",
        "--env", "POSTGRES_DB=$DatabaseName",
        $Image
    )

    $Ready = $false
    for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
        & docker exec $ContainerName pg_isready -U postgres -d $DatabaseName *> $null
        if ($LASTEXITCODE -eq 0) {
            $Ready = $true
            break
        }
        Start-Sleep -Milliseconds 500
    }
    if (-not $Ready) {
        throw "disposable PostgreSQL did not become ready"
    }

    $UpMigration = Join-Path $ProjectRoot "migrations\phase3b\001_xiewenxian_staging_identity.sql"
    $DownMigration = Join-Path $ProjectRoot "migrations\phase3b\001_xiewenxian_staging_identity.down.sql"
    $Proof = Join-Path $ProjectRoot "tests\integration\gate_db1_rls_proof.sql"
    Invoke-DockerChecked @("cp", $UpMigration, "${ContainerName}:/tmp/up.sql")
    Invoke-DockerChecked @("cp", $DownMigration, "${ContainerName}:/tmp/down.sql")
    Invoke-DockerChecked @("cp", $Proof, "${ContainerName}:/tmp/proof.sql")

    $RoleSql = @"
create role xiewenxian_staging_owner
  nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;
create role xiewenxian_staging_app
  nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;
create role xiewenxian_staging_admin_readonly
  nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;
grant create on database $DatabaseName to xiewenxian_staging_owner;
grant xiewenxian_staging_owner to postgres;
"@
    Invoke-DockerChecked @(
        "exec", $ContainerName,
        "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", $DatabaseName,
        "-c", $RoleSql
    )

    foreach ($Run in 1..2) {
        Invoke-DockerChecked @(
            "exec", $ContainerName,
            "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", $DatabaseName,
            "-c", "set role xiewenxian_staging_owner", "-f", "/tmp/up.sql"
        )
    }

    Invoke-DockerChecked @(
        "exec", $ContainerName,
        "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", $DatabaseName,
        "-f", "/tmp/proof.sql"
    )

    $RoleAttributes = & docker exec $ContainerName psql -X -A -t -v ON_ERROR_STOP=1 `
        -U postgres -d $DatabaseName `
        -c "select count(*) from pg_roles where rolname like 'xiewenxian_staging_%' and not rolsuper and not rolbypassrls and not rolcanlogin"
    if ($LASTEXITCODE -ne 0 -or $RoleAttributes.Trim() -ne "3") {
        throw "database roles are not fail-closed"
    }

    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & docker exec $ContainerName psql -X -v ON_ERROR_STOP=1 -U postgres -d $DatabaseName `
        -c "set role xiewenxian_staging_owner" -f "/tmp/down.sql" 1> $null 2> $null
    $BlockedRollbackExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousErrorActionPreference
    if ($BlockedRollbackExitCode -eq 0) {
        throw "rollback unexpectedly ran without the staging guard"
    }

    $SchemaAfterBlockedRollback = & docker exec $ContainerName psql -X -A -t `
        -v ON_ERROR_STOP=1 -U postgres -d $DatabaseName `
        -c "select count(*) from pg_namespace where nspname = 'xiewenxian_staging'"
    if ($LASTEXITCODE -ne 0 -or $SchemaAfterBlockedRollback.Trim() -ne "1") {
        throw "blocked rollback changed the staging schema"
    }

    Invoke-DockerChecked @(
        "exec", $ContainerName,
        "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", $DatabaseName,
        "-c", "set role xiewenxian_staging_owner",
        "-c", "set app.environment = 'staging'",
        "-f", "/tmp/down.sql"
    )

    $SchemaAfterApprovedRollback = & docker exec $ContainerName psql -X -A -t `
        -v ON_ERROR_STOP=1 -U postgres -d $DatabaseName `
        -c "select count(*) from pg_namespace where nspname = 'xiewenxian_staging'"
    if ($LASTEXITCODE -ne 0 -or $SchemaAfterApprovedRollback.Trim() -ne "0") {
        throw "approved rollback did not remove the staging schema"
    }

    $PostgresVersion = & docker exec $ContainerName psql -X -A -t `
        -v ON_ERROR_STOP=1 -U postgres -d $DatabaseName -c "show server_version"
    if ($LASTEXITCODE -ne 0) {
        throw "could not read disposable PostgreSQL version"
    }

    $StartedAt.Stop()
    [ordered]@{
        gate = "Gate DB-1"
        result = "PASS"
        postgres_version = $PostgresVersion.Trim()
        network = "none"
        storage = "tmpfs"
        synthetic_only = $true
        migration_apply_count = 2
        rls_asserted_behaviors = 15
        total_gate_checks = 19
        role_attribute_proof = "PASS"
        rollback_guard = "PASS"
        approved_rollback = "PASS"
        elapsed_ms = $StartedAt.ElapsedMilliseconds
    } | ConvertTo-Json
}
finally {
    if ($ContainerName -like "plm-gate-db1-*") {
        & docker rm --force $ContainerName *> $null
    }
}
