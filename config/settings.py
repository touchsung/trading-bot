from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    MARKET_PHASES: dict
    MARKET_HOLIDAYS: list
    ACCOUNT_NO: str
    ACCOUNT_BROKER: str
    DISCORD_WEBHOOK_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
