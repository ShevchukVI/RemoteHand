import os
import sys
import requests
import subprocess
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class UpdaterManager:
    """Менеджер для перевірки та встановлення оновлень"""

    GITHUB_REPO = "ShevchukVI/RemoteHand"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    def __init__(self):
        if getattr(sys, 'frozen', False):
            # Якщо .exe, шлях до .exe
            self.current_exe_path = Path(sys.executable)
            self.app_dir = self.current_exe_path.parent
        else:
            # Якщо .py, шлях до .exe невідомий (DEV)
            self.current_exe_path = None
            self.app_dir = Path.cwd()  # Використовуємо Path.cwd() для DEV

        self.current_version = self.get_current_version()

    def get_resource_path(self, relative_path):
        """ (НОВЕ) Отримати коректний шлях до ресурсу (для .exe та DEV) """
        try:
            # PyInstaller створює тимчасову папку _MEIPASS
            base_path = Path(sys._MEIPASS)
        except Exception:
            # В DEV-режимі
            if getattr(sys, 'frozen', False):
                base_path = Path(sys.executable).parent
            else:
                base_path = Path.cwd()
        return base_path / relative_path

    def get_current_version(self):
        """Отримати поточну версію (з обробкою кодувань)"""
        version_file = self.get_resource_path("version.txt")

        if version_file.exists():
            try:
                # Спробувати UTF-8-SIG (стандарт з BOM)
                return version_file.read_text(encoding='utf-8-sig').strip()
            except UnicodeDecodeError:
                try:
                    # Якщо не вийшло (byte 0xff), спробувати UTF-16
                    return version_file.read_text(encoding='utf-16').strip()
                except Exception:
                    pass
            except Exception:
                pass

        return "1.0.14"  # Fallback

    def get_latest_version(self):
        """Отримати найновішу версію з GitHub"""
        try:
            response = requests.get(self.GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            tag = data.get('tag_name', 'v1.0.0')
            return tag.lstrip('v')
        except Exception as e:
            logger.warning(f"Не вдалося отримати версію з GitHub: {e}")
            return None

    def compare_versions(self, current, latest):
        """Порівняти версії (використовує packaging, якщо доступно)"""
        try:
            from packaging.version import parse
            return parse(latest) > parse(current)
        except ImportError:
            try:
                current_parts = [int(x) for x in current.split('.')]
                latest_parts = [int(x) for x in latest.split('.')]
                return latest_parts > current_parts
            except:
                return False
        except Exception:
            return False

    def download_update(self, latest_version):
        """Завантажити нову версію"""
        try:
            logger.info(f"📥 Завантажую RemoteHand v{latest_version}...")
            download_url = f"https://github.com/{self.GITHUB_REPO}/releases/download/v{latest_version}/RemoteHand.exe"

            response = requests.get(download_url, timeout=60, stream=True)
            response.raise_for_status()

            new_exe_path = self.app_dir / "RemoteHand_new.exe"

            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"✅ RemoteHand v{latest_version} завантажено: {new_exe_path}")
            return new_exe_path

        except Exception as e:
            logger.error(f"❌ Помилка завантаження: {e}")
            return None

    def run_update_vbs_bat(self, new_exe_path: Path):
        """
        (ВИПРАВЛЕНО)
        Створює та запускає .bat через .vbs для 100% надійної заміни файлу.
        """
        if not self.current_exe_path:
            logger.warning("Не можу запустити оновлення в DEV режимі.")
            return

        # Використовуємо абсолютні шляхи
        bat_path = self.app_dir / "update.bat"
        vbs_path = self.app_dir / "update.vbs"
        current_exe_abs = str(self.current_exe_path.resolve())
        new_exe_abs = str(new_exe_path.resolve())
        current_exe_name = self.current_exe_path.name

        # --- Створюємо .BAT файл ---
        bat_content = f"""@ECHO OFF
TITLE Оновлення RemoteHand...
ECHO Закриваю попередню версію (TASKKILL)...
TASKKILL /F /IM "{current_exe_name}" > nul
ECHO Чекаю 5 секунд, поки процес завершиться...
ping 127.0.0.1 -n 6 > nul

ECHO Оновлюю файл...
MOVE /Y "{new_exe_abs}" "{current_exe_abs}"

ECHO Запускаю оновлену версію...
START "" "{current_exe_abs}"

ECHO Видаляю допоміжні файли...
DEL "{vbs_path.resolve()}"
(goto) 2>nul & del "%~f0"
"""
        try:
            # cp866 - кодування для .bat у Windows
            with open(bat_path, "w", encoding='cp866') as f:
                f.write(bat_content)
            logger.info(f"✅ Створено update.bat")
        except Exception as e:
            logger.error(f"❌ Помилка створення update.bat: {e}")
            return

        # --- Створюємо .VBS файл ---
        vbs_content = f"""
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /C ""{bat_path.resolve()}""", 0, False


"""
        try:
            with open(vbs_path, "w", encoding='utf-8') as f:
                f.write(vbs_content)
            logger.info(f"✅ Створено update.vbs")
        except Exception as e:
            logger.error(f"❌ Помилка створення update.vbs: {e}")
            return

        # --- Запускаємо VBScript і закриваємось ---
        try:
            logger.info(f"🔄 Запускаю update.vbs та завершую роботу...")

            # (ВИПРАВЛЕНО) os.startfile - найнадійніший спосіб "клікнути"
            os.startfile(str(vbs_path.resolve()))

            # Негайно закриваємо поточну програму
            sys.exit(0)
        except Exception as e:
            logger.error(f"❌ Помилка запуску wscript.exe: {e}")


    def check_and_update(self):
        """
Перевірити
та
встановити
оновлення
"""
        # (ВИПРАВЛЕНО) Більш надійна перевірка на DEV
        if os.getenv('REMOTEHAND_DEV_MODE') == '1' or not getattr(sys, 'frozen', False):
            logger.info("🔧 DEV режим - пропускаємо оновлення")
            return False

        logger.info("🔍 Перевірка оновлень...")

        latest_version = self.get_latest_version()
        if not latest_version:
            logger.info("⚠️ Не вдалося перевірити оновлення")
            return False

        logger.info(f"📌 Поточна версія: {self.current_version}")
        logger.info(f"📦 Остання версія: {latest_version}")

        if self.compare_versions(self.current_version, latest_version):
            logger.info(f"📦 Доступне оновлення: {latest_version}")

            new_exe = self.download_update(latest_version)

            if new_exe and new_exe.exists():
                logger.info(f"✅ Нова версія готова!")
                # (ВИПРАВЛЕНО) Використовуємо VBS->BAT метод
                self.run_update_vbs_bat(new_exe) 
                return True
            else:
                logger.error("❌ Не вдалося завантажити оновлення.")

        logger.info(f"✅ Версія актуальна: {self.current_version}")
        return False


def check_and_update():
    """
Функція
для
імпорту
в
main.py
"""
    updater = UpdaterManager()
    return updater.check_and_update()