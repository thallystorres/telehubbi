from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: SecretStr
    DATABASE_URL_TESTE: SecretStr
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    LIMITE_LEITURAS_CRUAS: int = 1000
    TOLERANCIA_FUTURO_S: int = 5
    JANELA_MAXIMA_CONSULTA_H: int = 72
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
