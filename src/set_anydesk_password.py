#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Окремий скрипт для встановлення пароля AnyDesk з адмін правами
"""

import subprocess
import sys
import os
import time

ANYDESK_PATH = sys.argv[1] if len(sys.argv) > 1 else None
PASSWORD = "r3moteh4nd"

if not ANYDESK_PATH or not os.path.exists(ANYDESK_PATH):
    print("[!] AnyDesk не знайдено")
    sys.exit(1)

try:
    print("[*] Встановлюю пароль AnyDesk...")

    # Запустити команду встановлення пароля
    cmd = [ANYDESK_PATH, "--set-password", "_full_access"]

    result = subprocess.run(
        cmd,
        input=PASSWORD,
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode == 0:
        print("[✓] Пароль встановлено!")
    else:
        print(f"[!] Код: {result.returncode}")
        print(f"[DEBUG] stderr: {result.stderr}")

    sys.exit(0)

except Exception as e:
    print(f"[!] Помилка: {e}")
    sys.exit(1)
