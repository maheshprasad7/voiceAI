import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ELEVENLABS_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM" # Hardcoded Rachel voice ID
    MODEL_NAME: str = "gemini-2.5-flash"
    
    MIC_DEVICE_INDEX: int = 0
    SPEAKER_DEVICE_INDEX: int = 0
    
    PORT: int = 8080
    HOST: str = "0.0.0.0"
    
    WAKE_WORD: str = "Hello"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
