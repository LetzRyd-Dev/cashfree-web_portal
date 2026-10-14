import os
import urllib.parse
from pathlib import Path

# Load .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

class Settings:
    PROJECT_NAME: str = "LetzRyd Partner App Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    DB_HOST: str = os.getenv("DB_HOST", "35.200.196.113")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    # DB_PASS must come from environment — no hardcoded default for security.
    # Cloud Run injects this via Secret Manager; local dev uses .env file.
    DB_PASS: str = os.getenv("DB_PASS", "")
    
    _encoded_pass = urllib.parse.quote_plus(DB_PASS)
    _encoded_user = urllib.parse.quote_plus(DB_USER)
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{_encoded_user}:{_encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # SECRET_KEY must come from environment in production.
    # If unset in production, generate a secure random 256-bit key to prevent token forgery.
    _default_secret = os.getenv("SECRET_KEY")
    if not _default_secret:
        if os.getenv("CASHFREE_ENV", "").upper() == "PRODUCTION" or os.getenv("ENVIRONMENT", "").lower() == "production":
            import secrets
            _default_secret = secrets.token_urlsafe(32)
        else:
            _default_secret = "letzryd_dev_secret_key_2026"
    SECRET_KEY: str = _default_secret
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))

    CASHFREE_APP_ID: str = os.getenv("CASHFREE_APP_ID", "CF_APP_LETZRYD_TEST")
    CASHFREE_SECRET_KEY: str = os.getenv("CASHFREE_SECRET_KEY", "CF_SECRET_LETZRYD_TEST_2026")
    CASHFREE_ENV: str = os.getenv("CASHFREE_ENV", "SANDBOX")
    CASHFREE_API_VERSION: str = os.getenv("CASHFREE_API_VERSION", "2023-08-01")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @property
    def CASHFREE_BASE_URL(self) -> str:
        if self.CASHFREE_ENV.upper() == "PRODUCTION":
            return "https://api.cashfree.com/pg"
        return "https://sandbox.cashfree.com/pg"

settings = Settings()
