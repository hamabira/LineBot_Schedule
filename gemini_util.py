import os
import google.generativeai as genai
from dotenv import load_dotenv
from db import get_recent_chat_logs  # ここでdb.pyの関数をインポート

# === APIキー読み込みとGemini初期化 ===
try:
    load_dotenv()  # .envファイルから環境変数を読み込む
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY が見つかりません。.env ファイルを確認してくれ！")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")  # モデルの指定

except Exception as e:
    print("🔴 Geminiの初期化エラー:", e)
    model = None  # エラーがあった場合はNoneを入れて後で使えないようにする

# === AIによる予定解析関数 ===
def analyze_task(user_id, message_text):
    from datetime import datetime

    if model is None:
        return '{"action": "error", "response": "Geminiが初期化されてないぞ！"}'

    # 直近の会話履歴を取得してログ出力
    logs = get_recent_chat_logs(user_id)
    print("📝 直近の会話ログ:", logs)

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    chat_history = "\n".join([f"ユーザー: {log['message']}\nAI: {log['response']}" for log in logs])

    prompt = f"""
あなたは明るくて励ましてくれる予定管理AIアシスタント！
ユーザーの自然な発話から、必要があれば「予定管理」に関するアクションを抽出してね。
それ以外は友達感覚で雑談してノリよく返して！

ユーザーが「来週の予定」と言ったら、
必ず period: "next_week" で返すこと！
「今週の予定」は period: "week"、
「再来週の予定」は period: "week_after_next"、
と必ず区別してくれ！

★重要★
- 予定追加などで「時間が指定されていない場合」は、"time"キー自体をJSONに含めず出力して！
  例：「今日課題する」→ {{"action": "add", "date": "2025-04-28", "task": "課題する"}}
- 逆に「時間指定あり」のときだけ "time": "HH:MM" を含めること！

# 現在の日付と時刻
今日の日付は {current_date} で、現在の時刻は {current_time} だよ！

# 会話履歴：
{chat_history}  # 直近のやり取りをここに追加

アクションがある場合は、以下のJSON形式で返して！
{{
  "action": "add" or "delete" or "show" or "update",
  "date": "YYYY-MM-DD",    # 任意
  "time": "HH:MM",         # 時間指定があるときのみ含める
  "task": "予定の内容",     # 任意
  "index": 予定の番号       # 任意（削除時）
  "period": "today" または "week" または "all"（表示のときのみ）
}}

**アクションが含まれない雑談のときは、以下のJSON形式で返して！**
{{
  "action": "chat",
  "response": "明るい雑談返事（例：『おっけー！今日も一緒にがんばろー！』とか）"
}}

例：
- 「明後日の夜ゲーム」 → {{"action": "add", "time": "19:00", "task": "ゲーム"}}
- 「今日の予定を教えて」 → {{"action": "show", "period": "today"}}
- 「今週の予定は？」 → {{"action": "show", "period": "week"}}
- 「予定を全部見せて」 → {{"action": "show", "period": "all"}}
- 「やる気出ない…」 → {{"action": "chat", "response": "無理しないで！たまには休憩も大事！」}}
- 「こんにちは！」 → {{"action": "chat", "response": "やっほー！今日もよろしくね！」}}
- 「明日の会議を午後8時からに変更」→ {{"action": "update", "old_date": "2025-04-20", "old_time": "21:00", "old_task": "会議", "new_date": "2025-04-20", "new_time": "20:00", "new_task": "会議"}}
- 「今日課題する」→ {{"action": "add", "date": "{current_date}", "task": "課題する"}}

# ユーザーの入力：
{message_text}

# 出力：
"""

    try:
        response = model.generate_content(prompt)
        print("🔵 Geminiの生返答:\n", response.text)
        result_text = response.text.strip().replace("```json", "").replace("```", "").strip()

        # JSONっぽい部分だけ取り出す（```json が含まれていた場合）
        if "```" in result_text:
            result_text = result_text.split("```")[-2]
        result_text = result_text.strip()

        return result_text
    except Exception as e:
        print("❌ Geminiエラー:", e)
        return '{"action": "unknown"}'

# === テスト実行（開発中のチェック用） ===
if __name__ == "__main__":
    user_id = 123
    test_message = "今日課題する"
    result = analyze_task(user_id, test_message)
    print("Geminiの応答:\n", result)