import sqlite3
import os
from datetime import datetime
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Adastra Autonomous OS", version="2.0")

DB_PATH = "adastra.db"
OWNER = "MR ABDALLAH BEN BELGACEM"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
async def home():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, created_at FROM clients ORDER BY id DESC")
    clients = cursor.fetchall()
    conn.close()

    clients_rows = ""
    for c in clients:
        clients_rows += f"<tr><td>{c[0]}</td><td>{c[1]}</td><td>{c[2]}</td><td>{c[3]}</td><td>{c[4]}</td></tr>"

    if not clients_rows:
        clients_rows = "<tr><td colspan='5' style='text-align: center; color: #9ca3af;'>لا يوجد عملاء مسجلين حتى الآن</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Adastra Autonomous OS v2.0</title>
        <style>
            body {{ font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f3f4f6; padding: 20px; }}
            .container {{ max-width: 900px; margin: 20px auto; background: #111827; padding: 25px; border-radius: 12px; border: 1px solid #1f2937; }}
            h1, h2 {{ color: #0284c7; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #1f2937; padding: 10px; text-align: right; }}
            th {{ background: #1f2937; color: #0284c7; }}
            form {{ background: #1f2937; padding: 15px; border-radius: 8px; margin-top: 20px; }}
            input {{ width: 100%; padding: 8px; margin: 5px 0 15px 0; background: #111827; border: 1px solid #374151; color: white; border-radius: 4px; }}
            button {{ background: #0284c7; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }}
            button:hover {{ background: #0369a1; }}
            .nav {{ text-align: center; margin-bottom: 20px; }}
            .nav a {{ color: #0284c7; text-decoration: none; font-weight: bold; margin: 0 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Adastra Autonomous OS v2.0</h1>
            <p style="text-align: center; color: #9ca3af;">المالك والمطور: {OWNER}</p>
            
            <div class="nav">
                <a href="/">الرئيسية والعملاء</a> | 
                <a href="/license">رخصة الاستخدام</a>
            </div>
            
            <h2>إضافة عميل جديد</h2>
            <form action="/add-client" method="POST">
                <label>اسم العميل:</label>
                <input type="text" name="name" required>
                <label>البريد الإلكتروني:</label>
                <input type="email" name="email">
                <label>رقم الهاتف:</label>
                <input type="text" name="phone">
                <button type="submit">حفظ العميل</button>
            </form>

            <h2>قائمة العملاء المسجلين</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>الاسم</th>
                        <th>البريد الإلكتروني</th>
                        <th>الهاتف</th>
                        <th>وقت التسجيل</th>
                    </tr>
                </thead>
                <tbody>
                    {clients_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

@app.get("/license", response_class=HTMLResponse)
async def license_page():
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>رخصة النظام - Adastra</title>
        <style>
            body {{ font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f3f4f6; padding: 20px; }}
            .container {{ max-width: 800px; margin: 40px auto; background: #111827; padding: 30px; border-radius: 12px; border: 1px solid #1f2937; line-height: 1.8; }}
            h1 {{ color: #0284c7; text-align: center; }}
            .nav {{ text-align: center; margin-top: 20px; }}
            .nav a {{ color: #0284c7; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>رخصة الاستخدام والملكية الفكرية</h1>
            <p><strong>اسم النظام:</strong> Adastra Autonomous OS v2.0</p>
            <p><strong>المالك الحصري والمطور:</strong> {OWNER}</p>
            <hr style="border: 0; border-top: 1px solid #1f2937; margin: 20px 0;">
            <p>جميع الحقوق محفوظة © 2026. هذا النظام محمي بموجب قوانين الملكية الفكرية. لايحق لأي جهة نسخ، أو تعديل، أو إعادة توزيع هذا الكود أو استخدامه تجارياً دون إذن خطي صريح ومسبق من المالك.</p>
            <div class="nav">
                <a href="/">← العودة إلى الصفحة الرئيسية</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.post("/add-client", response_class=HTMLResponse)
async def add_client(name: str = Form(...), email: str = Form(""), phone: str = Form("")):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO clients (name, email, phone, created_at) VALUES (?, ?, ?, ?)", (name, email, phone, created_at))
    conn.commit()
    conn.close()
    return """
    <script>
        alert("تم إضافة العميل بنجاح!");
        window.location.href = "/";
    </script>
    """
