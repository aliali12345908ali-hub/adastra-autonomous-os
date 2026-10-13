# Adastra Autonomous OS — controlled foundation

This build is a local, testable foundation for the Adastra payment/order core and Beta Slots.

## Verification status

This archive is a **repair candidate**, not proof of a live Railway deployment. Runtime Gates A/B/C remain NOT PASS until executed against the isolated Railway PostgreSQL instance and raw JSON evidence is retained.

## Existing local checks (historical)
- Pytest: 10 passed.
- Alembic upgrade to `2026_10_04_adastra_beta`: passed on SQLite test database.
- `alembic heads`: `2026_10_04_adastra_beta`.
- Stripe guards tested for amount, currency, signature presence, duplicate event, and idempotency payload conflict.
- Beta Slots: 10 seeded slots, first-available reservation, exhaustion handling, PostgreSQL row-lock path.
- API does not call `Base.metadata.create_all()` at import.
- Railway configuration stages `alembic upgrade head` as the pre-deploy migration command.

## Not yet verified
- Real PostgreSQL migration execution.
- Real Stripe Test Mode webhook delivery/signature evidence.
- Cloud/Railway concurrency evidence, including 20-worker and stale-lease gates.
- Production readiness / VERIFIED state.

## Safety
No production deployment or GitHub `main` modification is performed by this archive.


## Gate order

1. **A — Migration:** on a disposable clean verification database, set `ADASTRA_TEST_DATABASE_URL`, `ADASTRA_MIGRATION_TEST=ALLOW`, and a unique `ADASTRA_MIGRATION_RUN_ID`; run `python scripts/gate_a_migration.py`. It refuses any target with existing public tables and saves JSON evidence.
2. **B — Concurrency:** only after A passes, run `python scripts/concurrency_evidence_harness.py --workers 20 --report concurrency-evidence.json` against the isolated PostgreSQL test URL.
3. **C — Stale worker:** the harness expires a lease and requires heartbeat and release to be rejected.
4. Preserve raw logs, JSON report, artifact SHA-256, database target identity (redacted), and timestamps. Any FAIL/INCONCLUSIVE blocks progression. Never run these gates against Production.
