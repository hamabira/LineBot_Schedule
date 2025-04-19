from models import Task, Session, ChatLog
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

def add_task(date, time, task_content):
    session = Session()
    try:
        task = Task(date=date, time=time, task=task_content)
        session.add(task)
        session.commit()
    except SQLAlchemyError as e:
        print("❌ add_task エラー:", e)
        session.rollback()
    finally:
        session.close()

def get_all_tasks():
    session = Session()
    try:
        return session.query(Task).all()
    except SQLAlchemyError as e:
        print("❌ get_all_tasks エラー:", e)
        return []
    finally:
        session.close()

def delete_task_by_details(date, task_content):
    session = Session()
    try:
        tasks_to_delete = session.query(Task).filter(Task.date == date, Task.task == task_content).all()
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
    finally:
        session.close()

def save_chat_log(user_id, message, response):
    session = Session()
    try:
        log = ChatLog(
            user_id=user_id,
            message=message,
            response=response,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(log)
        session.commit()
    except Exception as e:
        print("❌ save_chat_log エラー:", e)
        session.rollback()
    finally:
        session.close()

def get_recent_chat_logs(user_id, limit=5):
    session = Session()
    try:
        logs = (
            session.query(ChatLog)
            .filter(ChatLog.user_id == user_id)
            .order_by(ChatLog.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [{"message": log.message, "response": log.response} for log in logs]
    except Exception as e:
        print("❌ get_recent_chat_logs エラー:", e)
        return []
    finally:
        session.close()
