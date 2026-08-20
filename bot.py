import os
import json
import base64
import urllib.request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

WEB_APP_URL = "https://hussaindadebrahimi90-art.github.io/Earnzood/"
BOT_USERNAME = "Earnzood_bot"

REPOSITORY = os.getenv(
    "GITHUB_REPOSITORY",
    "hussaindadebrahimi90-art/Earnzood"
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DATA_FILE = "users.json"


# =========================
# GitHub Storage
# =========================

def github_request(url, method="GET", data=None):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "EarnZood-Bot"
    }

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def load_users():
    if not GITHUB_TOKEN:
        return {}

    try:
        url = (
            f"https://api.github.com/repos/"
            f"{REPOSITORY}/contents/{DATA_FILE}"
        )

        result = github_request(url)

        content = base64.b64decode(
            result["content"]
        ).decode("utf-8")

        return json.loads(content)

    except Exception:
        return {}


def save_users(users):
    if not GITHUB_TOKEN:
        print("WARNING: GITHUB_TOKEN is not configured")
        return

    url = (
        f"https://api.github.com/repos/"
        f"{REPOSITORY}/contents/{DATA_FILE}"
    )

    try:
        current = github_request(url)
        sha = current["sha"]
    except Exception:
        sha = None

    content = json.dumps(
        users,
        ensure_ascii=False,
        indent=2
    )

    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": "Update EarnZood users",
        "content": encoded,
        "branch": "main"
    }

    if sha:
        payload["sha"] = sha

    github_request(
        url,
        method="PUT",
        data=json.dumps(payload).encode()
    )


# =========================
# User System
# =========================

def get_user(users, user_id):
    return users.get(str(user_id))


def create_user(users, user_id, username="", first_name=""):
    uid = str(user_id)

    if uid not in users:
        users[uid] = {
            "id": user_id,
            "username": username or "",
            "first_name": first_name or "",
            "balance": 0.0,
            "referrals": [],
            "referred_by": None,
            "referral_earned": 0.0
        }
        return True

    return False


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    users = load_users()

    user_id = user.id

    is_new = create_user(
        users,
        user_id,
        user.username,
        user.first_name
    )

    referral_id = None

    if context.args:
        referral_id = context.args[0]

    # =========================
    # Referral
    # =========================

    if is_new and referral_id:

        try:
            referral_id = int(referral_id)

            # کاربر نمی‌تواند خودش را دعوت کند
            if referral_id != user_id:

                inviter = get_user(
                    users,
                    referral_id
                )

                if inviter:

                    users[str(user_id)]["referred_by"] = referral_id

                    # پاداش رفرال
                    referral_reward = 0.10

                    users[str(referral_id)]["balance"] += referral_reward

                    users[str(referral_id)]["referrals"].append(
                        user_id
                    )

                    users[str(referral_id)]["referral_earned"] += referral_reward

        except ValueError:
            pass

    if is_new:
        save_users(users)

    # =========================
    # Mini App Button
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

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    text = f"""
🎉 به EarnZood خوش آمدید!

💰 روش‌های کسب درآمد:

🎁 پاداش روزانه
📺 مشاهده تبلیغات
📋 انجام تسک‌ها
👥 دعوت دوستان

👥 لینک دعوت شما:

https://t.me/{BOT_USERNAME}?start={user_id}

💎 با دعوت دوستان می‌توانید پاداش دریافت کنید.

🚀 برای شروع روی دکمه زیر بزنید.
"""

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )


# =========================
# PROFILE
# =========================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    users = load_users()

    data = get_user(
        users,
        user.id
    )

    if not data:
        create_user(
            users,
            user.id,
            user.username,
            user.first_name
        )
        save_users(users)
        data = users[str(user.id)]

    link = (
        f"https://t.me/"
        f"{BOT_USERNAME}"
        f"?start={user.id}"
    )

    text = f"""
👤 حساب کاربری

🆔 ID: {user.id}

💰 موجودی:
${data["balance"]:.2f}

👥 تعداد دعوت‌ها:
{len(data["referrals"])}

🔗 لینک دعوت:

{link}
"""

    await update.message.reply_text(text)


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not configured"
        )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "profile",
            profile
        )
    )

    print("EarnZood Bot is running...")

    # مهم:
    # run_polling را await نمی‌کنیم
    app.run_polling()


if __name__ == "__main__":
    main()
