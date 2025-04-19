import os
import google.generativeai as genai
from dotenv import load_dotenv

# === APIキー読み込みとGemini初期化 ===
try:
    load_dotenv()  # .envファイルから環境変数を読み込む
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY が見つかりません。.env ファイルを確認してください。")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")  # モデルの指定

except Exception as e:
    print("🔴 Geminiの初期化エラー:", e)
    model = None  # エラーがあった場合はNoneを入れて後で使えないようにする

# === AIによる予定解析関数 ===
def analyze_task(message_text):
    from datetime import datetime

    if model is None:
        return '{"action": "error", "response": "Geminiが初期化されていません。"}'

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    prompt = f"""
あなたは優しく親しみやすい予定管理AIアシスタントです。
ユーザーの自然な発話から、必要があれば「予定管理」に関するアクションを抽出し、それ以外は雑談として受け取ってください。

# 現在の日付と時刻
今日の日付は {current_date} で、現在の時刻は {current_time} です。

アクションがある場合は、以下のJSON形式で返してください：
{{
  "action": "add" or "delete" or "show",
  "date": "YYYY-MM-DD",    # 任意
  "time": "HH:MM",         # 任意
  "task": "予定の内容",     # 任意
  "index": 予定の番号       # 任意（削除時）
  "period": "today" または "week" または "all"（表示のときのみ）
}}

アクションが含まれない雑談メッセージの場合は、以下のJSON形式で返してください：
{{
  "action": "chat",
  "response": "ユーザーへの優しい返事"
}}

例：
- 「今日の予定を教えて」 → {{"action": "show", "period": "today"}}
- 「今週の予定は？」 → {{"action": "show", "period": "week"}}
- 「予定を全部見せて」 → {{"action": "show", "period": "all"}}


# ユーザーの入力：
{message_text}

# 出力：
"""

    try:
        response = model.generate_content(prompt)
        print("🔵 Geminiの生返答:\n", response.text)  # ← ここ追加！
        result_text = response.text.strip().replace("```json", "").replace("```", "").strip()

        # JSONっぽい部分だけ取り出す（```json が含まれていた場合）
        if "```" in result_text:
            result_text = result_text.split("```")[-2]  # ```json の中身だけ抜き出す
        result_text = result_text.strip()

        return result_text
    except Exception as e:
        print("❌ Geminiエラー:", e)
        return '{"action": "unknown"}'

# === テスト実行（開発中のチェック用） ===
if __name__ == "__main__":
    test_message = "明日の午前中に会議"
    result = analyze_task(test_message)
    print("Geminiの応答:\n", result)
