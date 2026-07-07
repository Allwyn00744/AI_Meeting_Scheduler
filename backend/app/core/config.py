from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Meeting Scheduler"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str

    # Set to true only for local debugging. Logs every SQL statement
    # (including bound parameter values), which is noisy and can leak
    # sensitive data into logs/console output if left on in production.
    SQLALCHEMY_ECHO: bool = False

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str

    # If true, connect using implicit SSL (typically port 465) via
    # smtplib.SMTP_SSL instead of plaintext + STARTTLS (typically
    # port 587). Defaults to STARTTLS since that's what the provider
    # this app was built against (Gmail SMTP, port 587) expects.
    EMAIL_USE_SSL: bool = False
    EMAIL_TIMEOUT_SECONDS: int = 10

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # JWT
    # No default on purpose: the application must fail fast at
    # startup if this is not supplied via environment/.env, rather
    # than silently falling back to a value baked into source control.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Comma-separated list of allowed frontend origins for CORS, e.g.
    # "http://localhost:3000,https://app.example.com". Never include
    # "*" here — a wildcard origin combined with credentialed
    # requests (cookies/Authorization headers) is rejected by
    # browsers anyway and is not a safe configuration.
    CORS_ORIGINS: str = "http://localhost:3000"

    # Default page size / max page size for list endpoints that
    # support pagination.
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]
        # Defensively strip any wildcard that might get configured -
        # this app always sends credentials (Authorization headers),
        # and a wildcard origin must never be combined with that.
        return [origin for origin in origins if origin != "*"]


settings = Settings()
