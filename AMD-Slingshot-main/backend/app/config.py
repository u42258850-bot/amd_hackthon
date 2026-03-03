from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgriSoil AI Backend"
    environment: str = "development"
    api_prefix: str = "/api"
    mongo_uri: str | None = None
    mongo_db_name: str = "agrisoil"
    weather_api_base_url: str = "https://api.open-meteo.com/v1/forecast"
    firebase_project_id: str
    firebase_service_account_path: str | None = None
    firebase_service_account_json: str | None = None
    allow_dev_auth_bypass: bool = True
    require_db_on_startup: bool = False
    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "uploads"
    static_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        normalized: list[str] = []
        for origin in self.cors_origins.split(","):
            cleaned = origin.strip().rstrip("/")
            if cleaned:
                normalized.append(cleaned)
        return normalized


settings = Settings()
