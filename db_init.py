from sqlalchemy import create_engine, text
import os

# --- app.py と同じく環境変数 DATABASE_URL を使用 ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# アプリと同じ構造のテーブルを作るSQL
schema_sql = """
CREATE TABLE IF NOT EXISTS recipes (
  id          SERIAL PRIMARY KEY,
  title       VARCHAR(200) NOT NULL,
  minutes     INTEGER NOT NULL CHECK (minutes >= 1),
  description TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

# 初回だけ入れるサンプルデータ
seed_sql = """
INSERT INTO recipes (title, minutes, description)
VALUES
  (:t1, :m1, :d1),
  (:t2, :m2, :d2);
"""

with engine.begin() as conn:
    conn.execute(text(schema_sql))

    count = conn.execute(text("SELECT COUNT(*) FROM recipes;")).scalar_one()
    if count == 0:
        conn.execute(
            text(seed_sql),
            dict(
                t1="卵焼き",
                m1=10,
                d1="卵・砂糖・塩を混ぜて焼くシンプルな定番。",
                t2="味噌汁",
                m2=15,
                d2="出汁を取り、味噌を溶き、豆腐とわかめを加える。",
            ),
        )

print("OK: 初期テーブル作成とデータ投入が完了しました。")
