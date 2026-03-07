"""
Application-wide configuration.

Loads environment variables from a .env file and exposes them
through a Settings object. Any module that needs config values
(DB URL, API keys, etc.) should import `settings` from here.
"""

import os
from dotenv import load_dotenv

# Load .env file from the backend root directory.
# This needs to run before we read any os.getenv() calls.
load_dotenv()


class Settings:
    # Database URL — defaults to a local SQLite file for development.
    # In production, this gets overridden via environment variable to a PostgreSQL URI.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

    # OpenAI key used by all four LangChain agents.
    # Left empty by default so the app can still start without it (for DB/OR work).
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


# Single shared instance — import this everywhere instead of creating new Settings().
settings = Settings()