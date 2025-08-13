from pathlib import Path
from pydantic_settings import BaseSettings
import base64

class Settings(BaseSettings):
    DATA_DIR: Path = Path(__file__).parent.parent / "data"
    MAX_CONTENT_LENGTH_MB: int = 200

    BROKER_URL: str = "redis://localhost:6379/0"
    RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"

settings = Settings()
