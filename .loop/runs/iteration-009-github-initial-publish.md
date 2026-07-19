# Iteration 009 — GitHub Initial Publish

## Goal

Publish the approved PLM baseline to the empty public repository and provide a design-only LINE OA
voice-call integration blueprint. Do not begin Task 004 or copy legacy runtime code.

## Changes

- Added `docs/line-oa-voice-call-integration-blueprint.md`.
- Updated README, architecture and changelog to reflect Task 001–003 and the Legacy audit.
- Reduced `.env.example` to four blank MiniMax variables.
- Expanded `.gitignore` to exclude all env files except the example, audio, provider raw evidence,
  result/timeline evidence and the complete Legacy reference clone.
- Initialized a standalone PLM Git repository on `main` with the approved `origin`.

## Security evidence

- Content scan found no high-confidence private key, bearer token, JWT, provider key or assigned
  production credential. Detected token-like strings were verified as test placeholders or matcher
  identifiers without printing values.
- Local `.env`, audio artifacts, raw provider results/timelines and nested Legacy `.git` are ignored.
- The Legacy reference repository was not staged, modified, copied or converted to a submodule.

## Validation

- `uv run ruff check .`: PASS.
- `uv run mypy --strict src`: PASS, 41 source files.
- `uv run pytest`: PASS, 47 tests.
- Tests emitted one non-failing sandbox permission warning for `.pytest_cache`; test execution and
  assertions completed successfully.

## Result

`NEEDS_HUMAN_POST_PUBLISH_REVIEW`

Task 004 remains `NOT_AUTHORIZED`.
