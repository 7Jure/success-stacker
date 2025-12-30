import os
from datetime import timedelta
from pathlib import Path

# Apsolutni path do projekta
BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Apsolutni path za SQLite
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR}/instance/database.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
