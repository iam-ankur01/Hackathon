from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    GROQ_API_KEY: str = ""

    FIREBASE_CREDENTIALS: str = "./firebase-service-account.json"
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_STORAGE_BUCKET: str = ""

    FRONTEND_ORIGIN: str = "http://localhost:5173"
    UPLOAD_DIR: str = "./uploads"


settings = Settings()
