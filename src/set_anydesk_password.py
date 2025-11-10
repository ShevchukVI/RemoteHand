#!/usr/bin/env python3
"""Встановлення пароля AnyDesk з адмін правами"""

import subprocess
import sys
import os
import time
import ctypes

ANYDESK_PATH = sys.argv[1] if len(sys.argv) > 1 else None
PASSWORD = os.getenv("ANYDESK_PASSWORD", "r3moteh4nd")

if not ANYDESK_PATH or not os.path.exists(ANYDESK_PATH):
    print("[!] AnyDesk не знайдено")
    sys.exit(1)

# Перевіримо чи запущено з адмін правами
try:
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    if not is_admin:
        print("[!] Потрібні адмін права")
        # Перезапустити з адмін правами
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{__file__}" "{ANYDESK_PATH}"',
            None,
            1  # SW_SHOW
        )
        sys.exit(0)
except:
    pass

try:
    print(f"[*] Встановлюю пароль AnyDesk (у адміні)...")
    time.sleep(1)

    # Встановити через stdin
    cmd = [ANYDESK_PATH, "--set-password", "_full_access"]

    result = subprocess.run(
        cmd,
        input=PASSWORD + "\n",
        capture_output=True,
        text=True,
        timeout=10
    )

    print(f"[CODE] {result.returncode}")
    if result.returncode in [0, 8000]:
        print("[✓] Пароль встановлено!")
    else:
        print(f"[!] Код: {result.returncode}")

    sys.exit(0)

except Exception as e:
    print(f"[!] Помилка: {e}")
    sys.exit(1)
