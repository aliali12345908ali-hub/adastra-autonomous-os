import json

def process_subscription(user_id, plan_type="pro"):
    """
    نظام تجريبي لإدارة الاشتراكات وتفعيل الخدمات المدفوعة لـ Adastra Autonomous OS
    """
    pricing = {
        "basic": 10,
        "pro": 29,
        "enterprise": 99
    }
    
    amount = pricing.get(plan_type, 10)
    
    response = {
        "status": "success",
        "user_id": user_id,
        "plan": plan_type,
        "amount_usd": amount,
        "message": f"User {user_id} successfully subscribed to {plan_type} plan for ${amount}."
    }
    
    print(json.dumps(response, indent=4))
    return response

if __name__ == "__main__":
    # محاكاة اشتراك تجريبي لمستخدم جديد
    process_subscription("user_abdullah_123", "pro")
