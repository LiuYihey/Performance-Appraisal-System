from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 企微凭证
    WECOM_CORP_ID: str
    WECOM_AGENT_ID: str
    WECOM_SECRET: str

    # 数据库
    DATABASE_URL: str = "mysql+aiomysql://perf:perf2026@localhost:3306/perf_system"

    # 应用
    APP_SECRET_KEY: str = "change-me-in-production"
    APP_BASE_URL: str = "http://localhost:8000"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
