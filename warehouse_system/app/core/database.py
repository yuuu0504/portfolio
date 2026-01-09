# app/core/database.py
import os
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from contextlib import asynccontextmanager

########### 防呆
from sqlalchemy import event
from sqlalchemy.engine import Engine

load_dotenv()

# 讀取環境變數
APP_ENV = os.getenv("APP_ENV", "development")
POSTGRES_URL = os.getenv("DATABASE_URL")
SQLITE_URL = os.getenv("SQLITE_URL", "sqlite+aiosqlite:///./local_dev.db")

# 判斷連線字串
if APP_ENV == "production":
    DATABASE_URL = POSTGRES_URL
    print("🚀 Using PostgreSQL Database")
else:
    DATABASE_URL = SQLITE_URL
    print("🛠️ Using SQLite Database (Development Mode)")

# 建立 Async Engine
# echo=True 會印出 SQL 語句，方便開發除錯
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

################### 外鑑保護資料不被刪
if "sqlite" in DATABASE_URL:
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# 依賴注入用的 Session 產生器
async def get_db():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

# 初始化 DB (用於 SQLite 快速建立 Table，正規做法是用 Alembic)
async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # 開發初期若要重置可打開
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_db_session_context():
    """提供給非 FastAPI Depends 使用的 Context Manager (例如 seed.py)"""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session