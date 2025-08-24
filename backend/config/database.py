import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_HOST = os.getenv("DB_HOST", "sql12.freesqldatabase.com")
DB_NAME = os.getenv("DB_NAME", "sql12795688")
DB_USER = os.getenv("DB_USER", "sql12795688")
DB_PASSWORD = os.getenv("DB_PASSWORD", "VATyekp2U8")
DB_PORT = os.getenv("DB_PORT", "3306")

# Create database URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
