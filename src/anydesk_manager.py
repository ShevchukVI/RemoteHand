import os
import subprocess
import time
import winreg
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AnyDeskManager:
    """Менеджер для AnyDesk запуску"""

    def __init__(self):
        self.anydesk_path = self.find_anydesk()
        self.anydesk_id = None

    def find_anydesk(self):
        """Знайти AnyDesk на ПК"""
        common_paths = [
            r"C:\Program Files\AnyDesk\AnyDesk.exe",
            r"C:\Program Files (x86)\AnyDesk\AnyDesk.exe",
            os.path.expanduser("~\\AppData\\Local\\AnyDesk\\AnyDesk.exe")
        ]

        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"✅ AnyDesk знайдено: {path}")
                return path

        logger.warning("⚠️ AnyDesk не знайдено")
        return None

    def download_anydesk(self):
        """Завантажити AnyDesk якщо його нема"""
        if self.anydesk_path:
            return True

        logger.info("📥 Завантаження AnyDesk...")

        try:
            import urllib.request

            download_url = "https://download.anydesk.com/AnyDesk.exe"
            save_path = os.path.expanduser("~\\Downloads\\AnyDesk.exe")

            logger.info(f"Завантажу з {download_url}...")
            urllib.request.urlretrieve(download_url, save_path)

            # Запустити встановлення
            logger.info("Запуск встановлювача...")
            subprocess.run([save_path], shell=True)

            # Знайти встановлений шлях
            time.sleep(3)
            self.anydesk_path = self.find_anydesk()

            if self.anydesk_path:
                logger.info("✅ AnyDesk успішно встановлено")
                return True
            else:
                logger.error("❌ AnyDesk не знайдено після встановлення")
                return False

        except Exception as e:
            logger.error(f"❌ Помилка завантаження: {e}")
            return False

    def get_anydesk_id(self):
        """Отримати AnyDesk ID з реєстру"""
        try:
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\AnyDesk",
                0,
                winreg.KEY_READ
            )
            anydesk_id, _ = winreg.QueryValueEx(reg_key, "uid")
            winreg.CloseKey(reg_key)

            logger.info(f"✅ AnyDesk ID: {anydesk_id}")
            return str(anydesk_id)

        except Exception as e:
            logger.error(f"❌ Помилка отримання ID: {e}")
            return None

    def set_anydesk_password(self, password):
        """Встановити пароль для AnyDesk"""
        try:
            reg_path = r"Software\AnyDesk"

            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                reg_path,
                0,
                winreg.KEY_SET_VALUE
            )

            # Встановити пароль (базовий спосіб)
            winreg.SetValueEx(reg_key, "password", 0, winreg.REG_SZ, password)
            winreg.CloseKey(reg_key)

            logger.info("✅ Пароль встановлено")
            return True

        except Exception as e:
            logger.error(f"⚠️ Не вдалося встановити пароль: {e}")
            return False

    def start(self, password=None):
        """Запустити AnyDesk з паролем"""
        # Перевірити/завантажити AnyDesk
        if not self.anydesk_path:
            logger.info("AnyDesk не знайдено, завантажую...")
            if not self.download_anydesk():
                return None, None

        logger.info("🚀 Запуск AnyDesk...")

        try:
            # Запустити AnyDesk
            subprocess.Popen([self.anydesk_path])

            # Дочекатися запуску (2-3 секунди)
            time.sleep(3)

            # Встановити пароль якщо передано
            if password:
                self.set_anydesk_password(password)

            # Отримати ID
            anydesk_id = self.get_anydesk_id()

            logger.info(f"✅ AnyDesk запущено")
            return anydesk_id, password

        except Exception as e:
            logger.error(f"❌ Помилка запуску: {e}")
            return None, None
