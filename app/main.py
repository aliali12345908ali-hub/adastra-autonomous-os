import os

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_USER or not ADMIN_PASSWORD:
    raise ValueError(
        "Critical Security Error: Admin credentials must be set via environment variables."
    )

import htm


