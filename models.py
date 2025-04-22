import os
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    date = Column(String)
    time = Column(String)
    task = Column(String)

class ChatLog(Base):
    __tablename__ = 'chat_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    message = Column(String)
    response = Column(String)
    timestamp = Column(DateTime)  # ← datetime型で管理すると後で便利！

# RailwayのDATABASE_URLで接続（なければローカルSQLiteをfallback）
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# テーブル自動作成
Base.metadata.create_all(engine)