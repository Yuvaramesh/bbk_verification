import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB = "bbk"

    # Email Configuration
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USER = os.getenv("EMAIL_USER", "your-email@gmail.com")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")

    # App Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_ENV") == "development"

    # FirmCheck Mock Configuration
    FIRMCHECK_API_URL = "https://api.firmcheck.com/verify"  # Replace with real endpoint
    FIRMCHECK_API_KEY = os.getenv("FIRMCHECK_API_KEY", "mock-key")

    # Admin Settings
    ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "admin@company.com").split(",")
    CEO_EMAIL = os.getenv("CEO_EMAIL", "ceo@company.com")

    # File Upload
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif"}

    # Google Gemini API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
