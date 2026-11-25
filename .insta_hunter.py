
import os
import sqlite3
import random
import string
import csv
import io
import re

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN = os.environ["BOT_TOKEN"]

db = sqlite3.connect("insta_hunter.db")
db.execute("""
CREATE TABLE IF NOT EXISTS usernames (
    username TEXT PRIMARY KEY,
    category TEXT,
    status TEXT DEFAULT 'Unverified'
)
""")
db.commit()


def save(username, category):
    db.execute(
        "INSERT OR IGNORE INTO usernames "
        "(username, category) VALUES (?, ?)",
        (username, category)
    )
    db.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 INSTA HUNTER\n\n"
        "/quad - توليد يوزرات رباعية\n"
        "/generate - توليد يوزرات\n"
        "/save USER - حفظ يوزر\n"
        "/check USER - تسجيل يوزر للفحص\n"
        "/list - عرض المحفوظات\n"
        "/export - تصدير CSV"
    )


async def quad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chars = string.ascii_lowercase + string.digits
    results = set()

    while len(results) < 20:
        results.add("".join(random.choices(chars, k=4)))

    for username in results:
        save(username, "Quad")

    await update.message.reply_text(
        "🎯 اليوزرات الرباعية:\n\n" +
        "\n".join("@" + u for u in sorted(results))
    )


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chars = string.ascii_lowercase + string.digits
    results = set()

    while len(results) < 15:
        length = random.choice([4, 5, 6])
        results.add(
            "".join(random.choices(chars, k=length))
        )

    for username in results:
        save(username, "Generated")

    await update.message.reply_text(
        "🎲 النتائج:\n\n" +
        "\n".join("@" + u for u in sorted(results))
    )


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدم /save username")
        return

    username = context.args[0].lower().lstrip("@")

    if not re.fullmatch(r"[a-z0-9._]{1,30}", username):
        await update.message.reply_text("❌ صيغة غير صحيحة")
        return

    save(username, "Manual")
    await update.message.reply_text(f"✅ تم حفظ @{username}")


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدم /check username")
        return

    username = context.args[0].lower().lstrip("@")

    if not re.fullmatch(r"[a-z0-9._]{1,30}", username):
        await update.message.reply_text("❌ صيغة غير صحيحة")
        return

    save(username, "Check request")

    await update.message.reply_text(
        f"🔎 @{username}\n"
        "الحالة: غير متحقق منها.\n"
        "لا يعني ذلك أن الحساب متاح."
    )


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.execute(
        "SELECT username, category FROM usernames LIMIT 50"
    ).fetchall()

    if not rows:
        await update.message.reply_text("القائمة فارغة")
        return

    message = "📋 المحفوظات:\n\n"
    for username, category in rows:
        message += f"@{username} — {category}\n"

    await update.message.reply_text(message)


async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.execute(
        "SELECT username, category FROM usernames"
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Username", "Category"])
    writer.writerows(rows)

    file = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    file.name = "insta_hunter.csv"

    await update.message.reply_document(
        document=file,
        caption="📁 Insta Hunter"
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quad", quad))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CommandHandler("save", save_command))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("list", list_users))
    app.add_handler(CommandHandler("export", export))

    app.run_polling()


if __name__ == "__main__":
    main()
