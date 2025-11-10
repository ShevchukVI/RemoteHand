import os
import sys
import subprocess
import time
import logging
import psutil
import platform
import ctypes
import socket
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

UNATTENDED_PASSWORD = "r3moteh4nd"


class AnyDeskManager:
    """Менеджер для AnyDesk"""

    def __init__(self, config_manager, telegram_api):
        self.config = config_manager
        self.telegram = telegram_api
        self.anydesk_path = self.find_anydesk()
        self._is_running = False
        self.connection_id = None

    def find_anydesk(self) -> Optional[str]:
        """Знайти AnyDesk"""
        possible_paths = [
            r"C:\Program Files\AnyDesk\AnyDesk.exe",
            r"C:\Program Files (x86)\AnyDesk\AnyDesk.exe",
            os.path.expanduser("~\\AppData\\Local\\AnyDesk\\AnyDesk.exe"),
            os.path.expanduser("~\\AppData\\Roaming\\AnyDesk\\AnyDesk.exe"),
            os.path.expanduser("~\\Downloads\\AnyDesk.exe"),
            r"C:\ProgramData\AnyDesk\AnyDesk.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ AnyDesk знайдено: {path}")
                return path

        logger.warning("⚠️ AnyDesk не знайдено")
        return None

    def download_anydesk(self) -> bool:
        """Завантажити AnyDesk"""
        if self.anydesk_path:
            return True

        logger.info("📥 Завантаження AnyDesk...")
        try:
            import urllib.request
            downloads_dir = os.path.expanduser("~\\Downloads")
            save_path = os.path.join(downloads_dir, "AnyDesk.exe")
            download_url = "https://download.anydesk.com/AnyDesk.exe"

            if not os.path.exists(save_path):
                logger.info(f"Завантажу...")
                urllib.request.urlretrieve(download_url, save_path)

            logger.info("Запуск встановлювача...")
            subprocess.Popen([save_path])

            logger.info("Чекаю на встановлення (90 сек)...")
            for i in range(90):
                time.sleep(1)
                self.anydesk_path = self.find_anydesk()
                if self.anydesk_path:
                    logger.info(f"✅ AnyDesk встановлено")
                    time.sleep(3)
                    return True

            return False
        except Exception as e:
            logger.error(f"❌ Помилка: {e}")
            return False

    def check_if_running(self) -> bool:
        """Перевірити, чи AnyDesk запущено"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'anydesk' in proc.info['name'].lower():
                    logger.info(f"ℹ️ AnyDesk запущено (PID: {proc.info['pid']})")
                    self._is_running = True
                    return True
        except:
            pass
        self._is_running = False
        return False

    def launch_anydesk(self) -> bool:
        """Запустити AnyDesk"""
        if self.check_if_running():
            return True

        if not self.anydesk_path or not Path(self.anydesk_path).exists():
            logger.error("Шлях невідомий")
            return False

        try:
            logger.info(f"🚀 Запускаю AnyDesk...")
            subprocess.Popen(self.anydesk_path)
            time.sleep(5)

            if self.check_if_running():
                logger.info("✅ AnyDesk запущено")
                return True
            else:
                self._is_running = True
                return True
        except Exception as e:
            logger.error(f"❌ Помилка: {e}")
            return False

    def set_password_with_admin(self) -> bool:
        """
        Запускає *саму себе* з адмін правами для встановлення пароля.
        Коректно обробляє DEV-режим.
        """
        if not self.anydesk_path:
            logger.error("Шлях AnyDesk невідомий, не можу встановити пароль")
            return False

        try:
            logger.info(f"🔐 Запускаю встановлення пароля з адмін правами...")

            # Передати пароль як змінну середовища
            env = os.environ.copy()
            env["ANYDESK_PASSWORD"] = UNATTENDED_PASSWORD

            if getattr(sys, 'frozen', False):
                # Режим EXE: запускаємо сам .exe
                executable = sys.executable
                arguments = f'--set-anydesk-password "{self.anydesk_path}"'
                logger.info(f"EXE Mode Admin Lauch: {executable} {arguments}")
            else:
                # Режим DEV: запускаємо python.exe + [скрипт]
                executable = sys.executable  # python.exe
                # (ВИПРАВЛЕНО) Використовуємо Path.cwd() для коректного шляху в DEV
                # Викликаємо dev_run.py, який налаштує sys.path
                script_path = str(Path.cwd() / "dev_run.py")
                arguments = f'"{script_path}" --set-anydesk-password "{self.anydesk_path}"'
                logger.info(f"DEV Mode Admin Lauch: {executable} {arguments}")

            # Запустити скрипт з адмін правами
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Запит адмін прав
                executable,  # RemoteHand.exe або python.exe
                arguments,  # Аргументи
                None,
                1  # SW_SHOW - показати вікно (UAC)
            )

            logger.info(f"✅ Запрос адмін прав надіслано користувачу")
            return True

        except Exception as e:
            logger.error(f"❌ Помилка запуску адмін-процесу: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_connection_id(self) -> Optional[str]:
        """Отримати ID"""
        if not self.anydesk_path:
            return None

        try:
            logger.info("📌 Отримую ID...")

            result = subprocess.run(
                [self.anydesk_path, '--get-id'],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )

            if result.returncode == 0:
                connection_id = result.stdout.strip()
                if connection_id and connection_id.isdigit():
                    logger.info(f"✅ ID: {connection_id}")
                    self.connection_id = connection_id
                    return connection_id

        except Exception as e:
            logger.error(f"❌ Помилка: {e}")

        return None

    def start(self, password: str = None) -> Tuple[Optional[str], Optional[str]]:
        """(ОНОВЛЕНО) Запустити AnyDesk з очікуванням адмін-процесу"""
        password = UNATTENDED_PASSWORD

        # Крок 1: Якщо вже запущено (нічого не змінилось)
        if self.check_if_running():
            logger.info("AnyDesk вже запущено")
            connection_id = self.get_connection_id()
            if connection_id:
                try:
                    user_name = self.config.get("user_name", "")
                    self.telegram.send_anydesk_info(
                        self.config.store_location_text,
                        user_name, socket.gethostname(), connection_id, password
                    )
                except Exception as e:
                    logger.error(f"❌ Telegram: {e}")
            return connection_id, password

        # Крок 2: Завантажити якщо потрібно
        if not self.anydesk_path:
            if not self.download_anydesk():
                return None, None

        # Крок 3: Запустити
        if not self.launch_anydesk():
            return None, None

        # Крок 4: ВСТАНОВИТИ ПАРОЛЬ (З ОЧІКУВАННЯМ)
        logger.info("🔐 Встановлення пароля...")

        # (ОНОВЛЕНО) Використовуємо C:\ProgramData - спільну папку
        flag_file = Path(os.environ.get("PROGRAMDATA", "C:/")) / ".rh_pass_set_flag"
        logger.info(f"[*] Шлях до прапорця: {flag_file}")

        if flag_file.exists():
            try:
                os.remove(flag_file)
            except Exception as e:
                logger.warning(f"Не вдалося видалити старий прапорець: {e}")

        # Запускаємо адмін-процес
        if not self.set_password_with_admin():
            logger.error("Не вдалося запустити адмін-процес.")
            pass

        # (ОНОВЛЕНО) Чекаємо на адмін-процес (до 3 хвилин)
        logger.info("Чекаю на завершення роботи адмін-процесу (до 180 сек)...")
        password_set = False
        for i in range(180):  # 3 хвилини
            if flag_file.exists():
                logger.info("✅ Адмін-процес завершив роботу.")
                try:
                    os.remove(flag_file)
                except:
                    pass
                password_set = True
                break
            time.sleep(1)

        if not password_set:
            logger.warning("⚠️ Адмін-процес не відповів (timeout). Пробую продовжити...")

        # Крок 5: Отримати ID
        logger.info("📌 Отримання ID...")
        time.sleep(1)  # Дамо AnyDesk секунду
        connection_id = self.get_connection_id()

        if not connection_id:
            logger.info("Повторна спроба отримати ID...")
            time.sleep(3)
            connection_id = self.get_connection_id()

        # Крок 6: Надіслати в Telegram
        try:
            user_name = self.config.get("user_name", "")
            self.telegram.send_anydesk_info(
                self.config.store_location_text,
                user_name,
                socket.gethostname(),
                connection_id if connection_id else "НЕ ОТРИМАНО",
                password if password_set else "(НЕ ВСТАНОВЛЕНО!)"
            )
            logger.info("✅ Телеграм сповіщено")
        except Exception as e:
            logger.error(f"❌ Телеграм помилка: {e}")

        logger.info(f"✅ Готово (ID: {connection_id})")
        return connection_id, password