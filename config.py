import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GOOGLE_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

    DB_URL: str = os.getenv("DB_URL", "sqlite:///data/employees.db")

    MAX_FIX_ATTEMPTS: int = int(os.getenv("MAX_FIX_ATTEMPTS", "3"))


settings = Settings()
