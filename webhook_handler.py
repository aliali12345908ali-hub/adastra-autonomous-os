import sqlite3


def handle_successful_payment(session_id, customer_email, amount):
  conn = None
  try:
    conn = sqlite3.connect("adastra_os.db")
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT OR REPLACE INTO transactions (session_id, customer_email, amount, status)
            VALUES (?, ?, ?, 'paid')
        """,
        (session_id, customer_email, amount),
    )
    conn.commit()
    print(f"Payment recorded for {customer_email}, Amount: {amount}")
  except Exception as e:
    print(f"Database error during payment handling: {e}")
  finally:
    if conn:
      conn.close()


if __name__ == "__main__":
  print("Webhook Handler Ready.")


