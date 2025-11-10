import os
from pathlib import Path

# (ВИДАЛЕНО) from dotenv import load_dotenv
# (ВИДАЛЕНО) load_dotenv()

APP_NAME = "RemoteHand"
RDP_HOST = "23.88.7.196"
RDP_PORT = 4420
PING_HOST = "23.88.7.196"

# 🔒 ЗІ ЗМІННИХ СЕРЕДОВИЩА
# (ВИПРАВЛЕНО) Це єдине місце, де ми читаємо змінні.
# main.py відповідає за завантаження .env, ЯКЩО це DEV-режим.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Файли
LOCK_FILE = Path.home() / ".remotehand" / "lock"