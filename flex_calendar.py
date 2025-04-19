from linebot.models import FlexSendMessage


flex_calendar_dict = {
    "type": "bubble",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [{
            "type": "text",
            "text": "今週のカレンダー",
            "weight": "bold",
            "size": "lg",
            "color": "#ffffff"
        }],
        "backgroundColor": "#0066CC"
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": "月", "align": "center", "size": "sm"},
                    {"type": "text", "text": "火", "align": "center", "size": "sm"},
                    {"type": "text", "text": "水", "align": "center", "size": "sm"},
                    {"type": "text", "text": "木", "align": "center", "size": "sm"},
                    {"type": "text", "text": "金", "align": "center", "size": "sm"},
                    {"type": "text", "text": "土", "align": "center", "color": "#0066CC", "size": "sm"},
                    {"type": "text", "text": "日", "align": "center", "color": "#CC0000", "size": "sm"}
                ]
            },
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": "20:00\n会議", "align": "center", "size": "xs"},
                    {"type": "text", "text": "なし", "align": "center", "size": "xs"},
                    {"type": "text", "text": "13:00\n勉強会", "align": "center", "size": "xs"},
                    {"type": "text", "text": "なし", "align": "center", "size": "xs"},
                    {"type": "text", "text": "19:00\n飲み会", "align": "center", "size": "xs"},
                    {"type": "text", "text": "なし", "align": "center", "size": "xs"},
                    {"type": "text", "text": "なし", "align": "center", "size": "xs"}
                ]
            }
        ]
    },
    "footer": {
        "type": "box",
        "layout": "vertical",
        "contents": [{
            "type": "text",
            "text": "予定をタップで詳細も見れるように拡張できるぞ！",
            "size": "xs",
            "color": "#888888"
        }]
    }
}