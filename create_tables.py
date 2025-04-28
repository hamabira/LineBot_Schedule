from models import Base, engine, Task, ChatLog

print("使ってるDB：", engine.url)
Base.metadata.create_all(engine)
print("テーブル作成できたぜ！")