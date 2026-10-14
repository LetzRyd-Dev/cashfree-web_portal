import psycopg2
from psycopg2 import pool
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLAlchemy Engine & Session
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    connect_args={
        "connect_timeout": 10,
        "options": "-c lock_timeout=5000ms",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_psycopg_pool = None

def get_raw_pool():
    global _psycopg_pool
    if _psycopg_pool is None:
        _psycopg_pool = pool.ThreadedConnectionPool(1, 20, dsn=settings.DATABASE_URL, connect_timeout=10)
    return _psycopg_pool

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_raw_db_conn():
    p = get_raw_pool()
    conn = p.getconn()
    try:
        yield conn
    finally:
        p.putconn(conn)
