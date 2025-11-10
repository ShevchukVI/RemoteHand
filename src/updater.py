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
        # (ОНОВЛЕНО) Визначаємо шляхи для .exe
        if getattr(sys, 'frozen', False):
            # Режим EXE
            self.current_exe_path = Path(sys.executable)
            self.app_dir = self.current_exe_path.parent
        else:
            # Режим DEV
            self.current_exe_path = None
            self.app_dir = Path(__file__).parent.parent

        self.version_file = self.app_dir / "version.txt"
        self.current_version = self.get_current_version()

    def get_current_version(self):
        """Отримати поточну версію"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except:
                pass
        return "1.0.0"

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
            # Fallback для простого порівняння, якщо packaging не встановлено
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

            # (ОНОВЛЕНО) Зберігаємо як _new.exe
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
        Створює та запускає .bat файл для заміни .exe
        """
        if not self.current_exe_path:
            logger.warning("Не можу запустити .bat в DEV режимі.")
            return

        bat_path = self.app_dir / "update.bat"
        current_exe_name = self.current_exe_path.name
        new_exe_name = new_exe_path.name

        # (ОНОВЛЕНА ЛОГІКА .BAT)
        # TIMEOUT /T 5 - Збільшено час очікування до 5 сек
        # MOVE /Y - Надійно замінює старий файл новим
        # (GOTO) 2>NUL & DEL "%~f0" - Трюк для самовидалення .bat файлу
        bat_content = f"""@ECHO OFF
TITLE Оновлення RemoteHand...
ECHO Чекаю, поки програма закриється...
TIMEOUT /T 5 /NOBREAK
ECHO Оновлюю файл...
MOVE /Y "{new_exe_name}" "{current_exe_name}"
ECHO Запускаю оновлену версію...
START "" "{current_exe_name}"
ECHO Видаляю тимчасові файли...
(GOTO) 2>NUL & DEL "%~f0"
"""
        try:
            with open(bat_path, "w", encoding='cp866') as f:
                f.write(bat_content)

            logger.info(f"✅ Створено update.bat")

            # (ОНОВЛЕНО) Додано shell=True для надійнішого запуску .bat
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
        # НЕ оновлювати в DEV режимі!
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

            # Завантажити нову версію
            new_exe = self.download_update(latest_version)

            if new_exe and new_exe.exists():
                logger.info(f"✅ Нова версія готова!")
                # (ОНОВЛЕНО) Запускаємо .bat замість прямого запуску
                self.run_update_batch(new_exe)
                return True  # Хоча програма вже вийде
            else:
                logger.error("❌ Не вдалося завантажити оновлення.")

        logger.info(f"✅ Версія актуальна: {self.current_version}")
        return False


def check_and_update():
    """Функція для імпорту в main.py"""
    updater = UpdaterManager()
    return updater.check_and_update()