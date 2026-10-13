"""Independent PostgreSQL concurrency evidence harness for Adastra beta slots.

Safety model:
- Uses only ADASTRA_TEST_DATABASE_URL; never falls back to DATABASE_URL.
- Refuses SQLite.
- Requires ADASTRA_CONCURRENCY_TEST=ALLOW and a unique test run id.
- Creates synthetic customer/order rows, then exercises beta slot leasing.
- Cleans up only rows belonging to this run.
- Emits PASS only when all invariants are proven.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TEST_DATABASE_ENV = "ADASTRA_TEST_DATABASE_URL"
ALLOW_ENV = "ADASTRA_CONCURRENCY_TEST"
RUN_ID_ENV = "ADASTRA_CONCURRENCY_RUN_ID"
EXPECTED_SLOTS = 10
DEFAULT_WORKERS = 20


def _require_test_database_url() -> str:
    url = os.getenv(TEST_DATABASE_ENV, "").strip()
    if not url:
        raise RuntimeError(f"{TEST_DATABASE_ENV} is required; DATABASE_URL is never used as fallback")
    if url.startswith("sqlite"):
        raise RuntimeError("SQLite is not an accepted backend for this gate; real PostgreSQL is required")
    if os.getenv(ALLOW_ENV) != "ALLOW":
        raise RuntimeError(f"Set {ALLOW_ENV}=ALLOW to authorize the isolated test mutation")
    run_id = os.getenv(RUN_ID_ENV, "").strip()
    if not run_id:
        raise RuntimeError(f"{RUN_ID_ENV} must be a unique, explicit test-run identifier")
    # Make the application modules use the explicitly supplied test database only.
    os.environ["DATABASE_URL"] = url
    return url


# Import application code only after the test-only database URL is validated.
DATABASE_URL = _require_test_database_url()

from sqlalchemy import create_engine, delete, func, select, text, update  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.models.models import Customer, Order  # noqa: E402
from app.models.beta_slots import BetaSlot, BetaSlotStatus  # noqa: E402
from app.services.beta_manager import (  # noqa: E402
    heartbeat_beta_slot,
    release_beta_slot,
    reserve_beta_slot,
)

RUN_ID = os.environ[RUN_ID_ENV]
EMAIL_PREFIX = f"adastra-concurrency-{RUN_ID}-"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def make_engine():
    return create_engine(DATABASE_URL, future=True, pool_pre_ping=True, pool_size=1, max_overflow=0)


def check_postgres_and_migration(db: Session) -> dict[str, Any]:
    dialect = db.bind.dialect.name if db.bind else "unknown"
    if dialect != "postgresql":
        raise RuntimeError(f"Expected PostgreSQL, got {dialect}")
    version = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    if version != "2026_10_04_adastra_beta":
        raise RuntimeError(f"Unexpected Alembic version: {version!r}")
    count = db.execute(select(func.count()).select_from(BetaSlot)).scalar_one()
    if count != EXPECTED_SLOTS:
        raise RuntimeError(f"Expected {EXPECTED_SLOTS} beta slots, found {count}")
    return {"dialect": dialect, "alembic_head": version, "slot_count": count}


def setup_run(db: Session) -> list[int]:
    # Clean only stale rows carrying this exact run id. This makes reruns deterministic.
    stale_customers = list(db.execute(select(Customer).where(Customer.email.like(f"{EMAIL_PREFIX}%"))).scalars())
    stale_customer_ids = [c.id for c in stale_customers]
    if stale_customer_ids:
        stale_orders = list(db.execute(select(Order.id).where(Order.customer_id.in_(stale_customer_ids))).scalars())
        if stale_orders:
            db.execute(update(BetaSlot).where(BetaSlot.order_id.in_(stale_orders)).values(
                status=BetaSlotStatus.AVAILABLE,
                order_id=None,
                lease_until=None,
                heartbeat_at=None,
                released_at=utcnow(),
            ))
            db.execute(delete(Order).where(Order.id.in_(stale_orders)))
        db.execute(delete(Customer).where(Customer.id.in_(stale_customer_ids)))

    # Fail closed if the verification DB contains any pre-existing reservation.
    # Never reset unrelated slots: that could destroy real reservation state.
    occupied = list(db.execute(select(BetaSlot).where(BetaSlot.status != BetaSlotStatus.AVAILABLE)).scalars())
    if occupied:
        raise RuntimeError(
            "Verification DB is not in a clean beta-slot state; refusing to reset unrelated reservations"
        )

    order_ids: list[int] = []
    for i in range(DEFAULT_WORKERS):
        customer = Customer(
            name=f"Concurrency Test {RUN_ID}-{i}",
            email=f"{EMAIL_PREFIX}{i}@invalid.test",
            company="ADASTRA-CONCURRENCY-TEST",
        )
        db.add(customer)
        db.flush()
        order = Order(
            customer_id=customer.id,
            project_name=f"Concurrency Test {RUN_ID}-{i}",
            industry="TEST",
            automation_challenge="Synthetic concurrency evidence only",
            technology_stack={"test": "concurrency"},
            amount_cents=100000,
            currency="eur",
        )
        db.add(order)
        db.flush()
        order_ids.append(order.id)
    db.commit()
    return order_ids


@dataclass
class ReserveResult:
    index: int
    order_id: int
    status: str
    slot_id: int | None = None
    slot_number: int | None = None
    error: str | None = None
    lease_until: str | None = None
    heartbeat_at: str | None = None


def reserve_worker(index: int, order_id: int, barrier: Any) -> dict[str, Any]:
    engine = make_engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        with SessionLocal() as db:
            barrier.wait(timeout=30)
            try:
                slot = reserve_beta_slot(db, order_id)
                db.commit()
                return asdict(ReserveResult(
                    index=index,
                    order_id=order_id,
                    status="RESERVED",
                    slot_id=slot.id,
                    slot_number=slot.slot_number,
                    lease_until=slot.lease_until.isoformat() if slot.lease_until else None,
                    heartbeat_at=slot.heartbeat_at.isoformat() if slot.heartbeat_at else None,
                ))
            except LookupError as exc:
                db.rollback()
                return asdict(ReserveResult(index, order_id, "FULLY_BOOKED", error=str(exc)))
            except Exception as exc:  # evidence harness must report unexpected failures
                db.rollback()
                return asdict(ReserveResult(index, order_id, "ERROR", error=f"{type(exc).__name__}: {exc}"))
    finally:
        if order_ids:
            try:
                with SessionLocal() as db:
                    cleanup_run(db, order_ids)
            except Exception:
                # Evidence gate remains INCONCLUSIVE/FAIL; never mask the primary result.
                pass
        engine.dispose()


def heartbeat_worker(slot_id: int, order_id: int, rogue_order_id: int, barrier: Any) -> dict[str, Any]:
    engine = make_engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    result: dict[str, Any] = {"slot_id": slot_id, "order_id": order_id}
    try:
        with SessionLocal() as db:
            barrier.wait(timeout=30)
            before = db.execute(select(BetaSlot.lease_until).where(BetaSlot.id == slot_id)).scalar_one()
            slot = heartbeat_beta_slot(db, slot_id, order_id)
            renewed = slot.lease_until
            db.commit()
            result.update({"owner_heartbeat": "PASS", "lease_before": before.isoformat() if before else None,
                           "lease_after": renewed.isoformat() if renewed else None})

            rogue = None
            with SessionLocal() as rogue_db:
                try:
                    heartbeat_beta_slot(rogue_db, slot_id, rogue_order_id)
                    rogue = "UNEXPECTED_SUCCESS"
                    rogue_db.rollback()
                except LookupError:
                    rogue = "REJECTED"
                    rogue_db.rollback()
                except Exception as exc:
                    rogue = f"ERROR:{type(exc).__name__}"
                    rogue_db.rollback()
            result["rogue_heartbeat"] = rogue
            return result
    except Exception as exc:
        result["status"] = f"ERROR:{type(exc).__name__}: {exc}"
        return result
    finally:
        if order_ids:
            try:
                with SessionLocal() as db:
                    cleanup_run(db, order_ids)
            except Exception:
                # Evidence gate remains INCONCLUSIVE/FAIL; never mask the primary result.
                pass
        engine.dispose()


def release_worker(slot_id: int, order_id: int, rogue_order_id: int) -> dict[str, Any]:
    engine = make_engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    result = {"slot_id": slot_id, "order_id": order_id}
    try:
        with SessionLocal() as db:
            try:
                release_beta_slot(db, slot_id, rogue_order_id)
                result["rogue_release"] = "UNEXPECTED_SUCCESS"
                db.rollback()
            except LookupError:
                result["rogue_release"] = "REJECTED"
                db.rollback()
            slot = release_beta_slot(db, slot_id, order_id)
            db.commit()
            result["owner_release"] = {
                "status": slot.status.value,
                "order_id": slot.order_id,
                "lease_until": slot.lease_until,
                "heartbeat_at": slot.heartbeat_at,
                "released_at": slot.released_at.isoformat() if slot.released_at else None,
            }
            return result
    except Exception as exc:
        result["status"] = f"ERROR:{type(exc).__name__}: {exc}"
        return result
    finally:
        if order_ids:
            try:
                with SessionLocal() as db:
                    cleanup_run(db, order_ids)
            except Exception:
                # Evidence gate remains INCONCLUSIVE/FAIL; never mask the primary result.
                pass
        engine.dispose()


def verify_invariants(db: Session, results: list[dict[str, Any]], hb_results: list[dict[str, Any]], release_results: list[dict[str, Any]]) -> dict[str, Any]:
    reserved = [r for r in results if r["status"] == "RESERVED"]
    full = [r for r in results if r["status"] == "FULLY_BOOKED"]
    errors = [r for r in results if r["status"] == "ERROR"]
    slot_ids = [r["slot_id"] for r in reserved]
    unique_slot_ids = set(slot_ids)
    duplicate_slot_ids = len(slot_ids) - len(unique_slot_ids)

    active = list(db.execute(select(BetaSlot).where(BetaSlot.status == BetaSlotStatus.RESERVED)).scalars())
    available = list(db.execute(select(BetaSlot).where(BetaSlot.status == BetaSlotStatus.AVAILABLE)).scalars())

    hb_owner_pass = sum(r.get("owner_heartbeat") == "PASS" for r in hb_results)
    hb_rogue_rejected = sum(r.get("rogue_heartbeat") == "REJECTED" for r in hb_results)
    rel_owner_pass = sum(bool(r.get("owner_release", {}).get("released_at")) for r in release_results)
    rel_rogue_rejected = sum(r.get("rogue_release") == "REJECTED" for r in release_results)

    invariants = {
        "I1_exact_capacity": len(reserved) == EXPECTED_SLOTS and len(full) == DEFAULT_WORKERS - EXPECTED_SLOTS,
        "I2_unique_slot_assignment": duplicate_slot_ids == 0 and len(unique_slot_ids) == len(reserved),
        "I3_no_unexpected_worker_errors": len(errors) == 0,
        "I4_ownership_heartbeat": hb_owner_pass == EXPECTED_SLOTS and hb_rogue_rejected == EXPECTED_SLOTS,
        "I5_ownership_release_and_cleanup": rel_owner_pass == EXPECTED_SLOTS and rel_rogue_rejected == EXPECTED_SLOTS and len(active) == 0 and len(available) == EXPECTED_SLOTS,
    }
    return {
        "invariants": invariants,
        "counts": {
            "reserved_results": len(reserved),
            "fully_booked_results": len(full),
            "unexpected_errors": len(errors),
            "duplicate_slot_ids": duplicate_slot_ids,
            "active_slots_after_release": len(active),
            "available_slots_after_release": len(available),
            "heartbeat_owner_pass": hb_owner_pass,
            "heartbeat_rogue_rejected": hb_rogue_rejected,
            "release_owner_pass": rel_owner_pass,
            "release_rogue_rejected": rel_rogue_rejected,
        },
    }


def cleanup_run(db: Session, order_ids: list[int]) -> None:
    db.execute(update(BetaSlot).where(BetaSlot.order_id.in_(order_ids)).values(
        status=BetaSlotStatus.AVAILABLE,
        order_id=None,
        lease_until=None,
        heartbeat_at=None,
        released_at=utcnow(),
    ))
    customers = list(db.execute(select(Customer.id).where(Customer.email.like(f"{EMAIL_PREFIX}%"))).scalars())
    if customers:
        db.execute(delete(Order).where(Order.customer_id.in_(customers)))
        db.execute(delete(Customer).where(Customer.id.in_(customers)))
    db.commit()


def process_entry(kind: str, queue: Any, payload: dict[str, Any]) -> None:
    """Pickle-safe multiprocessing entrypoint for Python spawn."""
    try:
        if kind == "reserve":
            result = reserve_worker(payload["index"], payload["order_id"], payload["barrier"])
        elif kind == "heartbeat":
            result = heartbeat_worker(
                payload["slot_id"], payload["order_id"], payload["rogue_order_id"], payload["barrier"]
            )
        elif kind == "release":
            result = release_worker(payload["slot_id"], payload["order_id"], payload["rogue_order_id"])
        else:
            result = {"status": "ERROR:unknown_process_kind", "kind": kind}
    except Exception as exc:
        result = {"status": f"ERROR:{type(exc).__name__}: {exc}"}
    queue.put(result)


def collect_results(queue: Any, processes: list[mp.Process], expected: int, timeout: float = 10.0) -> list[dict[str, Any]]:
    """Collect exactly the results that arrived; missing workers make the gate inconclusive."""
    results: list[dict[str, Any]] = []
    deadline = time.monotonic() + timeout
    while len(results) < expected and time.monotonic() < deadline:
        remaining = max(0.1, deadline - time.monotonic())
        try:
            results.append(queue.get(timeout=min(1.0, remaining)))
        except Exception:
            continue
    for p in processes:
        if p.is_alive():
            p.terminate()
            p.join(5)
    return results


def run(workers: int) -> dict[str, Any]:
    if workers != DEFAULT_WORKERS:
        raise ValueError(f"This gate is fixed at {DEFAULT_WORKERS} contenders to prove the 10-slot boundary")

    engine = make_engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    report: dict[str, Any] = {"run_id": RUN_ID, "started_at": utcnow().isoformat(), "status": "INCONCLUSIVE"}
    order_ids: list[int] = []
    try:
        with SessionLocal() as db:
            report["preflight"] = check_postgres_and_migration(db)
            order_ids = setup_run(db)

        ctx = mp.get_context("spawn")
        barrier = ctx.Barrier(workers)
        processes: list[mp.Process] = []
        queue = ctx.Queue()

        for i, order_id in enumerate(order_ids):
            p = ctx.Process(
                target=process_entry,
                args=("reserve", queue, {"index": i, "order_id": order_id, "barrier": barrier}),
            )
            p.start()
            processes.append(p)

        reserve_results = collect_results(queue, processes, workers, timeout=20.0)
        reserve_results.sort(key=lambda x: x.get("index", 10**9))
        if len(reserve_results) != workers:
            raise RuntimeError(f"Only {len(reserve_results)}/{workers} reserve workers returned evidence")
        report["reserve_results"] = reserve_results
        winners = [r for r in reserve_results if r["status"] == "RESERVED"]

        hb_barrier = ctx.Barrier(len(winners))
        hb_processes: list[mp.Process] = []
        hb_queue = ctx.Queue()
        loser_ids = [r["order_id"] for r in reserve_results if r["status"] == "FULLY_BOOKED"]
        if len(loser_ids) != DEFAULT_WORKERS - EXPECTED_SLOTS:
            raise RuntimeError(f"Expected {DEFAULT_WORKERS - EXPECTED_SLOTS} losing contenders, found {len(loser_ids)}")
        rogue_order_id = loser_ids[0]
        for r in winners:
            p = ctx.Process(
                target=process_entry,
                args=("heartbeat", hb_queue, {
                    "slot_id": r["slot_id"],
                    "order_id": r["order_id"],
                    "rogue_order_id": rogue_order_id,
                    "barrier": hb_barrier,
                }),
            )
            p.start()
            hb_processes.append(p)
        hb_results = collect_results(hb_queue, hb_processes, len(winners), timeout=20.0)
        if len(hb_results) != len(winners):
            raise RuntimeError(f"Only {len(hb_results)}/{len(winners)} heartbeat workers returned evidence")
        report["heartbeat_results"] = hb_results

        release_processes: list[mp.Process] = []
        release_queue = ctx.Queue()
        for r in winners:
            p = ctx.Process(
                target=process_entry,
                args=("release", release_queue, {
                    "slot_id": r["slot_id"],
                    "order_id": r["order_id"],
                    "rogue_order_id": rogue_order_id,
                }),
            )
            p.start()
            release_processes.append(p)
        release_results = collect_results(release_queue, release_processes, len(winners), timeout=20.0)
        if len(release_results) != len(winners):
            raise RuntimeError(f"Only {len(release_results)}/{len(winners)} release workers returned evidence")
        report["release_results"] = release_results

        # Gate C: expire a fresh lease and prove the previous owner is fenced out.
        stale_gate = {"status": "INCONCLUSIVE"}
        with SessionLocal() as db:
            stale_slot = reserve_beta_slot(db, order_ids[0], lease_seconds=900)
            stale_slot_id = stale_slot.id
            db.commit()
            db.execute(update(BetaSlot).where(BetaSlot.id == stale_slot_id).values(lease_until=utcnow() - timedelta(seconds=5)))
            db.commit()
            stale_gate["lease_expired"] = True
            try:
                heartbeat_beta_slot(db, stale_slot_id, order_ids[0])
                stale_gate["heartbeat"] = "UNEXPECTED_SUCCESS"
            except LookupError as exc:
                db.rollback(); stale_gate["heartbeat"] = "REJECTED"; stale_gate["heartbeat_reason"] = str(exc)
            try:
                release_beta_slot(db, stale_slot_id, order_ids[0])
                stale_gate["release"] = "UNEXPECTED_SUCCESS"
            except LookupError as exc:
                db.rollback(); stale_gate["release"] = "REJECTED"; stale_gate["release_reason"] = str(exc)
            stale_gate["status"] = "PASS" if stale_gate.get("heartbeat") == "REJECTED" and stale_gate.get("release") == "REJECTED" else "FAIL"
        report["gate_c_stale_worker"] = stale_gate

        with SessionLocal() as db:
            cleanup_run(db, order_ids)
            report["verification"] = verify_invariants(db, reserve_results, hb_results, release_results)
            report["verification"]["invariants"]["I6_stale_worker_rejected"] = stale_gate["status"] == "PASS"
            report["status"] = "PASS" if all(report["verification"]["invariants"].values()) else "FAIL"
        report["finished_at"] = utcnow().isoformat()
        return report
    finally:
        if order_ids:
            try:
                with SessionLocal() as db:
                    cleanup_run(db, order_ids)
            except Exception:
                # Evidence gate remains INCONCLUSIVE/FAIL; never mask the primary result.
                pass
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="ADASTRA PostgreSQL multi-process concurrency evidence harness")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    try:
        report = run(args.workers)
    except Exception as exc:
        report = {"run_id": RUN_ID, "status": "INCONCLUSIVE", "error": f"{type(exc).__name__}: {exc}"}

    payload = json.dumps(report, indent=2, sort_keys=True, default=str)
    print(payload)
    if args.report:
        args.report.write_text(payload + "\n", encoding="utf-8")
    return 0 if report.get("status") == "PASS" else 2


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
