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
    DB_PASS: str = os.getenv("DB_PASS", "8S5]U3@L^Xz)\\FH}")
    
    _encoded_pass = urllib.parse.quote_plus(DB_PASS)
    _encoded_user = urllib.parse.quote_plus(DB_USER)
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{_encoded_user}:{_encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "letzryd_secret_key_partner_app_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))

    CASHFREE_APP_ID: str = os.getenv("CASHFREE_APP_ID", "")
    CASHFREE_SECRET_KEY: str = os.getenv("CASHFREE_SECRET_KEY", "")
    CASHFREE_ENV: str = os.getenv("CASHFREE_ENV", "SANDBOX")
    CASHFREE_API_VERSION: str = os.getenv("CASHFREE_API_VERSION", "2023-08-01")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @property
    def CASHFREE_BASE_URL(self) -> str:
        if self.CASHFREE_ENV.upper() == "PRODUCTION":
            return "https://api.cashfree.com/pg"
        return "https://sandbox.cashfree.com/pg"

settings = Settings()
