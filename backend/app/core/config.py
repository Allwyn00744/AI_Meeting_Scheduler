from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Meeting Scheduler"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # JWT
    SECRET_KEY: str = "9xxsdIpdEEEgivQDmXEqhD9xDHc9On3OUY1mlXE5UPqpt_IopV1r-tUJGSaTG5BVuneu0Pmdkf-vjusgo3vAew"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()