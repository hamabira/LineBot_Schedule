import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from linebot import LineBotApi
from linebot.models import TextSendMessage
from db import get_all_tasks, get_all_user_ids
from app import make_day_response

# トークンは環境変数から取るようにしよう！
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def push_today_schedule():
    # 日本時間で7時に送りたい場合、UTC+9に合わせる
    now_utc = datetime.utcnow()
    now_japan = now_utc + timedelta(hours=9)
    today_str = now_japan.strftime("%Y-%m-%d")

    user_ids = get_all_user_ids()
    for user_id in user_ids:
        all_tasks = get_all_tasks(user_id)
        # t.dateがstr型("YYYY-MM-DD")前提！
        tasks_today = [t for t in all_tasks if t.date == today_str]
        message = make_day_response(tasks_today, now_japan.date(), "今日")
        try:
            line_bot_api.push_message(user_id, TextSendMessage(text=message))
            print(f"{user_id} に今日の予定を送ったぜ！")
        except Exception as e:
            print(f"{user_id} へのpushでエラー: {e}")

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    # UTCで22時＝日本時間7時
    scheduler.add_job(push_today_schedule, 'cron', hour=22, minute=0)
    scheduler.start()
    print("全ユーザーに毎朝7時(JST)の自動通知が稼働したぜ！")

    # 無限ループでプロセス維持（APSchedulerのみの場合）
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()