import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time

# Retry connection logic
def get_engine():
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(
                f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
                f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
            )
            engine.connect()
            return engine
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)
            continue

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    import time
    max_retries = 5
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Retrying database creation (attempt {attempt + 1})...")
            time.sleep(5)