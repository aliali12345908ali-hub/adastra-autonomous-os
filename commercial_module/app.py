from flask import Flask, jsonify, request
import os

app = Flask(__name__)

PRICING = {
    "basic": 10,
    "pro": 29,
    "enterprise": 99
}

@app.route('/')
def home():
    return jsonify({
        "system": "Adastra Autonomous OS",
        "status": "online",
        "commercial_status": "ready"
    })

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json() or {}
    user_id = data.get("user_id", "guest")
    plan_type = data.get("plan", "pro")
    
    amount = PRICING.get(plan_type, 10)
    
    return jsonify({
        "status": "success",
        "user_id": user_id,
        "plan": plan_type,
        "amount_usd": amount,
        "message": f"User {user_id} successfully subscribed to {plan_type} plan for ${amount}."
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
