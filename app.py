from gemini_util import analyze_task
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

import os
print("APIキー:", os.getenv("GEMINI_API_KEY"))


# 自分のチャネルアクセストークン & シークレットをここに貼る
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
    user_message = event.message.text

    try:
        # Geminiでメッセージ解析！
        result = analyze_task(user_message)
        print("Geminiの応答:", result)

        # 文字列 → 辞書型に変換（安全処理）
        import json
        task_data = json.loads(result)

        # 保存（簡単なテキストファイル）
        with open("tasks.txt", "a", encoding="utf-8") as f:
            f.write(json.dumps(task_data, ensure_ascii=False) + "\n")

        # 返信メッセージ作成
        response_text = f"✅ 予定を追加しました！\n📅 {task_data['date']} {task_data['time']}\n📝 {task_data['task']}"

    except Exception as e:
        print("エラー:", e)
        response_text = "予定の解析に失敗しました💦\nフォーマットを確認してみてください！"

    # LINEへ返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_text)
    )

if __name__ == "__main__":
    app.run(port=5000)
