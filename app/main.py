import os

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_USER or not ADMIN_PASSWORD:
    raise ValueError(
        "Critical Security Error: Admin credentials must be set via environment variables."
    )

import htm


import os
import shutil
from fastapi import HTTPException


@app.get("/api/backup")
def create_backup():
  db_path = "app.db"
  backup_path = "backup_app.db"

  if os.path.exists(db_path):
    shutil.copy(db_path, backup_path)
    return {
        "status": "success",
        "message": "Actual backup created successfully",
        "backup_file": backup_path,
    }
  else:
    raise HTTPException(status_code=404, detail="Database file not found")

import stripe
from fastapi import Header, HTTPException, Request

# إعداد مفتاح Stripe السري من متغيرات البيئة
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
ENDPOINT_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


@app.post("/api/webhook/stripe")
async def stripe_webhook(
    request: Request, stripe_signature: str = Header(None)
):
  payload = await request.body()
  try:
    event = stripe.Webhook.construct_event(
        payload, stripe_signature, ENDPOINT_SECRET
    )
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid payload")
  except stripe.error.SignatureVerificationError:
    raise HTTPException(status_code=400, detail="Invalid signature")

  # التحقق من نجاح عملية الدفع
  if event["type"] == "payment_intent.succeeded":
    payment_intent = event["data"]["object"]
    print(f"Payment successful for ID: {payment_intent['id']}")
    # هنا يمكنك إضافة كود تحديث حالة الطلب في قاعدة البيانات ليصبح مدفوعاً

  return {"status": "success"}


