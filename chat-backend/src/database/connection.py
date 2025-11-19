from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config.config import Config


DATABASE_URL = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency para obtener sesión de base de datos
    Usado en FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
