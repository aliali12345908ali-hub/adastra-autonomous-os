import sqlite3
import shutil
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Adastra Autonomous OS", version="2.0")

DB_PATH = "adastra.db"
OWNER = "MR ABDALLAH BEN BELGACEM"

class AIRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Adastra Autonomous OS v2.0</title>
        <style>
            body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f3f4f6; padding: 20px; }
            .container { max-width: 900px; margin: 20px auto; background: #111827; padding: 25px; border-radius: 12px; border: 1px solid #1f2937; }
            h1 { color: #0284c7; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Adastra Autonomous OS v2.0</h1>
            <p>المشروع يعمل بنجاح تام.</p>
        </div>
    </body>
    </html>
    """

@app.get("/api/v1/finance")
async def get_finance():
    return {"status": "success", "system": "Adastra Autonomous OS", "owner": OWNER}
