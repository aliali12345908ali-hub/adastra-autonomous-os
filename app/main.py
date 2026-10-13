from fastapi import FastAPI, Form, Response
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime

app = FastAPI(title="Adastra OS")
DB = "adastra.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, desc TEXT, amount REAL, type TEXT, date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def home():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, desc, amount, type, date FROM transactions ORDER BY id DESC")
    txs = c.fetchall()
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    inc = c.fetchone()[0] or 0.0
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
    exp = c.fetchone()[0] or 0.0
    
    c.execute("SELECT value FROM settings WHERE key='siret'")
    row_siret = c.fetchone()
    siret = row_siret[0] if row_siret else "Not Set"
    conn.close()
    net = inc - exp

    rows = ""
    for t in txs:
        color = "#059669" if t[3] == "Income" else "#dc2626"
        rows += "<tr><td>" + str(t[0]) + "</td><td>" + str(t[1]) + "</td><td style='color:" + color + "; font-weight:bold;'>" + str(t[2]) + " EUR</td><td>" + str(t[3]) + "</td><td>" + str(t[4]) + "</td></tr>"
    if not rows:
        rows = "<tr><td colspan='5' style='text-align:center; color:#9ca3af;'>No transactions found</td></tr>"

    return """
    <!DOCTYPE html><html lang='en' dir='ltr'><head><meta charset='UTF-8'><title>Adastra OS - Legal & Financial</title>
    <style>
        body { font-family: Tahoma; background: #0b0f19; color: #f3f4f6; padding: 20px; }
        .box { max-width: 850px; margin: auto; background: #111827; padding: 20px; border-radius: 10px; border: 1px solid #1f2937; }
        h1, h2 { color: #0284c7; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px; }
        th, td { border: 1px solid #1f2937; padding: 8px; text-align: left; }
        th { background: #1f2937; color: #0284c7; }
        form, .settings-box { background: #1f2937; padding: 15px; border-radius: 6px; margin-top: 15px; }
        input, select { width: 100%; padding: 8px; margin: 5px 0 12px 0; background: #111827; border: 1px solid #374151; color: white; border-radius: 4px; }
        button { background: #0284c7; color: white; border: none; padding: 10px; border-radius: 4px; width: 100%; font-weight: bold; cursor: pointer; }
    </style></head><body>
    <div class="box">
        <h1>Adastra Autonomous OS</h1>
        <p style="text-align: center; color: #9ca3af;">Owner: MR ABDALLAH BEN BELGACEM | SIRET/SIREN: <b>""" + siret + """</b> | Balance: """ + str(net) + """ EUR</p>
        
        <div class="settings-box">
            <h3>French Entity Settings (SIRET)</h3>
            <form action="/update-siret" method="POST">
                <label>SIRET / SIREN Number (14 digits):</label>
                <input type="text" name="siret" value=""" + siret + """ required>
                <button type="submit">Save SIRET</button>
            </form>
        </div>

        <h2>Add Transaction</h2>
        <form action="/add" method="POST">
            <label>Description:</label><input type="text" name="desc" required>
            <label>Amount (EUR):</label><input type="number" step="0.01" name="amount" required>
            <label>Type:</label>
            <select name="type"><option value="Income">Income</option><option value="Expense">Expense</option></select>
            <button type="submit">Save Transaction</button>
        </form>

        <h2>History</h2>
        <table><tr><th>ID</th><th>Description</th><th>Amount</th><th>Type</th><th>Date</th></tr>""" + rows + """</table>
    </div></body></html>
    """

@app.post("/add", response_class=HTMLResponse)
def add(desc: str = Form(...), amount: float = Form(...), type: str = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (desc, amount, type, date) VALUES (?, ?, ?, ?)", (desc, amount, type, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    return "<script>alert('Saved!'); window.location.href='/';</script>"

@app.post("/update-siret", response_class=HTMLResponse)
def update_siret(siret: str = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('siret', ?)", (siret,))
    conn.commit()
    conn.close()
    return "<script>alert('SIRET Updated Successfully!'); window.location.href='/';</script>"
