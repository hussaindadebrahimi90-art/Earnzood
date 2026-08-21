import os
import json
import base64
import urllib.request
import urllib.error

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_OWNER = "hussaindadebrahimi90-art"
GITHUB_REPO = "Earnzood"
USERS_FILE = "user.json"
BRANCH = "main"

BOT_USERNAME = "Earnzood_bot"
WEB_APP_URL = "https://hussaindadebrahimi90-art.github.io/Earnzood/"

ADMIN_ID = 8009297169

REFERRAL_REWARD = 0.40


# =========================================================
# GITHUB
# =========================================================

def github_url():
    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{USERS_FILE}"
    )


def github_request(method="GET", data=None):

    req = urllib.request.Request(
        github_url(),
        method=method,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "EarnZood-Bot",
        },
    )

    if data is not None:

        req.add_header(
            "Content-Type",
            "application/json"
        )

        data = json.dumps(data).encode("utf-8")

    with urllib.request.urlopen(
        req,
        data=data,
        timeout=20
    ) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


async def load_users():

    def load():

        try:

            result = github_request("GET")

            content = base64.b64decode(
                result["content"].replace("\n", "")
            ).decode("utf-8")

            return json.loads(content), result["sha"]

        except Exception as e:

            print(
                "LOAD ERROR:",
                repr(e)
            )

            return {}, None

    return await __import__("asyncio").to_thread(load)


async def save_users(data, sha):

    def save():

        content = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )

        encoded = base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")

        payload = {
            "message": "Update EarnZood users",
            "content": encoded,
            "branch": BRANCH,
        }

        if sha:
            payload["sha"] = sha

        try:

            return github_request(
                "PUT",
                payload
            )

        except urllib.error.HTTPError as e:

            print(
                "SAVE ERROR:",
                e.read().decode()
            )

            return None

        except Exception as e:

            print(
                "SAVE ERROR:",
                repr(e)
            )

            return None

    return await __import__("asyncio").to_thread(save)


# =========================================================
# HELPERS
# =========================================================

def is_admin(user_id):

    return int(user_id) == ADMIN_ID


def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 ورود به EarnZood",
                web_app=WebAppInfo(
                    url=WEB_APP_URL
                )
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ پنل مدیریت",
                callback_data="admin"
            )
        ],
    ])


def admin_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📊 آمار",
                callback_data="admin_stats"
            ),
            InlineKeyboardButton(
                "👥 کاربران",
                callback_data="admin_users"
            ),
        ],
        [
            InlineKeyboardButton(
                "💰 مدیریت موجودی",
                callback_data="admin_balance"
            )
        ],
        [
            InlineKeyboardButton(
                "🚫 مسدود کردن",
                callback_data="admin_block"
            ),
            InlineKeyboardButton(
                "🟢 فعال کردن",
                callback_data="admin_unblock"
            ),
        ],
        [
            InlineKeyboardButton(
                "🎁 تنظیم پاداش‌ها",
                callback_data="admin_rewards"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 پیام همگانی",
                callback_data="admin_broadcast"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="home"
            )
        ],
    ])


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    user = update.effective_user

    users, sha = await load_users()

    user_id = str(user.id)

    if user_id not in users:

        users[user_id] = {
            "id": user.id,
            "username": user.username or "",
            "first_name": user.first_name or "",
            "balance": 0.0,
            "referrals": 0,
            "referrer": None,
        }

        await save_users(
            users,
            sha
        )

    else:

        users[user_id]["username"] = (
            user.username or ""
        )

        users[user_id]["first_name"] = (
            user.first_name or ""
        )

        await save_users(
            users,
            sha
        )

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
        reply_markup=main_menu()
    )


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "🚫 دسترسی ندارید.",
            show_alert=True
        )

        return

    await query.edit_message_text(
        "⚙️ پنل مدیریت EarnZood\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_menu()
    )


# =========================================================
# STATISTICS
# =========================================================

