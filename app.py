import json
import os
import traceback
from datetime import datetime, timedelta
from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)

from gemini_util import analyze_task
from db import add_task, get_all_tasks, delete_task_by_details, save_chat_log, update_task, get_all_user_ids
from flex_calendar_util import build_flex_calendar, build_month_calendar

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'Tv2tIB/qKJqSn5jiPnV/h+DBh2c66NDw82UuAbkuZvAdF5YJ7EkGwbpsQpJx7DqgymSd1iNfO49Zsz+m/2+JmcYs068O2Ku6JsOEFzJbhXwnUMg4+jx2otX+9pvSMAgZBRTGaa84PBRMJbwwBCcpWQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '031c826c752cd2ef1c10e86114d361b6'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def make_day_response(task_list, date_obj, label):
    if not task_list:
        return f"📭 {label}（{date_obj.month}月{date_obj.day}日）は何もないみたい！"
    task_list.sort(key=lambda x: x.time)
    res = f"📅 {label}（{date_obj.month}月{date_obj.day}日）の予定：\n"
    for i, t in enumerate(task_list, 1):
        res += f"{i}. {t.time} - {t.task}\n"
    return res

def make_month_response(task_list, year, month):
    if not task_list:
        return f"📭 {year}年{month}月の予定は何もないみたい！"
    task_list.sort(key=lambda x: (x.date, x.time))
    res = f"📅 {year}年{month}月の予定一覧：\n"
    for i, t in enumerate(task_list, 1):
        res += f"{i}. {t.date} {t.time} - {t.task}\n"
    return res

