import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./adastra.db")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    success_url: str = os.getenv("SUCCESS_URL", "http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}")
    cancel_url: str = os.getenv("CANCEL_URL", "http://localhost:8000/cancel")
    target_amount_cents: int = int(os.getenv("TARGET_AMOUNT_CENTS", "100000"))
    target_currency: str = os.getenv("TARGET_CURRENCY", "eur").lower()
    engine_switch: str = os.getenv("ADASTRA_ENGINE_SWITCH", "OFF")

settings = Settings()
