from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GHANA_NLP_API_KEY: str
    GROQ_API_KEY: str
    AUDIO_STORAGE_PATH: str
    SCIENTIFIC_WORDS_FILE: str
    DEFAULT_MALE_VOICE: str
    DEFAULT_FEMALE_VOICE: str


VOICE_MAP = {
    "Kofi": "male_low",
    "Ama": "male_high",
    "Akua": "female",
}

settings = Settings()
settings.AUDIO_STORAGE_PATH = str(Path(settings.AUDIO_STORAGE_PATH).expanduser())
Path(settings.AUDIO_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

