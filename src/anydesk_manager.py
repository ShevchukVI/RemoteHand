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
        """Встановити пароль через окремий скрипт з адмін правами"""
        if not self.anydesk_path:
            logger.error("Шлях невідомий")
            return False

        try:
            logger.info(f"🔐 Запускаю встановлення пароля з адмін правами...")

            # Визначити шлях до скрипту
            if getattr(sys, 'frozen', False):
                # Якщо EXE - скрипт поруч
                script_path = os.path.join(os.path.dirname(sys.executable), "src", "set_anydesk_password.py")
            else:
                # Якщо DEV
                script_path = os.path.join(os.path.dirname(__file__), "set_anydesk_password.py")

            if not os.path.exists(script_path):
                logger.error(f"Скрипт не знайдено: {script_path}")
                return False

            # Передати пароль як змінну середовища
            env = os.environ.copy()
            env["ANYDESK_PASSWORD"] = UNATTENDED_PASSWORD

            # Запустити скрипт з адмін правами
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                f'"{script_path}" "{self.anydesk_path}"',
                None,
                1  # SW_SHOW - показати вікно
            )

            logger.info(f"✅ Запрос адмін прав надіслано користувачу")
            time.sleep(3)
            return True

        except Exception as e:
            logger.error(f"❌ Помилка: {e}")
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
        """Запустити AnyDesk"""
        password = UNATTENDED_PASSWORD

        # Крок 1: Якщо вже запущено
        if self.check_if_running():
            logger.info("AnyDesk вже запущено")
            connection_id = self.get_connection_id()
            if connection_id:
                try:
                    # ⚠️ ДОДАТИ ПІБ
                    user_name = self.config.get("user_name", "")

                    self.telegram.send_anydesk_info(
                        self.config.store_location_text,
                        user_name,  # ⬅️ ПІБ
                        socket.gethostname(),  # ПК
                        connection_id,
                        password
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

        # Крок 4: ВСТАНОВИТИ ПАРОЛЬ З АДМІН ПРАВАМИ
        logger.info("🔐 Встановлення пароля...")
        time.sleep(2)
        self.set_password_with_admin()

        # Крок 5: Отримати ID
        logger.info("📌 Отримання ID...")
        time.sleep(2)
        connection_id = self.get_connection_id()

        if not connection_id:
            time.sleep(3)
            connection_id = self.get_connection_id()

        # Крок 6: Надіслати в Telegram з ПІБ
        try:
            # ⚠️ ДОДАТИ ПІБ
            user_name = self.config.get("user_name", "")

            self.telegram.send_anydesk_info(
                self.config.store_location_text,
                user_name,  # ⬅️ ПІБ
                socket.gethostname(),  # ПК
                connection_id if connection_id else "не отримано",
                password
            )
            logger.info("✅ Телеграм сповіщено")
        except Exception as e:
            logger.error(f"❌ Телеграм помилка: {e}")

        logger.info(f"✅ Готово (ID: {connection_id})")
        return connection_id, password
