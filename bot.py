import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

WEB_APP_URL = "https://hussaindadebrahimi90-art.github.io/Earnzood/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 شروع کسب درآمد",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """
🎉 به EarnZood خوش آمدید!

💰 در EarnZood می‌توانید از چند روش پاداش بگیرید:

🎁 پاداش روزانه
📺 مشاهده تبلیغات
📋 انجام تسک‌ها
👥 دعوت دوستان

🚀 برای شروع روی دکمه زیر بزنید.
"""

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("EarnZood Bot is running...")

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
