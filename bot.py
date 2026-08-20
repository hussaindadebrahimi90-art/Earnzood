import os
import json
import base64
import requests

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)


# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "hussaindadebrahimi90-art/Earnzood"
FILE_PATH = "users.json"
BRANCH = "main"

WEB_APP_URL = "https://hussaindadebrahimi90-art.github.io/Earnzood/"


# =========================
# GITHUB
# =========================

def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def load_users():

    url = (
        f"https://api.github.com/repos/"
        f"{REPO}/contents/{FILE_PATH}?ref={BRANCH}"
    )

    response = requests.get(
        url,
        headers=github_headers(),
        timeout=20
    )

    if response.status_code == 404:
        return {}, None

    if response.status_code != 200:
        raise RuntimeError(
            f"GitHub load error: "
            f"{response.status_code} {response.text}"
        )

    data = response.json()

    content = base64.b64decode(
        data["content"]
    ).decode("utf-8")

    users = json.loads(content)

    return users, data["sha"]


def save_users(users, sha):

    content = json.dumps(
        users,
        ensure_ascii=False,
        indent=2
    )

    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    url = (
        f"https://api.github.com/repos/"
        f"{REPO}/contents/{FILE_PATH}"
    )

    payload = {
        "message": "Update EarnZood users",
        "content": encoded,
        "branch": BRANCH
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        url,
        headers=github_headers(),
        json=payload,
        timeout=20
    )

    if response.status_code not in (200, 201):

        raise RuntimeError(
            f"GitHub save error: "
            f"{response.status_code} {response.text}"
        )


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user or not update.message:
        return

    user_id = str(user.id)

    # -------------------------
    # Referral parameter
    # -------------------------

    referrer_id = None

    if context.args:

        value = context.args[0].strip()

        if value.isdigit():
            referrer_id = value


    try:

        users, sha = load_users()

        changed = False


        # =========================
        # NEW USER
        # =========================

        if user_id not in users:

            users[user_id] = {
                "id": user.id,
                "username": user.username or "",
                "first_name": user.first_name or "",
                "balance": 0.0,
                "referrals": 0,
                "referrer": None
            }

            changed = True


            # =========================
            # REGISTER REFERRAL
            # =========================

            if (
                referrer_id
                and referrer_id != user_id
                and referrer_id in users
            ):

                users[user_id]["referrer"] = referrer_id

                users[referrer_id]["referrals"] = (
                    users[referrer_id].get(
                        "referrals",
                        0
                    ) + 1
                )


        # =========================
        # EXISTING USER
        # =========================

        else:

            # Referral can only be assigned once

            if (
                referrer_id
                and referrer_id != user_id
                and not users[user_id].get("referrer")
                and referrer_id in users
            ):

                users[user_id]["referrer"] = referrer_id

                users[referrer_id]["referrals"] = (
                    users[referrer_id].get(
                        "referrals",
                        0
                    ) + 1
                )

                changed = True


        # =========================
        # SAVE
        # =========================

        if changed:

            save_users(
                users,
                sha
            )

            print(
                f"User {user_id} saved successfully."
            )


    except Exception as error:

        print(
            "Referral/GitHub error:",
            error
        )


    # =========================
    # MINI APP BUTTON
    # =========================

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 شروع کسب درآمد",
                web_app=WebAppInfo(
                    url=WEB_APP_URL
                )
            )
        ]
    ]

    markup = InlineKeyboardMarkup(
        keyboard
    )


    # =========================
    # WELCOME MESSAGE
    # =========================

    text = """
🎉 به EarnZood خوش آمدید!

💰 روش‌های کسب درآمد:

🎁 پاداش روزانه
📺 مشاهده تبلیغات
📋 انجام تسک‌ها
👥 دعوت دوستان

🚀 برای شروع روی دکمه زیر بزنید.
"""

    await update.message.reply_text(
        text,
        reply_markup=markup
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN is not configured"
        )

    if not GITHUB_TOKEN:

        raise RuntimeError(
            "GITHUB_TOKEN is not configured"
        )


    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    print(
        "EarnZood Bot is running..."
    )


    # مهم:
    # asyncio.run استفاده نمی‌کنیم.
    # خود run_polling مدیریت Event Loop را انجام می‌دهد.

    application.run_polling()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
