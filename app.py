import json
import os
import traceback
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from gemini_util import analyze_task
from db import add_task, get_all_tasks, delete_task_by_details, save_chat_log, update_task

app = Flask(__name__)

# 🔐 LINEの設定
LINE_CHANNEL_ACCESS_TOKEN = 'Tv2tIB/qKJqSn5jiPnV/h+DBh2c66NDw82UuAbkuZvAdF5YJ7EkGwbpsQpJx7DqgymSd1iNfO49Zsz+m/2+JmcYs068O2Ku6JsOEFzJbhXwnUMg4+jx2otX+9pvSMAgZBRTGaa84PBRMJbwwBCcpWQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '031c826c752cd2ef1c10e86114d361b6'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    try:
        result = analyze_task(user_id,user_message)
        print("Geminiの応答:", result)

        if result.strip().startswith('{'):
            task_data = json.loads(result)
        else:
            response_text = result.strip()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=result.strip())
            )
            return

        action = task_data.get("action")

        if action == "show":
            period = task_data.get("period", "all")
            now = datetime.now()
            filtered_tasks = []

            for task in get_all_tasks(user_id):
                task_date = datetime.strptime(task.date, "%Y-%m-%d").date()
                if period == "today" and task_date == now.date():
                    filtered_tasks.append(task)
                elif period == "week" and now.date() <= task_date <= now.date() + timedelta(days=6):
                    filtered_tasks.append(task)
                elif period == "all":
                    filtered_tasks.append(task)

            if not filtered_tasks:
                response_text = "\U0001F4ED 表示できる予定が見つかりませんでした！"
            else:
                filtered_tasks.sort(key=lambda x: (x.date, x.time))
                response_text = "\U0001F4C5 予定一覧：\n"
                for i, task in enumerate(filtered_tasks, 1):
                    response_text += f"{i}. {task.date} {task.time} - {task.task}\n"

        elif action == "chat":
            response_text = task_data.get("response", "\U0001F60A どうしましたか？")

        elif action == "delete":
            date = task_data.get("date")
            task_text = task_data.get("task")
            if date and task_text:
                success = delete_task_by_details(user_id, date, task_text)
                if success:
                    response_text = f"\U0001F5D1️ 次の予定を削除しました：\n\U0001F4C5 {date}\n\U0001F4DD {task_text}"
                else:
                    response_text = "❌ 指定された予定が見つかりませんでした。"
            else:
                response_text = "❌ 削除条件が不足しています。"

        elif action == "add":
            date = task_data.get("date")
            time = task_data.get("time")
            task_text = task_data.get("task")
            if date and time and task_text:
                add_task(user_id, date, time, task_text)
                response_text = f"✅ 予定を追加しました！\n\U0001F4C5 {date} {time}\n\U0001F4DD {task_text}"
            else:
                response_text = "❌ 予定の追加に必要な情報が不足しています。"

        elif action == "update":
            old_date = task_data.get("old_date")
            old_time = task_data.get("old_time")
            old_task = task_data.get("old_task")
            new_date = task_data.get("new_date")
            new_time = task_data.get("new_time")
            new_task = task_data.get("new_task")
            if all([old_date, old_time, old_task, new_date, new_time, new_task]):
                success = update_task(user_id, old_date, old_time, old_task, new_date, new_time, new_task)
                if success:
                    response_text = f"✅ 予定を変更したよ！\n📅 {old_date} {old_time}「{old_task}」→ {new_date} {new_time}「{new_task}」"
                else:
                    response_text = "❌ 変更対象の予定が見つからなかったよ！"
            else:
                response_text = "❌ 変更に必要な情報が足りないみたい！"

        else:
            response_text = "🤖 ごめんなさい、内容をうまく理解できませんでした\U0001F4A6"


        save_chat_log(user_id, user_message, response_text)

    except Exception as e:
        print("エラー:", e)
        traceback.print_exc()
        response_text = "予定の処理中にエラーが発生しました\U0001F4A6"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_text)
    )

if __name__ == "__main__":
    app.run(debug=True)
