from fastapi import FastAPI, HTTPException, Request
import sqlite3
import stripe

app = FastAPI()


def check_user_payment_status(customer_email: str) -> bool:
  conn = None
  try:
    conn = sqlite3.connect("adastra_os.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status FROM transactions WHERE customer_email = ? AND status ="
        " 'paid'",
        (customer_email,),
    )
    result = cursor.fetchone()
    return result is not None
  except Exception as e:
    print(f"Error checking payment: {e}")
    return False
  finally:
    if conn:
      conn.close()


@app.get("/api/get-protected-info")
def get_protected_info(customer_email: str):
  if not check_user_payment_status(customer_email):
    raise HTTPException(
        status_code=403,
        detail="Access Denied: Payment is required before receiving information.",
    )

  return {
      "status": "success",
      "message": "Payment verified. Here is your confidential information.",
      "data": {"autonomous_system_status": "Operational"},
  }


