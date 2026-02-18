import logging
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from .config import BOT_TOKEN, PUBLIC_URL, WEBHOOK_PATH, PORT, ADMIN_IDS
from .db import init_db, forgive_user, set_rules, set_welcome, get_strikes
from .moderation import check_flood, check_link_spam, apply_punishment, send_welcome_if_any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")

def _is_owner(uid: int) -> bool:
    return uid in ADMIN_IDS

def _reply_user(update: Update):
    m = update.effective_message
    if not m or not m.reply_to_message or not m.reply_to_message.from_user:
        return None
    return m.reply_to_message.from_user

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("✅ Bot running. /help")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Owner commands (reply to user):\n"
        "/status\n/forgive\n/unrestrict\n/ban\n\n"
        "Chat settings:\n"
        "/rules\n/setrules <text>\n/setwelcome <text>"
    )

async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .db import get_chat_settings
    from .config import DEFAULT_RULES
    chat = update.effective_chat
    if not chat:
        return
    _, rules = get_chat_settings(chat.id)
    await update.effective_message.reply_text(rules or DEFAULT_RULES)

async def setrules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    if not u or not c or not _is_owner(u.id):
        return
    parts = update.effective_message.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.effective_message.reply_text("Usage: /setrules <text>")
        return
    set_rules(c.id, parts[1].strip())
    await update.effective_message.reply_text("✅ Rules updated")

async def setwelcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    if not u or not c or not _is_owner(u.id):
        return
    parts = update.effective_message.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.effective_message.reply_text("Usage: /setwelcome <text>")
        return
    set_welcome(c.id, parts[1].strip())
    await update.effective_message.reply_text("✅ Welcome updated")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    if not u or not c or not _is_owner(u.id):
        return
    t = _reply_user(update)
    if not t:
        await update.effective_message.reply_text("Reply to user msg with /status")
        return
    await update.effective_message.reply_text(f"User: {t.id}\nStrikes: {get_strikes(c.id, t.id)}")

async def forgive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    if not u or not c or not _is_owner(u.id):
        return
    t = _reply_user(update)
    if not t:
        await update.effective_message.reply_text("Reply to user msg with /forgive")
        return
    forgive_user(c.id, t.id)
    await update.effective_message.reply_text("✅ Strikes reset")

async def unrestrict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    if not u or not c or not _is_owner(u.id):
        return
    t = _reply_user(update)
    if not t:
        await update.effective_message.reply_text("Reply to user msg with /unrestrict")
        return
    perms = ChatPermissions(
        can_send_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_invite_users=True,
    )
    await context.bot.restrict_chat_member(c.id, t.id, perms)
    await update.effective_message.reply_text("✅ Unrestricted")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    c = update.effective_chat
    if not u or not c or not _is_owner(u.id):
        return
    t = _reply_user(update)
    if not t:
        await update.effective_message.reply_text("Reply to user msg with /ban")
        return
    await context.bot.ban_chat_member(c.id, t.id)
    await update.effective_message.reply_text("⛔ Banned")

async def new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_welcome_if_any(update, context)

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user:
        return
    if not msg.text and not msg.caption:
        return

    # admin bypass
    try:
        m = await context.bot.get_chat_member(chat.id, user.id)
        if m.status in ("administrator", "creator"):
            return
    except Exception:
        pass

    text = msg.text or msg.caption or ""
    if check_flood(chat.id, user.id, text):
        await apply_punishment(update, context, "Flood/Repeated messages")
        return
    if check_link_spam(text):
        await apply_punishment(update, context, "Link spam / unauthorized link")
        return

def build() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("rules", rules_cmd))
    app.add_handler(CommandHandler("setrules", setrules_cmd))
    app.add_handler(CommandHandler("setwelcome", setwelcome_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("forgive", forgive_cmd))
    app.add_handler(CommandHandler("unrestrict", unrestrict_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_members))
    app.add_handler(MessageHandler(filters.TEXT | filters.Caption(True), on_message))
    return app

def main():
    init_db()
    app = build()
    webhook_url = f"{PUBLIC_URL}{WEBHOOK_PATH}"
    log.info("Webhook URL: %s", webhook_url)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,          # must match WEBHOOK_PATH without leading slash
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
