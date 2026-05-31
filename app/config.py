from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/orchestrator"
    REDIS_URL: str = "redis://redis:6379/0"
    WORKFLOW_STREAM: str = "workflow_stream"

    class Config:
        env_file = ".env"


settings = Settings()