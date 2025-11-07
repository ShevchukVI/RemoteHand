import os
from pathlib import Path

APP_NAME = "RemoteHand"
VERSION_FILE = "version.txt"
GITHUB_REPO = "ShevchukVI/RemoteHand"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# RDP налаштування
RDP_HOST = "23.88.7.196"
RDP_PORT = "4420"
PING_HOST = "8.8.8.8"

# Шляхи
BASE_DIR = Path(__file__).parent
LOCK_FILE = BASE_DIR / f"{APP_NAME}.lock"