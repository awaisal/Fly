Fly.io Telegram Webhook Bot

Required secrets:
- BOT_TOKEN
- PUBLIC_URL (https://your-app.fly.dev)
- ADMIN_IDS (numeric telegram user ids)

Volume for persistence:
- fly volumes create botdata --size 1
Mounted to /data
