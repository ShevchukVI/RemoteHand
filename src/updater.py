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
            self.current_exe_path = Path(sys.executable)
            self.app_dir = self.current_exe_path.parent
        else:
            self.current_exe_path = None
            self.app_dir = Path(__file__).parent.parent

        self.version_file = self.app_dir / "version.txt"
        self.current_version = self.get_current_version()

    def get_current_version(self):
        """Отримати поточну версію"""
        if self.version_file.exists():
            try:
                # Спробувати UTF-8-SIG (стандарт з BOM)
                return self.version_file.read_text(encoding='utf-8-sig').strip()
            except UnicodeDecodeError:
                try:
                    # Якщо не вийшло (byte 0xff), спробувати UTF-16
                    return self.version_file.read_text(encoding='utf-16').strip()
                except Exception:
                    pass  # Перейдемо до fallback
            except Exception:
                pass  # Перейдемо до fallback

        return "1.0.0"  # Fallback

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
        """Порівняти версії"""
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

    def run_update_batch(self, new_exe_path: Path):
        """
        (ОНОВЛЕНО)
        Створює та запускає .bat файл, який примусово
        вбиває старий процес перед заміною.
        """
        if not self.current_exe_path:
            logger.warning("Не можу запустити .bat в DEV режимі.")
            return

        bat_path = self.app_dir / "update.bat"
        current_exe_name = self.current_exe_path.name
        new_exe_name = new_exe_path.name

        # (НОВА ЛОГІКА .BAT)
        # TASKKILL - Примусово вбиває заблокований процес
        # TIMEOUT /T 5 - Надійне очікування 5 секунд
        # MOVE /Y - Атомна заміна файлу
        # (goto) 2>nul & del "%~f0" - Надійний трюк для самовидалення
        bat_content = f"""@ECHO OFF
TITLE Оновлення RemoteHand...
ECHO Закриваю попередню версію (TASKKILL)...
TASKKILL /F /IM "{current_exe_name}" > nul
ECHO Чекаю 5 секунд, поки процес завершиться...
TIMEOUT /T 5 /NOBREAK > nul

ECHO Оновлюю файл...
MOVE /Y "{new_exe_name}" "{current_exe_name}"

ECHO Запускаю оновлену версію...
START "" "{current_exe_name}"

REM Самовидалення
(goto) 2>nul & del "%~f0"
"""
        try:
            with open(bat_path, "w", encoding='cp866') as f:
                f.write(bat_content)

            logger.info(f"✅ Створено update.bat")

            # Запускаємо .bat і від'єднуємо його від нашого процесу
            subprocess.Popen(
                [str(bat_path)],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
                shell=True
            )
            logger.info(f"🔄 Запущено update.bat. Завершую роботу...")

            # Негайно закриваємо поточну програму
            sys.exit(0)

        except Exception as e:
            logger.error(f"❌ Помилка створення/запуску update.bat: {e}")

    def check_and_update(self):
        """Перевірити та встановити оновлення"""
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
                self.run_update_batch(new_exe)
                return True
            else:
                logger.error("❌ Не вдалося завантажити оновлення.")

        logger.info(f"✅ Версія актуальна: {self.current_version}")
        return False


def check_and_update():
    """Функція для імпорту в main.py"""
    updater = UpdaterManager()
    return updater.check_and_update()