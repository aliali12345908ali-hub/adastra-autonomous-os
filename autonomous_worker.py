import time
import requests

API_URL = "http://localhost:8095/api/v1"

def run_autonomous_cycle():
    try:
        # 1. فحص موارد الجهاز تلقائياً
        shell_res = requests.post(f"{API_URL}/run-shell", json={"command": "uptime"})
        
        # 2. إرسال البيانات للذكاء الاصطناعي لاتخاذ قرار أو إعداد تقرير
        ai_res = requests.post(f"{API_URL}/ai", json={"prompt": f"System uptime data: {shell_res.json().get('stdout')}. Optimize if needed."})
        
        print("[AUTONOMOUS WORKER] Cycle executed successfully.")
    except Exception as e:
        print(f"[AUTONOMOUS WORKER] Error: {e}")

if __name__ == "__main__":
    while True:
        run_autonomous_cycle()
        time.sleep(60)  # ينفذ دورة صيانة وتحليل كل 60 ثانية تلقائياً
