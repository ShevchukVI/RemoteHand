import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ✅ В DEV режимі - завантажуємо .env файл
if not getattr(sys, 'frozen', False):
    load_dotenv()

APP_NAME = "RemoteHand"
RDP_HOST = "23.88.7.196"
RDP_PORT = 4420
PING_HOST = "23.88.7.196"

# 🔒 ТОКЕНИ - читаємо прямо з os.environ (працює і в DEV, і в RELEASE)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 🔍 DEBUG - перевірка наявності токенів (можна видалити після тесту)
if not TELEGRAM_TOKEN:
    print("⚠️ WARNING: TELEGRAM_TOKEN не знайдено!")
if not TELEGRAM_CHAT_ID:
    print("⚠️ WARNING: TELEGRAM_CHAT_ID не знайдено!")

# Файли
LOCK_FILE = Path.home() / ".remotehand" / "lock"
