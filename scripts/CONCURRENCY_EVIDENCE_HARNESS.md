# ADASTRA PostgreSQL Concurrency Evidence Harness

Independent, non-production gate for the `beta_slots` lease logic.

## Safety gates

The harness **never** reads `DATABASE_URL` as a fallback. It requires:

- `ADASTRA_TEST_DATABASE_URL` = isolated PostgreSQL test database URL
- `ADASTRA_CONCURRENCY_TEST=ALLOW`
- `ADASTRA_CONCURRENCY_RUN_ID` = unique run identifier

SQLite is rejected. The harness checks the Alembic head is exactly `2026_10_04_adastra_beta` and expects exactly 10 beta slots.

## What it proves

- 20 independent OS processes race for 10 slots.
- Exactly 10 reservations succeed and exactly 10 receive `Beta slots are fully booked`.
- No slot id is assigned twice.
- Each successful reservation has an explicit lease and heartbeat.
- Owner heartbeat succeeds; rogue heartbeat is rejected.
- Owner release succeeds; rogue release is rejected.
- Gate C expires a lease and proves the expired owner cannot heartbeat or release it.
- Final state contains 10 AVAILABLE slots and zero RESERVED slots.
- Synthetic customers/orders are cleaned up after verification.

## Execution

Run only against the isolated Railway PostgreSQL database:

```bash
export ADASTRA_TEST_DATABASE_URL='postgresql+psycopg://...'
export ADASTRA_CONCURRENCY_TEST='ALLOW'
export ADASTRA_CONCURRENCY_RUN_ID="$(date +%Y%m%d%H%M%S)-$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')"
python scripts/concurrency_evidence_harness.py --report concurrency-evidence.json
```

Do not substitute a production database URL. The script intentionally does not accept `DATABASE_URL` for this gate.

## Evidence rule

`PASS` means every invariant is true and cleanup completed. Any unexpected worker error, duplicate slot assignment, ownership violation, migration mismatch, backend mismatch, or cleanup failure prevents promotion.
