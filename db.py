import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from models import Task, ChatLog
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def _clean_time(val):
    # "未定"や空文字、Noneは全部Noneにする
    if val in [None, "", "未定"]:
        return None
    return val

def add_task(user_id, date, time, task_content):
    with SessionLocal() as session:
        try:
            task = Task(
                user_id=user_id,
                date=date,
                time=_clean_time(time),
                task=task_content
            )
            session.add(task)
            session.commit()
        except SQLAlchemyError as e:
            print("❌ add_task エラー:", e)
            session.rollback()

def get_all_tasks(user_id):
    with SessionLocal() as session:
        try:
            return session.query(Task).filter(Task.user_id == user_id).all()
        except SQLAlchemyError as e:
            print("❌ get_all_tasks エラー:", e)
            return []

def delete_task_by_details(user_id, date, task_content):
    with SessionLocal() as session:
        try:
            tasks_to_delete = session.query(Task).filter(
                Task.user_id == user_id,
                Task.date == date,
                Task.task == task_content
            ).all()
            if tasks_to_delete:
                for task in tasks_to_delete:
                    session.delete(task)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            print("❌ delete_task エラー:", e)
            session.rollback()
            return False

def save_chat_log(user_id, message, response):
    with SessionLocal() as session:
        try:
            log = ChatLog(
                user_id=user_id,
                message=message,
                response=response,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(log)
            session.commit()
        except SQLAlchemyError as e:
            print("❌ save_chat_log エラー:", e)
            session.rollback()

def get_recent_chat_logs(user_id, limit=5):
    with SessionLocal() as session:
        try:
            logs = (
                session.query(ChatLog)
                .filter(ChatLog.user_id == user_id)
                .order_by(ChatLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [{"message": log.message, "response": log.response} for log in logs]
        except SQLAlchemyError as e:
            print("❌ get_recent_chat_logs エラー:", e)
            return []

def update_task(user_id, old_date, old_time, old_task, new_date, new_time, new_task):
    with SessionLocal() as session:
        try:
            task = session.query(Task).filter_by(
                user_id=user_id,
                date=old_date,
                time=_clean_time(old_time),
                task=old_task
            ).first()
            if task:
                task.date = new_date
                task.time = _clean_time(new_time)
                task.task = new_task
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            print("❌ update_task エラー:", e)
            session.rollback()
            return False

def get_all_user_ids():
    with SessionLocal() as session:
        try:
            user_ids = session.query(Task.user_id).distinct().all()
            return [uid[0] for uid in user_ids]
        except SQLAlchemyError as e:
            print("❌ get_all_user_ids エラー:", e)
            return []