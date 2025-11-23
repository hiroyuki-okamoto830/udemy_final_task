from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, List

from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template
from sqlalchemy import (
    create_engine, String, Integer, Text, DateTime, CheckConstraint, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

load_dotenv()

def get_database_url() -> Optional[str]:
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url

DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None

class Base(DeclarativeBase):
    pass

class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint("minutes >= 1", name="ck_recipes_minutes_ge_1"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

if engine is not None:
    Base.metadata.create_all(engine)

app = Flask(__name__)

def _to_bool_env(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@app.route("/", methods=["GET", "POST"])
def index():
    errors: List[str] = []
    form_values = {"title": "", "minutes": "", "description": ""}

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        minutes_raw = (request.form.get("minutes") or "").strip()
        description = (request.form.get("description") or "").strip()

        form_values["title"] = title
        form_values["minutes"] = minutes_raw
        form_values["description"] = description

        minutes_val: Optional[int] = None
        try:
            minutes_val = int(minutes_raw)
        except:
            errors.append("所要分数は整数で入力してください。")

        if minutes_val is not None and minutes_val < 1:
            errors.append("所要分数は1以上の整数で入力してください。")

        if not title:
            errors.append("タイトルは必須です。")

        if engine is None:
            errors.append("データベースが未設定のため保存できません。")

        if not errors:
            with Session(engine) as session:
                item = Recipe(title=title, minutes=minutes_val, description=description)
                session.add(item)
                session.commit()
            return redirect(url_for("index"))

    recipes: List[Recipe] = []
    if engine is not None:
        with Session(engine) as session:
            recipes = session.query(Recipe).order_by(
                Recipe.created_at.desc(), Recipe.id.desc()
            ).all()

    return render_template(
        "index.html",
        errors=errors,
        recipes=recipes,
        debug="false",
        port=8000,
        db_ready=(engine is not None),
        form_values=form_values,
    )


# ▼ 編集処理
@app.route("/update/<int:recipe_id>", methods=["POST"])
def update_recipe(recipe_id: int):
    if engine is None:
        return redirect(url_for("index"))

    title = (request.form.get("title") or "").strip()
    minutes_raw = (request.form.get("minutes") or "").strip()
    description = (request.form.get("description") or "").strip()

    try:
        minutes_val = int(minutes_raw)
    except:
        return redirect(url_for("index"))

    if minutes_val < 1:
        return redirect(url_for("index"))

    with Session(engine) as session:
        item = session.get(Recipe, recipe_id)
        if item:
            item.title = title
            item.minutes = minutes_val
            item.description = description
            session.commit()

    return redirect(url_for("index"))


# ▼ 削除処理
@app.route("/delete/<int:recipe_id>", methods=["POST"])
def delete_recipe(recipe_id: int):
    if engine is None:
        return redirect(url_for("index"))

    with Session(engine) as session:
        item = session.get(Recipe, recipe_id)
        if item:
            session.delete(item)
            session.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
