import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallbacksecret")
    MONGO_URI = os.getenv("MONGO_URI")
    APP_PASSWORD = os.getenv("APP_PASSWORD", "emekaok123")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    SESSION_PERMANENT = True
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30  # 30 days
