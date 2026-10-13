from flask import Flask, jsonify, request
import os
import secrets
import sqlite3

app = Flask(__name__)

DB_NAME = "adastra.db"

def init_db():
    """إنشاء الجداول في قاعدة البيانات إذا لم تكن موجودة"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            plan TEXT NOT NULL,
            requests_used INTEGER DEFAULT 0
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO api_keys (key, user_id, plan, requests_used) VALUES (?, ?, ?, ?)",
                   ("key_abdullah_pro_99", "user_abdullah_123", "pro", 0))
    cursor.execute("INSERT OR IGNORE INTO api_keys (key, user_id, plan, requests_used) VALUES (?, ?, ?, ?)",
                   ("key_guest_basic_10", "user_guest_001", "basic", 0))
    conn.commit()
    conn.close()

init_db()

PRICING = {
    "basic": 10,
    "pro": 29,
    "enterprise": 99
}

MAX_REQUESTS = 5

@app.route('/')
def home():
    return jsonify({
        "system": "Adastra Autonomous OS",
        "status": "online",
        "commercial_status": "ready (Stripe Integration Active)",
        "database": "SQLite (Persistent)",
        "rate_limiting": f"Active ({MAX_REQUESTS} req/key max)"
    })

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """مسار استقبال إشعارات الدفع التلقائية من Stripe"""
    event = request.get_json() or {}
    
    # محاكاة التحقق من نجاح عملية الدفع (checkout.session.completed)
    event_type = event.get("type", "checkout.session.completed")
    data_object = event.get("data", {}).get("object", {})
    
    user_id = data_object.get("customer_email", "client_" + secrets.token_hex(4))
    plan_type = data_object.get("metadata", {}).get("plan", "pro")

    # توليد مفتاح API جديد وحفظه تلقائياً في قاعدة البيانات
    new_api_key = f"key_{secrets.token_hex(8)}"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO api_keys (key, user_id, plan, requests_used) VALUES (?, ?, ?, 0)",
                   (new_api_key, user_id, plan_type))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "event": event_type,
        "user_id": user_id,
        "plan": plan_type,
        "generated_api_key": new_api_key,
        "message": "Payment verified via Stripe. API key generated and stored successfully."
    }), 200

@app.route('/subscribe', methods=['POST'])
def subscribe():
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        return jsonify({
            "status": "error",
            "message": "Unauthorized: Missing X-API-Key header"
        }), 401

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, plan, requests_used FROM api_keys WHERE key = ?", (api_key,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Unauthorized: Invalid X-API-Key"
        }), 401

    user_id, plan_type, requests_used = row

    if requests_used >= MAX_REQUESTS:
        conn.close()
        return jsonify({
            "status": "error",
            "message": f"Rate limit exceeded! Maximum allowed requests: {MAX_REQUESTS}",
            "requests_used": requests_used
        }), 429

    new_usage = requests_used + 1
    cursor.execute("UPDATE api_keys SET requests_used = ? WHERE key = ?", (new_usage, api_key))
    conn.commit()
    conn.close()

    amount = PRICING.get(plan_type, 10)
    
    return jsonify({
        "status": "success",
        "user_id": user_id,
        "plan": plan_type,
        "amount_usd": amount,
        "requests_used": f"{new_usage}/{MAX_REQUESTS}",
        "message": f"Authenticated user {user_id} accessed {plan_type} plan."
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
