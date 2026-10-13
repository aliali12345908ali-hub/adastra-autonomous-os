#!/usr/bin/env python3
"""Gate A: migrate an explicitly authorized clean PostgreSQL test DB to Alembic HEAD."""
from __future__ import annotations
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
URL=os.getenv("ADASTRA_TEST_DATABASE_URL", "").strip()
RUN_ID=os.getenv("ADASTRA_MIGRATION_RUN_ID", "").strip()
if os.getenv("ADASTRA_MIGRATION_TEST") != "ALLOW" or not URL or URL.startswith("sqlite") or not RUN_ID:
    raise SystemExit("FAIL-CLOSED: require PostgreSQL ADASTRA_TEST_DATABASE_URL, ADASTRA_MIGRATION_TEST=ALLOW, ADASTRA_MIGRATION_RUN_ID")
os.environ["DATABASE_URL"]=URL
report={"gate":"A","run_id":RUN_ID,"started_at":datetime.now(timezone.utc).isoformat(),"status":"INCONCLUSIVE"}
engine=create_engine(URL,pool_pre_ping=True)
try:
    with engine.connect() as conn:
        dialect=conn.dialect.name
        if dialect != "postgresql": raise RuntimeError(f"Expected PostgreSQL, got {dialect}")
        tables=inspect(conn).get_table_names(schema="public")
        if tables: raise RuntimeError(f"Target DB is not clean; public tables exist: {tables}")
    result=subprocess.run([sys.executable,"-m","alembic","upgrade","head"],env=os.environ.copy(),text=True,capture_output=True)
    report["migration_stdout"]=result.stdout[-12000:]; report["migration_stderr"]=result.stderr[-12000:]
    if result.returncode != 0: raise RuntimeError(f"alembic upgrade head exited {result.returncode}")
    with engine.connect() as conn:
        current=conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        tables=sorted(inspect(conn).get_table_names(schema="public"))
        slots=conn.execute(text("SELECT count(*) FROM beta_slots")).scalar_one()
        if current != "2026_10_04_adastra_beta": raise RuntimeError(f"Unexpected Alembic head: {current}")
        if slots != 10: raise RuntimeError(f"Expected 10 slots, got {slots}")
        for required in ("customers","orders","audit_events","beta_slots","alembic_version"):
            if required not in tables: raise RuntimeError(f"Missing required table: {required}")
    report.update({"status":"PASS","dialect":dialect,"alembic_head":current,"public_tables":tables,"beta_slot_count":slots})
except Exception as exc: report.update({"status":"FAIL","error":f"{type(exc).__name__}: {exc}"})
finally: engine.dispose()
report["finished_at"]=datetime.now(timezone.utc).isoformat()
payload=json.dumps(report,indent=2,sort_keys=True); print(payload)
out=Path(os.getenv("ADASTRA_EVIDENCE_DIR",".")); out.mkdir(parents=True,exist_ok=True)
(out/f"gate-a-{RUN_ID}.json").write_text(payload+"\n",encoding="utf-8")
sys.exit(0 if report["status"]=="PASS" else 2)
