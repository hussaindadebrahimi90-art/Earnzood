import os
import json
import base64
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "hussaindadebrahimi90-art/Earnzood"
FILE_PATH = "users.json"
BRANCH = "main"

WEB_APP_URL = "https://hussaindadebrahimi90-art.github.io/Earnzood/"


def github_get():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}?ref={BRANCH}"

    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
        timeout=15
    )

    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]

    if r.status_code == 404:
        return {}, None

    raise Exception(f"GitHub GET error: {r.status_code} {r.text}")


def github_save(users, sha):
    content = json.dumps(
        users,
        ensure_ascii=False,
        indent=2
    )

    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

    body = {
        "message": "Update referral users",
        "content": encoded,
        "branch": BRANCH
    }

    if sha:
        body["sha"] = sha

    r = requests.put(
        url,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        },
        json=body,
        timeout=15
    )

    if r.status_code not in (200, 201):
        raise Exception(
            f"GitHub SAVE error: {r.status_code} {r.text}"
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    user_id = str(user.id)

    args = context.args

    referrer_id = None

    if args:
        if args[0].isdigit():
            referrer_id = args[0]

    try:

        users, sha = github_get()

        if user_id not in users:

            users[user_id] = {
                "id": user.id,
                "username": user.username or "",
                "first_name": user.first_name or "",
                "balance": 0,
                "referrals": 0,
                "referrer": None
            }

            if (
                referrer_id
                and referrer_id != user_id
                and referrer_id in users
            ):

                users[user_id]["referrer"] = referrer_id

                users[referrer_id]["referrals"] = (
                    users[referrer_id].get("referrals", 0) + 1
                )

            github_save(users, sha)

        else:

            changed = False

            if (
                referrer_id
                and referrer_id != user_id
                and not users[user_id].get("referrer")
                and referrer_id in users
            ):

                users[user_id]["referrer"] = referrer_id

                users[referrer_id]["referrals"] = (
                    users[referrer_id].get("referrals", 0) + 1
                )

                changed = True

            if changed:
                github_save(users, sha)

    except Exception as e:
        print("Referral error:", e)

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 شروع کسب درآمد",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ]
    ]

    await update.message.reply_text(
        "🎉 به EarnZood خوش آمدید!\n\n"
        "💰 روش‌های کسب درآمد:\n\n"
        "🎁 پاداش روزانه\n"
        "📺 مشاهده تبلیغات\n"
        "📋 انجام تسک‌ها\n"
        "👥 دعوت دوستان\n\n"
        "🚀 برای شروع روی دکمه زیر بزنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def main():

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is not configured")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    print("EarnZood Bot is running...")

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
