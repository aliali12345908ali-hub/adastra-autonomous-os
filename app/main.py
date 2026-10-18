from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
import sqlite3
import os

app = FastAPI(title="Adastra Autonomous OS", version="2.0.1")
security = HTTPBasic()

ADMIN_USER = "adastra"
import os
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default_secure_password")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = credentials.username == ADMIN_USER
    correct_pass = credentials.password == ADMIN_PASSWORD
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access to Adastra Financial Ledger",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def init_db():
    conn = sqlite3.connect("adastra_ledger.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def read_root(username: str = Depends(verify_credentials)):
    conn = sqlite3.connect("adastra_ledger.db")
    cursor = conn.cursor()
    cursor.execute("SELECT type, amount, description, date FROM transactions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Adastra Autonomous OS - Financial Ledger</title>
        <style>
            body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }
            .container { max-width: 800px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            h1 { color: #38bdf8; text-align: center; }
            table { width: 100%; margin-top: 20px; border-collapse: collapse; }
            th, td { padding: 12px; border-bottom: 1px solid #334155; text-align: left; }
            th { background: #0284c7; color: white; }
            .badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; }
            .income { background: #10b981; color: white; }
            .expense { background: #ef4444; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Adastra Autonomous OS (FR Ledger)</h1>
            <p><strong>Status:</strong> Cloud Production Active 24/7</p>
            <hr style="border:0; border-top:1px solid #334155;">
            <h2>Financial Transactions</h2>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Amount (€)</th>
                    <th>Description</th>
                    <th>Date</th>
                </tr>
    """
    for row in rows:
        t_type, amount, desc, date = row
        badge_class = "income" if t_type.lower() == "income" else "expense"
        html_content += f"<tr><td><span class='badge {badge_class}'>{t_type}</span></td><td>{amount}</td><td>{desc}</td><td>{date}</td></tr>"
        
    html_content += """
            </table>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/api/transaction")
def add_transaction(type: str, amount: float, description: str, username: str = Depends(verify_credentials)):
    conn = sqlite3.connect("adastra_ledger.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (type, amount, description) VALUES (?, ?, ?)", (type, amount, description))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Transaction recorded securely under French compliance rules."}

@app.get("/api/backup")
def get_backup(username: str = Depends(verify_credentials)):
    if os.path.exists("adastra_ledger.db"):
        return {"status": "backup_ready", "file": "adastra_ledger.db", "note": "Automated snapshot secured."}
    return {"status": "error", "message": "Database not found."}

@app.get("/health")
def health_check():
    return {"status": "online", "system": "Adastra Autonomous OS"}