def make_quickreply_for_month(year, month):
    # 前月・今月・次月のQuickReply（年またぎもOK！）
    pre_month = (datetime(year, month, 1) - timedelta(days=1))
    next_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
    this_month = datetime(year, month, 1)
    return QuickReply(
        items=[
            QuickReplyButton(action=MessageAction(label=f"{pre_month.year}年{pre_month.month}月", text=f"{pre_month.year}-{pre_month.month:02d}の予定")),
            QuickReplyButton(action=MessageAction(label=f"{this_month.year}年{this_month.month}月", text=f"{this_month.year}-{this_month.month:02d}の予定")),
            QuickReplyButton(action=MessageAction(label=f"{next_month.year}年{next_month.month}月", text=f"{next_month.year}-{next_month.month:02d}の予定")),
        ]
    )

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
    response_text = ""

    try:
        import re
        if user_message in ["今月の予定", "今月カレンダー", "今月のカレンダー"]:
            now = datetime.now()
            year = now.year
            month = now.month
            month_start = now.replace(day=1).date()
            next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = (next_month - timedelta(days=1)).date()
            all_tasks = get_all_tasks(user_id)
            filtered_tasks = [t for t in all_tasks if month_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= month_end]
            filtered_tasks.sort(key=lambda t: (t.date, t.time))
            if filtered_tasks:
                flex_calendar_dict = build_month_calendar(filtered_tasks, year, month)
                flex_message = FlexSendMessage(
                    alt_text=f"{year}年{month}月の予定カレンダーだよ！",
                    contents=flex_calendar_dict,
                    quick_reply=make_quickreply_for_month(year, month)
                )
                line_bot_api.reply_message(event.reply_token, flex_message)
            else:
                response_text = f"📭 {year}年{month}月の予定は何もないみたい！"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=response_text,
                    quick_reply=make_quickreply_for_month(year, month)
                ))
            save_chat_log(user_id, user_message, response_text)
            return
        if user_message in ["来月の予定", "来月カレンダー", "来月のカレンダー"]:
            now = datetime.now()
            next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
            year = next_month.year
            month = next_month.month
            # ここは「5月の予定」パターンの下のブロックそっくりに書けばOK！
            month_start = datetime(year, month, 1).date()
            n_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
            month_end = (n_month - timedelta(days=1)).date()
            all_tasks = get_all_tasks(user_id)
            filtered_tasks = [t for t in all_tasks if month_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= month_end]
            filtered_tasks.sort(key=lambda t: (t.date, t.time))
            if filtered_tasks:
                flex_calendar_dict = build_month_calendar(filtered_tasks, year, month)
                flex_message = FlexSendMessage(
                    alt_text=f"{year}年{month}月の予定カレンダーだよ！",
                    contents=flex_calendar_dict,
                    quick_reply=make_quickreply_for_month(year, month)
                )
                line_bot_api.reply_message(event.reply_token, flex_message)
            else:
                response_text = f"📭 {year}年{month}月の予定は何もないみたい！"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=response_text,
                    quick_reply=make_quickreply_for_month(year, month)
                ))
            save_chat_log(user_id, user_message, response_text)
            return

        if user_message in ["再来月の予定", "再来月カレンダー", "再来月のカレンダー"]:
            now = datetime.now()
            next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
            after_next_month = (next_month.replace(day=28) + timedelta(days=4)).replace(day=1)
            year = after_next_month.year
            month = after_next_month.month
            month_start = datetime(year, month, 1).date()
            n_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
            month_end = (n_month - timedelta(days=1)).date()
            all_tasks = get_all_tasks(user_id)
            filtered_tasks = [t for t in all_tasks if month_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= month_end]
            filtered_tasks.sort(key=lambda t: (t.date, t.time))
            if filtered_tasks:
                flex_calendar_dict = build_month_calendar(filtered_tasks, year, month)
                flex_message = FlexSendMessage(
                    alt_text=f"{year}年{month}月の予定カレンダーだよ！",
                    contents=flex_calendar_dict,
                    quick_reply=make_quickreply_for_month(year, month)
                )
                line_bot_api.reply_message(event.reply_token, flex_message)
            else:
                response_text = f"📭 {year}年{month}月の予定は何もないみたい！"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=response_text,
                    quick_reply=make_quickreply_for_month(year, month)
                ))
            save_chat_log(user_id, user_message, response_text)
            return

        # --- 「2026年5月の予定」「2025年12月のカレンダー」対応 ---
        m_jp_yyyy = re.match(r"^(\d{4})年(\d{1,2})月(の予定|のカレンダー|カレンダー|予定)?$", user_message)
        if m_jp_yyyy:
            year = int(m_jp_yyyy.group(1))
            month = int(m_jp_yyyy.group(2))
            month_start = datetime(year, month, 1).date()
            next_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
            month_end = (next_month - timedelta(days=1)).date()
            all_tasks = get_all_tasks(user_id)
            filtered_tasks = [t for t in all_tasks if month_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= month_end]
            filtered_tasks.sort(key=lambda t: (t.date, t.time))
            if filtered_tasks:
                flex_calendar_dict = build_month_calendar(filtered_tasks, year, month)
                flex_message = FlexSendMessage(
                    alt_text=f"{year}年{month}月の予定カレンダーだよ！",
                    contents=flex_calendar_dict,
                    quick_reply=make_quickreply_for_month(year, month)
                )
                line_bot_api.reply_message(event.reply_token, flex_message)
            else:
                response_text = f"📭 {year}年{month}月の予定は何もないみたい！"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=response_text,
                    quick_reply=make_quickreply_for_month(year, month)
                ))
            save_chat_log(user_id, user_message, response_text)
            return

        # --- 「5月の予定」「5月カレンダー」などの月指定パターン ---
        m_jp = re.match(r"^(\d{1,2})月(の予定|のカレンダー|カレンダー|予定)?$", user_message)
        if m_jp:
            now = datetime.now()
            month = int(m_jp.group(1))
            # 入力された月が今月より前→来年、それ以外は今年
            year = now.year if month >= now.month else now.year + 1
            month_start = datetime(year, month, 1).date()
            next_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
            month_end = (next_month - timedelta(days=1)).date()
            all_tasks = get_all_tasks(user_id)
            filtered_tasks = [t for t in all_tasks if month_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= month_end]
            filtered_tasks.sort(key=lambda t: (t.date, t.time))
            if filtered_tasks:
                flex_calendar_dict = build_month_calendar(filtered_tasks, year, month)
                flex_message = FlexSendMessage(
                    alt_text=f"{year}年{month}月の予定カレンダーだよ！",
                    contents=flex_calendar_dict,
                    quick_reply=make_quickreply_for_month(year, month)
                )
                line_bot_api.reply_message(event.reply_token, flex_message)
            else:
                response_text = f"📭 {year}年{month}月の予定は何もないみたい！"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=response_text,
                    quick_reply=make_quickreply_for_month(year, month)
                ))
            save_chat_log(user_id, user_message, response_text)
            return

        # --- 「2025-05の予定」パターン ---
        m = re.match(r"(\d{4})-(\d{1,2})の予定", user_message)
        if m:
            year = int(m.group(1))
            month = int(m.group(2))
            month_start = datetime(year, month, 1).date()
            next_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
            month_end = (next_month - timedelta(days=1)).date()
            all_tasks = get_all_tasks(user_id)
            filtered_tasks = [t for t in all_tasks if month_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= month_end]
            filtered_tasks.sort(key=lambda t: (t.date, t.time))
            if filtered_tasks:
                flex_calendar_dict = build_month_calendar(filtered_tasks, year, month)
                flex_message = FlexSendMessage(
                    alt_text=f"{year}年{month}月の予定カレンダーだよ！",
                    contents=flex_calendar_dict,
                    quick_reply=make_quickreply_for_month(year, month)
                )
                line_bot_api.reply_message(event.reply_token, flex_message)
            else:
                response_text = f"📭 {year}年{month}月の予定は何もないみたい！"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=response_text,
                    quick_reply=make_quickreply_for_month(year, month)
                ))
            save_chat_log(user_id, user_message, response_text)
            return

        # ------（以下は今まで通り）------
        result = analyze_task(user_id, user_message)
        print("Geminiの応答:", result)

        if result.strip().startswith('{'):
            task_data = json.loads(result)
        else:
            response_text = result.strip()
            if not response_text:
                response_text = "うーん、ちょっとよく分からなかった！もう一回聞いてくれる？"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text)
            )
            save_chat_log(user_id, user_message, response_text)
            return

        action = task_data.get("action")
        all_tasks = get_all_tasks(user_id)
        now = datetime.now()
        filtered_tasks = []
        period = task_data.get("period")
        date = task_data.get("date")

        if action == "show":
            if period == "today":
                target_date = now.date()
                filtered_tasks = [t for t in all_tasks if t.date == target_date.strftime("%Y-%m-%d")]
                response_text = make_day_response(filtered_tasks, target_date, "今日")
            elif period == "tomorrow":
                target_date = (now + timedelta(days=1)).date()
                filtered_tasks = [t for t in all_tasks if t.date == target_date.strftime("%Y-%m-%d")]
                response_text = make_day_response(filtered_tasks, target_date, "明日")
            elif period == "day_after_tomorrow":
                target_date = (now + timedelta(days=2)).date()
                filtered_tasks = [t for t in all_tasks if t.date == target_date.strftime("%Y-%m-%d")]
                response_text = make_day_response(filtered_tasks, target_date, "明後日")
            elif period == "n_days_later":
                n = int(task_data.get("days", 0))
                target_date = (now + timedelta(days=n)).date()
                filtered_tasks = [t for t in all_tasks if t.date == target_date.strftime("%Y-%m-%d")]
                response_text = make_day_response(filtered_tasks, target_date, f"{n}日後")
            elif date:
                if re.match(r"^\d{4}-\d{2}$", date):
                    year, month = map(int, date.split("-"))
                    month_start = datetime(year, month, 1).date()
                    next_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
                    month_end = (next_month - timedelta(days=1)).date()
                    filtered_tasks = [t for t in all_tasks if month_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= month_end]
                    filtered_tasks.sort(key=lambda t: (t.date, t.time))
                    flex_calendar_dict = build_month_calendar(filtered_tasks, year, month)
                    flex_message = FlexSendMessage(
                        alt_text=f"{year}年{month}月の予定カレンダーだよ！",
                        contents=flex_calendar_dict,
                        quick_reply=make_quickreply_for_month(year, month)
                    )
                    line_bot_api.reply_message(event.reply_token, flex_message)
                    save_chat_log(user_id, user_message, f"{year}年{month}月のカレンダーFlexを送信")
                    return
                else:
                    target_date = datetime.strptime(date, "%Y-%m-%d").date()
                    filtered_tasks = [t for t in all_tasks if t.date == target_date.strftime("%Y-%m-%d")]
                    response_text = make_day_response(filtered_tasks, target_date, f"{target_date.month}月{target_date.day}日")

            elif period == "week":
                today = now.date()
                this_monday = today - timedelta(days=today.weekday())
                week_start = this_monday
                week_end = week_start + timedelta(days=6)
                filtered_tasks = [t for t in all_tasks if week_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= week_end]
                filtered_tasks.sort(key=lambda t: (t.date, t.time))
                if not filtered_tasks:
                    response_text = "📭 今週の予定は何もないみたい！"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))
                else:
                    flex_calendar_dict = build_flex_calendar(filtered_tasks, start_date=week_start)
                    flex_message = FlexSendMessage(
                        alt_text="今週の予定カレンダーだよ！",
                        contents=flex_calendar_dict
                    )
                    line_bot_api.reply_message(event.reply_token, flex_message)
                save_chat_log(user_id, user_message, response_text)
                return
            elif period == "next_week":
                today = now.date()
                this_monday = today - timedelta(days=today.weekday())
                next_monday = this_monday + timedelta(days=7)
                next_sunday = next_monday + timedelta(days=6)
                filtered_tasks = [t for t in all_tasks if next_monday <= datetime.strptime(t.date, "%Y-%m-%d").date() <= next_sunday]
                filtered_tasks.sort(key=lambda t: (t.date, t.time))
                if not filtered_tasks:
                    response_text = "📭 来週の予定は何もないみたい！"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))
                else:
                    flex_calendar_dict = build_flex_calendar(filtered_tasks, start_date=next_monday)
                    flex_message = FlexSendMessage(
                        alt_text="来週の予定カレンダーだよ！",
                        contents=flex_calendar_dict
                    )
                    line_bot_api.reply_message(event.reply_token, flex_message)
                save_chat_log(user_id, user_message, response_text)
                return

            elif period == "week_after_next":
                today = now.date()
                this_monday = today - timedelta(days=today.weekday())
                week_after_next_monday = this_monday + timedelta(days=14)
                week_after_next_sunday = week_after_next_monday + timedelta(days=6)
                filtered_tasks = [t for t in all_tasks if week_after_next_monday <= datetime.strptime(t.date, "%Y-%m-%d").date() <= week_after_next_sunday]
                filtered_tasks.sort(key=lambda t: (t.date, t.time))
                if not filtered_tasks:
                    response_text = "📭 再来週の予定は何もないみたい！"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))
                else:
                    flex_calendar_dict = build_flex_calendar(filtered_tasks, start_date=week_after_next_monday)
                    flex_message = FlexSendMessage(
                        alt_text="再来週の予定カレンダーだよ！",
                        contents=flex_calendar_dict
                    )
                    line_bot_api.reply_message(event.reply_token, flex_message)
                save_chat_log(user_id, user_message, response_text)
                return

            elif period == "month":
                year = now.year
                month = now.month
                month_start = now.replace(day=1).date()
                next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
                month_end = (next_month - timedelta(days=1)).date()
                filtered_tasks = [t for t in all_tasks if month_start <= datetime.strptime(t.date, "%Y-%m-%d").date() <= month_end]
                filtered_tasks.sort(key=lambda t: (t.date, t.time))
                flex_calendar_dict = build_month_calendar(filtered_tasks, year, month)
                flex_message = FlexSendMessage(
                    alt_text=f"{year}年{month}月の予定カレンダーだよ！",
                    contents=flex_calendar_dict,
                    quick_reply=make_quickreply_for_month(year, month)
                )
                line_bot_api.reply_message(event.reply_token, flex_message)
                save_chat_log(user_id, user_message, f"{year}年{month}月のカレンダーFlexを送信")
                return

            elif period == "all" or not period:
                filtered_tasks = list(all_tasks)
                if not filtered_tasks:
                    response_text = "📭 表示できる予定が見つかりませんでした！"
                else:
                    filtered_tasks.sort(key=lambda x: (x.date, x.time))
                    response_text = "📅 予定一覧：\n"
                    for i, task in enumerate(filtered_tasks, 1):
                        response_text += f"{i}. {task.date} {task.time} - {task.task}\n"

            if not response_text:
                response_text = "うーん、表示できる予定がなかったよ！"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))
            save_chat_log(user_id, user_message, response_text)
            return

        # 以下（追加・削除・更新・チャット）は従来通り

        elif action == "chat":
            response_text = task_data.get("response", "😊 どうしましたか？")

        elif action == "delete":
            date = task_data.get("date")
            task_text = task_data.get("task")
            if date and task_text:
                success = delete_task_by_details(user_id, date, task_text)
                if success:
                    response_text = f"🗑️ 次の予定を削除したよ：\n📅 {date}\n📝 {task_text}"
                else:
                    response_text = "❌ 指定された予定が見つからなかった！"
            else:
                response_text = "❌ 削除条件が足りてないぞ！"

        elif action == "add":
            date = task_data.get("date")
            time = task_data.get("time")
            task_text = task_data.get("task")
            if date and time and task_text:
                add_task(user_id, date, time, task_text)
                response_text = f"✅ 予定を追加したぞ！\n📅 {date} {time}\n📝 {task_text}"
            else:
                response_text = "❌ 予定の追加に必要な情報が足りてないぞ！"

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
                    response_text = f"✅ 予定を変更したぞ！\n📅 {old_date} {old_time}「{old_task}」→ {new_date} {new_time}「{new_task}」"
                else:
                    response_text = "❌ 変更対象の予定が見つからなかった！"
            else:
                response_text = "❌ 変更に必要な情報が足りてないぞ！"

        else:
            response_text = "🤖 ごめん、内容がうまく理解できなかった💦"

        if not response_text:
            response_text = "うーん、何かうまくいかなかったみたい！"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )
        save_chat_log(user_id, user_message, response_text)

    except Exception as e:
        print("エラー:", e)
        traceback.print_exc()
        response_text = "予定の処理中にエラーが出た！💦"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

def push_today_schedule():
    today = datetime.now().date()
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        all_tasks = get_all_tasks(user_id)
        tasks_today = [t for t in all_tasks if t.date == today.strftime("%Y-%m-%d")]
        message = make_day_response(tasks_today, today, "今日")
        try:
            line_bot_api.push_message(user_id, TextSendMessage(text=message))
            print(f"{user_id} に今日の予定を送ったぜ！")
        except Exception as e:
            print(f"{user_id} へのpushでエラー: {e}")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(push_today_schedule, 'cron', hour=7, minute=0)
    scheduler.start()
    print("全ユーザーに毎朝7時の自動通知が稼働したぜ！")
    app.run(debug=True)