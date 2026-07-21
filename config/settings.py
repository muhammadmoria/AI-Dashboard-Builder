"""Central application configuration."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    APP_NAME: str = "Nexus BI"
    APP_VERSION: str = "1.0.0"
    ROOT: Path = ROOT
    DB_PATH: Path = ROOT / "database" / "nexus.db"
    LOG_DIR: Path = ROOT / "logs"
    CACHE_DIR: Path = ROOT / "cache"
    UPLOAD_DIR: Path = ROOT / "cache" / "uploads"
    ASSETS_DIR: Path = ROOT / "assets"
    MODELS_DIR: Path = ROOT / "models"

    MAX_UPLOAD_MB: int = 500
    SAMPLE_N_ROWS: int = 100_000
    CHART_PALETTE: list = field(default_factory=lambda: [
        "#7C3AED", "#4F46E5", "#06B6D4", "#10B981", "#F59E0B",
        "#EF4444", "#EC4899", "#8B5CF6", "#14B8A6", "#F97316"
    ])

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ENABLE_OPENAI: bool = bool(OPENAI_API_KEY)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
    COOKIE_EXPIRY_DAYS: int = 30

    def ensure_dirs(self) -> None:
        for p in [self.LOG_DIR, self.CACHE_DIR, self.UPLOAD_DIR,
                  self.MODELS_DIR, self.DB_PATH.parent]:
            p.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()