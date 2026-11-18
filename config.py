import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'nutritrack.db'}")
SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-this-secret-key")
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "12"))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@nutritrack.local").lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeThisAdminPassword123!")
