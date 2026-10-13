import time
import sqlite3

def check_system_health():
    conn = sqlite3.connect('adastra_os.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE status='paid'")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"Autonomous Worker Check: Total successful transactions = {count}")

if __name__ == "__main__":
    check_system_health()
