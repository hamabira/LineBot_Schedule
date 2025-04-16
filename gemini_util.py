import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

# .env から APIキーを読み込み
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Geminiの初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def analyze_task(message_text):
    prompt = f"""
    以下の日本語の予定文から、日付（YYYY-MM-DD）、時間（HH:MM）、内容（task）を抽出してください。
    必ず次のようなJSON形式で出力してください：

    {{
      "date": "2025-04-17",
      "time": "09:00",
      "task": "レポートを書く"
    }}

    入力: {message_text}
    出力:
    """

    try:
        print("🎯 送信プロンプト:", prompt)
        response = model.generate_content(prompt)
        print("✅ Geminiの応答:", response.text)

        # JSONだけを抜き出す（{〜}の中身）
        match = re.search(r'\{[\s\S]*?\}', response.text)
        if match:
            return match.group(0)
        else:
            raise ValueError("JSON形式が見つかりませんでした")

    except Exception as e:
        print("❌ Gemini API呼び出しでエラー:", e)
        return '{"date": "不明", "time": "不明", "task": "不明"}'

# 単体テスト用
if __name__ == "__main__":
    test_message = "明日の朝9時にレポートを書く"
    result = analyze_task(test_message)
    print("Geminiの応答:\n", result)
