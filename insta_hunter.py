import os
import re
import csv
import io
import sqlite3
import random
import string
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
DB_NAME = "usernames.db"

def init_db():
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS usernames (
                user_id INTEGER,
                username TEXT,
                UNIQUE(user_id, username)
            )
        """)

def save_username(user_id, username):
    with sqlite3.connect(DB_NAME) as db:
        db.execute(
            "INSERT OR IGNORE INTO usernames VALUES (?, ?)",
            (user_id, username)
        )

def get_usernames(user_id):
    with sqlite3.connect(DB_NAME) as db:
        return db.execute(
            "SELECT username FROM usernames WHERE user_id = ?",
            (user_id,)
        ).fetchall()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلًا بك في Insta Hunter!\n\n"
        "/quad - توليد أسماء رباعية\n"
        "/generate - توليد أسماء عشوائية\n"
        "/save الاسم - حفظ اسم\n"
        "/check الاسم - فحص صيغة الاسم\n"
        "/list - عرض الأسماء المحفوظة\n"
        "/export - تصدير الأسماء"
    )

async def quad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chars = string.ascii_lowercase + string.digits
    names = [
        "".join(random.choices(chars, k=4))
        for _ in range(10)
    ]
    await update.message.reply_text(
        "أسماء رباعية مقترحة:\n" + "\n".join(names)
    )

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chars = string.ascii_lowercase + string.digits + "._"
    names = [
        "".join(random.choices(chars, k=random.randint(5, 10)))
        for _ in range(10)
    ]
    await update.message.reply_text(
        "أسماء عشوائية مقترحة:\n" + "\n".join(names)
    )

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدم: /save username")
        return

    username = context.args[0].lower()

    if not re.fullmatch(r"[a-z0-9._]{1,30}", username):
        await update.message.reply_text("صيغة الاسم غير صحيحة.")
        return

    save_username(update.effective_user.id, username)
    await update.message.reply_text("تم حفظ الاسم.")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدم: /check username")
        return

    username = context.args[0].lower()

    if re.fullmatch(r"[a-z0-9._]{1,30}", username):
        await update.message.reply_text(
            "صيغة الاسم صحيحة، لكن لم يتم التحقق من توفره في إنستغرام."
        )
    else:
        await update.message.reply_text("صيغة الاسم غير صحيحة.")

async def list_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    names = get_usernames(update.effective_user.id)

    if not names:
        await update.message.reply_text("ما عندك أسماء محفوظة.")
        return

    await update.message.reply_text(
        "الأسماء المحفوظة:\n" +
        "\n".join(row[0] for row in names)
    )

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    names = get_usernames(update.effective_user.id)

    if not names:
        await update.message.reply_text("ما عندك أسماء لتصديرها.")
        return

    file = io.StringIO()
    writer = csv.writer(file)
    writer.writerow(["username"])
    writer.writerows(names)

    data = io.BytesIO(file.getvalue().encode("utf-8-sig"))
    data.name = "usernames.csv"

    await update.message.reply_document(
        document=data,
        filename="usernames.csv"
    )

def main():
    asyncio.set_event_loop(asyncio.new_event_loop())
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quad", quad))
    app.add_handler(CommandHandler("quadpro", quadpro))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CommandHandler("save", save))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("list", list_names))
    app.add_handler(CommandHandler("export", export))

    render_url = os.environ["RENDER_EXTERNAL_URL"]
    port = int(os.environ.get("PORT", "10000"))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"{render_url}/{TOKEN}"
    )
async def quadpro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chars = string.ascii_lowercase + string.digits

    names = set()

    while len(names) < 1000:
        names.add("".join(random.choices(chars, k=4)))

    for username in names:
        save_username(update.effective_user.id, username)

    await update.message.reply_text(
        f"تم توليد وحفظ {len(names)} اسم رباعي بنجاح!"
    )
if __name__ == "__main__":
    main()
