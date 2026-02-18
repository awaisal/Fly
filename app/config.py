import os

def _required(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

BOT_TOKEN = _required("BOT_TOKEN")

# Example: https://your-app.fly.dev
PUBLIC_URL = _required("PUBLIC_URL").rstrip("/")

# comma-separated numeric telegram user ids
ADMIN_IDS = set()
raw = os.getenv("ADMIN_IDS", "").strip()
if raw:
    ADMIN_IDS = {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}

# fly serves on 8080 internally (we keep it fixed)
PORT = int(os.getenv("PORT", "8080"))

# DB path (use /data only if volume mounted)
DB_PATH = os.getenv("DB_PATH", "/data/bot.db")

FLOOD_WINDOW_SEC = int(os.getenv("FLOOD_WINDOW_SEC", "8"))
FLOOD_MAX_MSG = int(os.getenv("FLOOD_MAX_MSG", "6"))
REPEAT_MAX = int(os.getenv("REPEAT_MAX", "3"))
LINK_SPAM_ENABLED = os.getenv("LINK_SPAM_ENABLED", "1") == "1"

DEFAULT_WELCOME = os.getenv("DEFAULT_WELCOME", "Welcome! ✅ Rules follow karo, spam mat karo 🙂")
DEFAULT_RULES = os.getenv(
    "DEFAULT_RULES",
    "Rules:\n1) Spam/Flood nahi\n2) Links bina permission nahi\n3) Abuse nahi\n4) Off-topic limit\nViolation par auto restriction."
)

# Webhook path = token (simple + secure)
WEBHOOK_PATH = f"/{BOT_TOKEN}"
