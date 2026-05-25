from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Chrona API"
    VERSION: str = "1.0.0"
    MEMGRAPH_URI: str = "bolt://localhost:7687"
    MEMGRAPH_USER: str = ""
    MEMGRAPH_PASSWORD: str = ""
    GROQ_API_KEY: str = ""
    DATADOG_API_KEY: str = ""
    DATADOG_APP_KEY: str = ""
    DATADOG_SITE: str = "datadoghq.com"
    GRAFANA_URL: str = ""
    GRAFANA_API_KEY: str = ""
    NEWRELIC_API_KEY: str = ""
    NEWRELIC_ACCOUNT_ID: str = ""
    TELEMETRY_MODE: str = "file"
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()