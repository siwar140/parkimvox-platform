"""
Configuration centralisée : toutes les valeurs sensibles/variables
sont lues depuis le fichier .env (voir .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB Atlas
    mongo_uri: str
    mongo_db_name: str = "parkimvox"

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Modèle Deep Learning
    model_path: str = "models_data/best_model.keras"
    norm_stats_path: str = "models_data/norm_stats.json"
    decision_threshold: float = 0.6952

    # CORS
    cors_origins: str = "http://localhost:5500"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
