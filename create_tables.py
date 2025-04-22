from models import Base, engine

# これだけでOK！
Base.metadata.create_all(engine)
print("テーブル作成できたぜ！")
