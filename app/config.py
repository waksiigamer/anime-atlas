import os
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    base_dir: Path = Path(__file__).resolve().parents[1]

    @property
    def database_path(self) -> Path:
        configured = os.getenv("ANIME_DATABASE_PATH")
        return (
            Path(configured)
            if configured
            else self.base_dir.parent / "anime-catalog" / "anime-data.db"
        )

    @property
    def session_secret(self) -> str:
        secret = os.getenv("ANIME_SESSION_SECRET")

        # if not secret:
        #     raise RuntimeError("ANIME_SESSION_SECRET must be configured")

        return secret


settings = Settings()