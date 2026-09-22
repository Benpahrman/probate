from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gieni OS Core"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "production"
    DATABASE_URL: Optional[str] = None
    
    # PostgreSQL Configuration
    POSTGRES_USER: str = "gieni_admin"
    POSTGRES_PASSWORD: str = "gieni_secure_pass"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gieni_production"

    @computed_field
    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL and "sqlite" in self.DATABASE_URL:
            return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
