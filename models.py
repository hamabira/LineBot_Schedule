from sqlalchemy import Column, Integer, String, Date, Time, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    date = Column(String)
    time = Column(String)
    task = Column(String)

class ChatLog(Base):
    __tablename__ = 'chat_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(String)  # ユーザーごとに分けるなら
    message = Column(String)
    response = Column(String)
    timestamp = Column(String)  # datetime型でもOK（strなら管理が簡単）


# SQLiteでtasks.dbを作成
engine = create_engine('sqlite:///tasks.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
