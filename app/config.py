import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("DB_PATH", "./data/app.db")

settings = Settings()
