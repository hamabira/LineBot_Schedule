import os
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .envを読み込む
load_dotenv()

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
    timestamp = Column(DateTime)  # datetime型で管理して便利！

# DATABASE_URLを.envから取得
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# テーブル自動作成（開発時やcreate_tables.pyで実行！）
Base.metadata.create_all(engine)