async def admin_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):
        return

    users, _ = await load_users()

    total = len(users)

    balance = 0
    referrals = 0

    for user in users.values():

        balance += float(
            user.get("balance", 0)
        )

        referrals += int(
            user.get("referrals", 0)
        )

    text = f"""
📊 آمار EarnZood

👥 تعداد کاربران:
{total}

💰 مجموع موجودی:
${balance:.2f}

👥 مجموع Referral:
{referrals}
"""

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="admin"
                )
            ]
        ])
    )


# =========================================================
# USERS
# =========================================================

async def admin_users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):
        return

    users, _ = await load_users()

    if not users:

        text = "👥 هنوز هیچ کاربری ثبت نشده است."

    else:

        lines = []

        for user_id, user in list(
            users.items()
        )[:20]:

            name = (
                user.get("first_name")
                or user.get("username")
                or "Unknown"
            )

            bal = float(
                user.get("balance", 0)
            )

            lines.append(
                f"👤 {name}\n"
                f"🆔 {user_id}\n"
                f"💰 ${bal:.2f}\n"
                f"👥 Ref: {user.get('referrals', 0)}"
            )

        text = (
            "👥 آخرین کاربران:\n\n"
            + "\n\n".join(lines)
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="admin"
                )
            ]
        ])
    )


# =========================================================
# BALANCE
# =========================================================

async def admin_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):
        return

    context.user_data["admin_action"] = "balance"

    await query.edit_message_text(
        "💰 مدیریت موجودی\n\n"
        "Telegram ID کاربر را ارسال کن:"
    )


# =========================================================
# BLOCK
# =========================================================

async def admin_block(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):
        return

    context.user_data["admin_action"] = "block"

    await query.edit_message_text(
        "🚫 Telegram ID کاربر را ارسال کن:"
    )


# =========================================================
# UNBLOCK
# =========================================================

async def admin_unblock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):
        return

    context.user_data["admin_action"] = "unblock"

    await query.edit_message_text(
        "🟢 Telegram ID کاربر را ارسال کن:"
    )


# =========================================================
# REWARDS
# =========================================================

async def admin_rewards(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):
        return

    await query.edit_message_text(
        "🎁 تنظیم پاداش‌ها\n\n"
        "فعلاً مقدار Referral در کد تنظیم شده است:\n\n"
        f"👥 Referral Reward: ${REFERRAL_REWARD:.2f}\n\n"
        "در مرحله بعد این بخش را قابل تغییر از داخل پنل می‌کنیم.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="admin"
                )
            ]
        ])
    )


# =========================================================
# BROADCAST
# =========================================================

async def admin_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):
        return

    context.user_data["admin_action"] = "broadcast"

    await query.edit_message_text(
        "📢 متن پیام همگانی را ارسال کن:"
    )


# =========================================================
# TEXT HANDLER
# =========================================================

