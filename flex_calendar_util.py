from datetime import datetime, timedelta

def build_flex_calendar(tasks, start_date=None):
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday()) if start_date is None else start_date
    days = [monday + timedelta(days=i) for i in range(7)]
    labels = ["月","火","水","木","金","土","日"]

    header = {
        "type":"box","layout":"vertical",
        "backgroundColor":"#378bdd","cornerRadius":"md",
        "paddingAll":"sm","paddingBottom":"xs",
        "contents":[
            {"type":"text","text":
             f"【{days[0].month}/{days[0].day}({labels[0]})～"
             f"{days[6].month}/{days[6].day}({labels[6]})】週間カレンダー",
             "size":"md","weight":"bold","align":"center",
             "wrap":True,"color":"#ffffff"}
        ]
    }

    weekday_row = {
        "type":"box","layout":"horizontal","margin":"xs",
        "contents":[
            {"type":"box","layout":"vertical",
             "borderColor":"#cccccc","borderWidth":"1px",
             "contents":[
                 {"type":"text","text":lbl,"size":"sm","align":"center",
                  "color":"#CC0000" if i==6 else "#0066CC" if i==5 else "#222222"}
             ]}
            for i,lbl in enumerate(labels)
        ]
    }

    date_row = {
        "type":"box","layout":"horizontal","margin":"none",
        "contents":[
            {"type":"box","layout":"vertical",
             "borderColor":"#cccccc","borderWidth":"1px",
             "contents":[
                 {"type":"text","text":f"{d.day}","size":"sm","align":"center",
                  "color":"#CC0000" if i==6 else "#0066CC" if i==5 else "#222222"}
             ]}
            for i,d in enumerate(days)
        ]
    }

    rows = []
    MAX = 3
    for idx in range(MAX):
        row = {"type":"box","layout":"horizontal","margin":"none","contents":[]}
        for i, d in enumerate(days):
            day_tasks = [t for t in tasks if t.date == d.strftime("%Y-%m-%d")]
            day_tasks.sort(key=lambda t: t.time or "99:99")
            if idx < len(day_tasks):
                time_label = day_tasks[idx].time if day_tasks[idx].time else "未定"
                txt = f"{time_label} {day_tasks[idx].task}"
            else:
                txt = " "
            row["contents"].append({
                "type": "box",
                "layout": "vertical",
                "borderColor": "#cccccc",
                "borderWidth": "1px",
                "contents": [
                    {
                        "type": "text",
                        "text": txt,
                        "size": "sm",
                        "align": "center",
                        "wrap": True,
                        "color": "#333333"
                    }
                ]
            })
        rows.append(row)


    plus = {"type":"box","layout":"horizontal","margin":"none","contents":[]}
    for d in days:
        day_tasks = [t for t in tasks if t.date == d.strftime("%Y-%m-%d")]
        rem = len(day_tasks) - MAX
        txt = f"+{rem}件" if rem > 0 else " "
        plus["contents"].append({
            "type": "box",
            "layout": "vertical",
            "borderColor": "#cccccc",
            "borderWidth": "1px",
            "contents": [
                {
                    "type": "text",
                    "text": txt,
                    "size": "sm",
                    "align": "center",
                    "color": "#888888",
                    "wrap": True
                }
            ]
        })
    rows.append({"type":"separator","margin":"none"})
    rows.append(plus)

    flex_calendar = {
        "type":"bubble",
        "body":{
            "type":"box","layout":"vertical",
            "spacing":"none",
            "paddingAll":"none","paddingTop":"none","paddingBottom":"none",
            "contents":[
                header,
                weekday_row,
                date_row,
                {"type":"separator","margin":"none"},
                *rows
            ]
        }
    }
    return flex_calendar

def build_month_calendar(tasks, year, month):
    from calendar import monthrange
    first_weekday, last_day = monthrange(year, month)
    days = []
    for d in range(1, last_day+1):
        days.append(datetime(year, month, d).date())
    labels = ["月","火","水","木","金","土","日"]

    calendar_rows = []
    week = []
    for i, day in enumerate(days):
        week.append(day)
        if (day.weekday() == 6) or (day == days[-1]):
            calendar_rows.append(week)
            week = []
    if calendar_rows and len(calendar_rows[0]) < 7:
        for _ in range(7-len(calendar_rows[0])):
            calendar_rows[0].insert(0, None)

    header = {
        "type":"box","layout":"vertical",
        "backgroundColor":"#378bdd","cornerRadius":"md",
        "paddingAll":"sm","paddingBottom":"xs",
        "contents":[
            {"type":"text","text":
             f"{year}年{month}月カレンダー",
             "size":"md","weight":"bold","align":"center",
             "wrap":True,"color":"#ffffff"}
        ]
    }
    weekday_row = {
        "type":"box","layout":"horizontal","margin":"xs",
        "contents":[
            {"type":"box","layout":"vertical",
             "borderColor":"#cccccc","borderWidth":"1px",
             "contents":[
                 {"type":"text","text":lbl,"size":"sm","align":"center",
                  "color":"#CC0000" if i==6 else "#0066CC" if i==5 else "#222222"}
             ]}
            for i,lbl in enumerate(labels)
        ]
    }
    date_rows = []
    for week in calendar_rows:
        row = {"type":"box","layout":"horizontal","margin":"none","contents":[]}
        for i, d in enumerate(week):
            if d is None:
                row["contents"].append({
                    "type":"box","layout":"vertical",
                    "borderColor":"#cccccc","borderWidth":"1px",
                    "contents":[{"type":"text","text":" ","size":"sm","align":"center"}]
                })
            else:
                day_tasks = [t for t in tasks if t.date==d.strftime("%Y-%m-%d")]
                day_tasks.sort(key=lambda t: t.time or "99:99")
                summary = f"{len(day_tasks)}件の用事" if len(day_tasks)>0 else " "
                row["contents"].append({
                    "type":"box","layout":"vertical",
                    "borderColor":"#cccccc","borderWidth":"1px",
                    "contents":[
                        {"type":"text","text":str(d.day),"size":"sm","align":"center"},
                        {"type":"text","text":summary,"size":"xs","align":"center","color":"#888888"}
                    ]
                })
        date_rows.append(row)

    flex_calendar = {
        "type":"bubble",
        "body":{
            "type":"box","layout":"vertical",
            "spacing":"none",
            "paddingAll":"none","paddingTop":"none","paddingBottom":"none",
            "contents":[
                header,
                weekday_row,
                *date_rows
            ]
        }
    }
    return flex_calendar