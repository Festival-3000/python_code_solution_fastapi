from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from decouple import config


# Create the database engine and session
engine = create_engine(
    f"mysql://{config('MYSQL_USER')}:{quote_plus(config('MYSQL_PASSWORD'))}@{config('MYSQL_HOST')}:{config('MYSQL_PORT')}/{config('MYSQL_DATABASE')}",
    echo=True,  # Set to False in production
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database model for users
Base = declarative_base()

# Create the database schema if not exists
Base.metadata.create_all(engine)

def get_db():
    """
    Connects to the DB
    """
    try:
        _db = SessionLocal()
        yield _db
    finally:
        _db.close()