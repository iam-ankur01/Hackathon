from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    GROQ_API_KEY: str = ""

    FIREBASE_CREDENTIALS: str = "./firebase-service-account.json"
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_STORAGE_BUCKET: str = ""
    USE_LOCAL_DB: bool = False
    LOCAL_DB_PATH: str = "./local_data.json"

    FRONTEND_ORIGIN: str = "http://localhost:5173"
    UPLOAD_DIR: str = "./uploads"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    def validate_production(self) -> None:
        if not self.is_production:
            return
        missing = []
        if self.SECRET_KEY == "dev-secret-change-me" or len(self.SECRET_KEY) < 32:
            missing.append("SECRET_KEY (minimum 32 characters)")
        if not self.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if not self.FIREBASE_CREDENTIALS_JSON:
            missing.append("FIREBASE_CREDENTIALS_JSON")
        if not self.FIREBASE_STORAGE_BUCKET:
            missing.append("FIREBASE_STORAGE_BUCKET")
        if self.USE_LOCAL_DB:
            missing.append("USE_LOCAL_DB must be false")
        if not self.FRONTEND_ORIGIN.startswith("https://"):
            missing.append("FRONTEND_ORIGIN must use https://")
        if missing:
            raise RuntimeError(
                "Invalid production configuration: " + "; ".join(missing)
            )


settings = Settings()
