from fastapi import FastAPI, HTTPException
import os
import sqlite3

app = FastAPI(title="Adastra Autonomous OS")

@app.get("/")
def root():
    return {"service": "Adastra Autonomous OS", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

def get_db():
    db = os.getenv("DATABASE_PATH", "adastra_os.db")
    return sqlite3.connect(db)

def check_user_payment_status(email: str):
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM transactions WHERE customer_email=? AND status='paid'",
            (email,)
        )
        return cur.fetchone() is not None
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

@app.get("/api/get-protected-info")
def protected(customer_email: str):
    if not check_user_payment_status(customer_email):
        raise HTTPException(403, "Payment required")
    return {"status":"success","autonomous_system_status":"Operational"}
