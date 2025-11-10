import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ✅ ЗАВАНТАЖИТИ .env З ПРАВИЛЬНОГО МІСЦЯ
if getattr(sys, 'frozen', False):
    # Якщо це EXE - .env в _MEIPASS (тимчасова директорія PyInstaller)
    env_path = Path(sys._MEIPASS) / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Завантажено .env з {env_path}")
    else:
        print(f"⚠️ .env не знайдено в {sys._MEIPASS}")
else:
    # DEV режим - .env в корені проєкту
    load_dotenv()
    print("✅ Завантажено .env (DEV режим)")

APP_NAME = "RemoteHand"
RDP_HOST = "23.88.7.196"
RDP_PORT = 4420
PING_HOST = "23.88.7.196"

# 🔒 ТОКЕНИ
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# 🔍 DEBUG - перевірка
if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN порожній!")
if not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM_CHAT_ID порожній!")

# Файли
LOCK_FILE = Path.home() / ".remotehand" / "lock"
