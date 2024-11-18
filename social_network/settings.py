from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_TIME_SECONDS: int

    PORT: int = 8000

    NEO_PASSWORD: str
    NEO_PORT: int = 7687
    NEO_URL: str | None = None

    @property
    def neo4j_url(self):
        return self.NEO_URL if self.NEO_URL else f"bolt://neo4j:{self.NEO_PORT}"


settings = Settings()
