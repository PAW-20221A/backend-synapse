from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str | None = None
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Transcript API
    transcript_api_base_url: str = "https://transcriptapi.com/api/v2"
    transcript_api_key: str = ""

    # LLM
    openai_api_key: str = ""
    groq_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = (
                f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self


settings = Settings()