async def admin_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    if not is_admin(
        update.effective_user.id
    ):
        return

    action = context.user_data.get(
        "admin_action"
    )

    if not action:
        return

    text = update.message.text.strip()

    # -----------------------------------------------------
    # BALANCE
    # -----------------------------------------------------

    if action == "balance":

        if not text.isdigit():

            await update.message.reply_text(
                "❌ Telegram ID باید عدد باشد."
            )

            return

        target_id = text

        users, sha = await load_users()

        if target_id not in users:

            await update.message.reply_text(
                "❌ کاربر پیدا نشد."
            )

            context.user_data.clear()

            return

        context.user_data[
            "balance_user"
        ] = target_id

        context.user_data[
            "admin_action"
        ] = "balance_amount"

        await update.message.reply_text(
            "💰 مقدار تغییر موجودی را ارسال کن.\n\n"
            "برای افزایش:\n"
            "+1\n\n"
            "برای کاهش:\n"
            "-1"
        )

        return

    # -----------------------------------------------------
    # BALANCE AMOUNT
    # -----------------------------------------------------

    if action == "balance_amount":

        try:

            amount = float(text)

        except ValueError:

            await update.message.reply_text(
                "❌ مقدار نامعتبر است."
            )

            return

        target_id = context.user_data.get(
            "balance_user"
        )

        users, sha = await load_users()

        if target_id not in users:

            await update.message.reply_text(
                "❌ کاربر پیدا نشد."
            )

            context.user_data.clear()

            return

        old = float(
            users[target_id].get(
                "balance",
                0
            )
        )

        new = max(
            0,
            old + amount
        )

        users[target_id]["balance"] = round(
            new,
            2
        )

        await save_users(
            users,
            sha
        )

        await update.message.reply_text(
            f"✅ موجودی تغییر کرد.\n\n"
            f"🆔 {target_id}\n"
            f"💰 قبلی: ${old:.2f}\n"
            f"💰 جدید: ${new:.2f}"
        )

        context.user_data.clear()

        return

    # -----------------------------------------------------
    # BLOCK
    # -----------------------------------------------------

    if action == "block":

        if not text.isdigit():

            await update.message.reply_text(
                "❌ Telegram ID نامعتبر است."
            )

            return

        users, sha = await load_users()

        if text not in users:

            await update.message.reply_text(
                "❌ کاربر پیدا نشد."
            )

            context.user_data.clear()

            return

        users[text]["blocked"] = True

        await save_users(
            users,
            sha
        )

        await update.message.reply_text(
            "🚫 کاربر مسدود شد."
        )

        context.user_data.clear()

        return

    # -----------------------------------------------------
    # UNBLOCK
    # -----------------------------------------------------

    if action == "unblock":

        if not text.isdigit():

            await update.message.reply_text(
                "❌ Telegram ID نامعتبر است."
            )

            return

        users, sha = await load_users()

        if text not in users:

            await update.message.reply_text(
                "❌ کاربر پیدا نشد."
            )

            context.user_data.clear()

            return

        users[text]["blocked"] = False

        await save_users(
            users,
            sha
        )

        await update.message.reply_text(
            "🟢 کاربر فعال شد."
        )

        context.user_data.clear()

        return

    # -----------------------------------------------------
    # BROADCAST
    # -----------------------------------------------------

    if action == "broadcast":

        users, _ = await load_users()

        sent = 0
        failed = 0

        await update.message.reply_text(
            "📢 ارسال پیام شروع شد..."
        )

        for user_id, user in users.items():

            if user.get("blocked", False):
                continue

            try:

                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=text
                )

                sent += 1

            except Exception as e:

                failed += 1

                print(
                    "Broadcast error:",
                    user_id,
                    repr(e)
                )

        await update.message.reply_text(
            f"📢 ارسال تمام شد.\n\n"
            f"✅ موفق: {sent}\n"
            f"❌ ناموفق: {failed}"
        )

        context.user_data.clear()

        return


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    data = query.data

    if data == "admin":
        await admin_panel(
            update,
            context
        )

    elif data == "admin_stats":
        await admin_stats(
            update,
            context
        )

    elif data == "admin_users":
        await admin_users(
            update,
            context
        )

    elif data == "admin_balance":
        await admin_balance(
            update,
            context
        )

    elif data == "admin_block":
        await admin_block(
            update,
            context
        )

    elif data == "admin_unblock":
        await admin_unblock(
            update,
            context
        )

    elif data == "admin_rewards":
        await admin_rewards(
            update,
            context
        )

    elif data == "admin_broadcast":
        await admin_broadcast(
            update,
            context
        )

    elif data == "home":

        await query.answer()

        await query.edit_message_text(
            "🏠 منوی اصلی EarnZood",
            reply_markup=main_menu()
        )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not configured"
        )

    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN is not configured"
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
        CallbackQueryHandler(
            callback_router
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_text
        )
    )

    print(
        "EarnZood Bot is running..."
    )

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
