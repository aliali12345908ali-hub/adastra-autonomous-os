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

