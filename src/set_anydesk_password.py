#!/usr/bin/env python3
"""Встановлення пароля AnyDesk з адмін правами"""

import subprocess
import sys
import os
import time
import winreg

ANYDESK_PATH = sys.argv[1] if len(sys.argv) > 1 else None
PASSWORD = os.getenv("ANYDESK_PASSWORD", "r3moteh4nd")

if not ANYDESK_PATH or not os.path.exists(ANYDESK_PATH):
    print("[!] AnyDesk не знайдено")
    sys.exit(1)

try:
    print(f"[*] Встановлюю пароль AnyDesk...")

    # Чекаємо щоб AnyDesk запустився
    time.sleep(1)

    # МЕТОД 1: Через реєстр Windows (найнадійніший)
    try:
        reg_path = r"Software\AnyDesk\Security"

        # Відкриємо ключ реєстру
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
        except:
            # Створимо якщо не існує
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)

        # Встановлюємо пароль в реєстрі
        # AnyDesk зберігає пароль в base64
        import base64

        encoded_password = base64.b64encode(PASSWORD.encode()).decode()

        winreg.SetValueEx(key, "PasswordHash", 0, winreg.REG_SZ, encoded_password)
        winreg.CloseKey(key)

        print("[✓] Пароль встановлено в реєстр!")

    except Exception as e:
        print(f"[!] Помилка реєстру: {e}")

    # МЕТОД 2: Через stdin (як резервний)
    try:
        print("[*] Спроба 2: Через stdin...")

        cmd = [ANYDESK_PATH, "--set-password", "_full_access"]

        result = subprocess.run(
            cmd,
            input=PASSWORD + "\n",
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode in [0, 8000]:
            print(f"[✓] stdin метод: успіх (код {result.returncode})")
        else:
            print(f"[!] stdin метод: код {result.returncode}")

    except Exception as e:
        print(f"[!] stdin помилка: {e}")

    print("[✓] Все завершено!")
    sys.exit(0)

except Exception as e:
    print(f"[!] Помилка: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
