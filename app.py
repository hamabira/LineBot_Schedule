import json
import os
import traceback
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from gemini_util import analyze_task

app = Flask(__name__)

# 🔐 LINEの設定（自分のキー）
LINE_CHANNEL_ACCESS_TOKEN = 'Tv2tIB/qKJqSn5jiPnV/h+DBh2c66NDw82UuAbkuZvAdF5YJ7EkGwbpsQpJx7DqgymSd1iNfO49Zsz+m/2+JmcYs068O2Ku6JsOEFzJbhXwnUMg4+jx2otX+9pvSMAgZBRTGaa84PBRMJbwwBCcpWQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '031c826c752cd2ef1c10e86114d361b6'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 🔧 tasks.txt のパス（app.py のある場所に保存）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE = os.path.join(BASE_DIR, "tasks.txt")

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
    user_message = event.message.text.strip()

    try:
        result = analyze_task(user_message)
        print("Geminiの応答:", result)
        task_data = json.loads(result)

        action = task_data.get("action")

        if action == "show":
            if not os.path.exists(TASKS_FILE):
                open(TASKS_FILE, "w", encoding="utf-8").close()

            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = []
                for line in f:
                    if line.strip():
                        try:
                            tasks.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print("⚠️ JSON読み込みエラー:", e)
                            continue

            period = task_data.get("period", "all")
            now = datetime.now()
            filtered_tasks = []

            for task in tasks:
                try:
                    task_date = datetime.strptime(task["date"], "%Y-%m-%d").date()
                    if period == "today":
                        if task_date == now.date():
                            filtered_tasks.append(task)
                    elif period == "week":
                        if now.date() <= task_date <= now.date() + timedelta(days=6):
                            filtered_tasks.append(task)
                    else:
                        filtered_tasks.append(task)
                except Exception as e:
                    print("⛔ 日付変換エラー:", e)

            if not filtered_tasks:
                response_text = "📭 表示できる予定が見つかりませんでした！"
            else:
                # 日付＋時刻の順にソート
                filtered_tasks.sort(key=lambda x: (x["date"], x["time"]))

                response_text = "📅 予定一覧：\n"
                for i, task in enumerate(filtered_tasks, 1):
                    response_text += f"{i}. {task['date']} {task['time']} - {task['task']}\n"

        elif action == "chat":
            response_text = task_data.get("response", "😊 どうしましたか？")

        elif action == "delete":
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = f.readlines()

            index = task_data.get("index")
            if index is not None and 0 <= index < len(tasks):
                deleted_task = json.loads(tasks.pop(index))
                with open(TASKS_FILE, "w", encoding="utf-8") as f:
                    f.writelines(tasks)
                response_text = f"🗑️ 次の予定を削除しました：\n📅 {deleted_task['date']} {deleted_task['time']}\n📝 {deleted_task['task']}"

            elif "date" in task_data and "task" in task_data:
                target_date = task_data["date"]
                target_task = task_data["task"]
                new_tasks = []
                deleted = None

                for task_str in tasks:
                    if not task_str.strip():  # 空行をスキップ
                        continue
                    try:
                        task = json.loads(task_str)
                        # キーの存在を確認
                        if "date" in task and "task" in task:
                            if task["date"] == target_date and task["task"] == target_task and deleted is None:
                                deleted = task
                                continue
                        new_tasks.append(task_str)
                    except json.JSONDecodeError as e:
                        print("⚠️ JSON読み込みエラー:", e)
                        continue

                if deleted:
                    with open(TASKS_FILE, "w", encoding="utf-8") as f:
                        for task in new_tasks:
                            f.write(json.dumps(task, ensure_ascii=False) + "\n")
                    response_text = f"🗑️ 次の予定を削除しました：\n📅 {deleted['date']} {deleted['time']}\n📝 {deleted['task']}"
                else:
                    response_text = "❌ 指定された予定が見つかりませんでした。"

            else:
                response_text = "❌ 削除条件が不足しています。"

        elif action == "add":
            response_text = add_task(task_data)

        else:
            response_text = "🤖 ごめんなさい、内容をうまく理解できませんでした💦"

    except Exception as e:
        print("エラー:", e)
        traceback.print_exc()
        response_text = "予定の処理中にエラーが発生しました💦"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_text)
    )

def add_task(task_data):
    try:
        # JSON形式であることを確認
        task_json = json.dumps(task_data, ensure_ascii=False)
        with open(TASKS_FILE, "a", encoding="utf-8") as f:
            f.write(task_json + "\n")
        return f"✅ 予定を追加しました！\n📅 {task_data['date']} {task_data['time']}\n📝 {task_data['task']}"
    except (TypeError, ValueError) as e:
        print("❌ JSONエンコードエラー:", e)
        return "❌ 予定の追加中にエラーが発生しました。"

def load_tasks():
    tasks = []
    if not os.path.exists(TASKS_FILE):
        return tasks

    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    tasks.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print("⚠️ JSON読み込みエラー:", e)
                    continue
    return tasks

if __name__ == "__main__":
    app.run(debug=True)
