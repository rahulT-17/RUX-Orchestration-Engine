# MEMORY / database.py : This file handles , engine creation , session creation , dependecy injection 


import os 
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Set it in environment variables.")

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"
# creating a connection pool to PostgreSQL :
engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO

)

# Creating session factory : 
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False 
)

Base = declarative_base()

# DEPENDENCY :
async def get_db() :
    async with AsyncSessionLocal() as session :
        yield session