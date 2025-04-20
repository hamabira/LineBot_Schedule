from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
from db import get_all_tasks, get_all_user_ids  # ← 追加！

from app import make_day_response

LINE_CHANNEL_ACCESS_TOKEN = 'Tv2tIB/qKJqSn5jiPnV/h+DBh2c66NDw82UuAbkuZvAdF5YJ7EkGwbpsQpJx7DqgymSd1iNfO49Zsz+m/2+JmcYs068O2Ku6JsOEFzJbhXwnUMg4+jx2otX+9pvSMAgZBRTGaa84PBRMJbwwBCcpWQdB04t89/1O/w1cDnyilFU='

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def push_today_schedule():
    today = datetime.now().date()
    user_ids = get_all_user_ids()  # ここで全ユーザーのuser_idリストを取得！
    for user_id in user_ids:
        all_tasks = get_all_tasks(user_id)
        tasks_today = [t for t in all_tasks if t.date == today.strftime("%Y-%m-%d")]
        message = make_day_response(tasks_today, today, "今日")
        try:
            line_bot_api.push_message(user_id, TextSendMessage(text=message))
            print(f"{user_id} に今日の予定を送ったぜ！")
        except Exception as e:
            print(f"{user_id} へのpushでエラー: {e}")

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(push_today_schedule, 'cron', hour=7, minute=0)
    scheduler.start()
    print("全ユーザーに毎朝7時の自動通知が稼働したぜ！")