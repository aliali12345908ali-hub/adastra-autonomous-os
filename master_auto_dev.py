import os
import sys
import sqlite3
import subprocess
import datetime

def log_status(service_name, status, details=""):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{service_name}] -> {status}: {details}")

def check_database_service():
    """فحص قاعدة البيانات والتأكد من الجداول"""
    try:
        conn = sqlite3.connect('adastra_os.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        log_status("Database Service", "ACTIVE", f"Tables found: {tables}")
        return True
    except Exception as e:
        log_status("Database Service", "FAILED", str(e))
        return False

def check_stripe_service():
    """فحص وحدة التعامل المالي وإعدادات stripe"""
    try:
        import stripe_handler
        log_status("Stripe Payment Service", "ACTIVE", "Module loaded successfully")
        return True
    except Exception as e:
        log_status("Stripe Payment Service", "FAILED", str(e))
        return False

def check_webhook_service():
    """فحص معالج الـ Webhooks"""
    try:
        import webhook_handler
        log_status("Webhook Service", "ACTIVE", "Handler ready for incoming payloads")
        return True
    except Exception as e:
        log_status("Webhook Service", "FAILED", str(e))
        return False

def check_autonomous_worker():
    """فحص العقل الذاتي للنظام والتأكد من جاهزيته"""
    try:
        result = subprocess.run(["python", "autonomous_worker.py"], capture_output=True, text=True)
        if result.returncode == 0:
            log_status("Autonomous Worker", "ACTIVE", result.stdout.strip())
            return True
        else:
            log_status("Autonomous Worker", "ERROR", result.stderr.strip())
            return False
    except Exception as e:
        log_status("Autonomous Worker", "FAILED", str(e))
        return False

def run_full_system_auto_dev():
    print("==========================================")
    print("=== STARTING FULL SERVICES AUTO-DEV CHECK ===")
    print("==========================================")
    
    db_ok = check_database_service()
    stripe_ok = check_stripe_service()
    webhook_ok = check_webhook_service()
    worker_ok = check_autonomous_worker()

    if db_ok and stripe_ok and webhook_ok and worker_ok:
        print(">>> ALL SERVICES ARE RUNNING AUTONOMOUSLY AND HEALTHY! <<<")
    else:
        print(">>> WARNING: SOME SERVICES REQUIRE ATTENTION <<<")

if __name__ == "__main__":
    run_full_system_auto_dev()
