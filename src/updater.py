import os
import sys
import requests
import subprocess
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class UpdaterManager:
    GITHUB_REPO = "ShevchukVI/RemoteHand"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.current_exe_path = Path(sys.executable)
            self.app_dir = self.current_exe_path.parent
        else:
            self.current_exe_path = None
            self.app_dir = Path.cwd()

        self.version_file = self.app_dir / "version.txt"
        self.current_version = self.get_current_version()

    def get_current_version(self):
        if self.version_file.exists():
            try:
                return self.version_file.read_text(encoding='utf-8-sig').strip()
            except UnicodeDecodeError:
                try:
                    return self.version_file.read_text(encoding='utf-16').strip()
                except Exception:
                    pass
        return "1.0.0"

    def get_latest_version(self):
        try:
            response = requests.get(self.GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            tag = data.get("tag_name", "v1.0.0")
            return tag.lstrip("v")
        except Exception as e:
            logger.warning(f"❌ Помилка отримання останньої версії з GitHub: {e}")
            return None

    def compare_versions(self, current, latest):
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
        try:
            logger.info(f"📥 Завантаження RemoteHand v{latest_version}...")

            download_url = f"https://github.com/{self.GITHUB_REPO}/releases/download/v{latest_version}/RemoteHand.exe"

            response = requests.get(download_url, timeout=60, stream=True)
            response.raise_for_status()

            temp_dir = Path(os.getenv("TEMP", self.app_dir))
            new_exe_path = temp_dir / "RemoteHand_update_temp.exe"

            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"✅ Завантажено RemoteHand v{latest_version} → {new_exe_path}")
            return new_exe_path

        except Exception as e:
            logger.error(f"❌ Помилка завантаження оновлення: {e}")
            return None

    def run_update_script(self, new_exe_path: Path):
        """Створює та запускає НАДІЙНИЙ скрипт оновлення"""
        if not self.current_exe_path:
            logger.warning("⚠️ Неможливо створити скрипт оновлення в DEV режимі.")
            return

        current_exe_abs = str(self.current_exe_path.resolve())
        new_exe_abs = str(new_exe_path.resolve())

        logger.info(f"📝 Створюю скрипт оновлення...")
        logger.info(f"   Старий файл: {current_exe_abs}")
        logger.info(f"   Новий файл: {new_exe_abs}")

        bat_content = f"""@ECHO OFF
    TITLE RemoteHand Auto Update v1.0.19
    COLOR 0A
    ECHO ====================================
    ECHO  RemoteHand Auto Update v1.0.19
    ECHO ====================================
    ECHO.
    ECHO [1/4] Closing RemoteHand...
    TASKKILL /F /IM "RemoteHand.exe" >nul 2>&1

    ECHO [2/4] Waiting for file unlock (5 sec)...
    TIMEOUT /T 5 /NOBREAK >nul

    ECHO [3/4] Replacing old version...
    MOVE /Y "{new_exe_abs}" "{current_exe_abs}"

    IF ERRORLEVEL 1 (
        ECHO ❌ Error: Failed to replace file!
        PAUSE
        EXIT /B 1
    )

    ECHO [4/4] Starting RemoteHand...
    START "" "{current_exe_abs}"

    ECHO.
    ECHO ✅ Update complete! New version: 1.0.19
    ECHO This window will close in 3 seconds...
    TIMEOUT /T 3 /NOBREAK >nul

    REM Видалити сам .bat файл після завершення
    (goto) 2>nul & del "%~f0"
    """

        bat_path = self.app_dir / "update.bat"

        try:
            with open(bat_path, 'w', encoding='cp866') as f:
                f.write(bat_content)

            logger.info(f"✅ Створено update.bat → {bat_path}")

            # Запуск .bat файлу
            subprocess.Popen(
                [str(bat_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(self.app_dir),
                shell=True
            )

            logger.info("🚀 Запущено update.bat, завершую програму через 2 сек...")

            # Завершити програму, щоб батник міг замінити EXE
            time.sleep(2)
            sys.exit(0)

        except Exception as e:
            logger.error(f"❌ Помилка створення update.bat: {e}")

    def check_and_update(self):
        if os.getenv("REMOTEHAND_DEV_MODE") == '1' or not getattr(sys, 'frozen', False):
            logger.info("🔧 DEV режим - пропуск оновлень")
            return False

        logger.info("🔄 Перевірка оновлень...")

        latest_version = self.get_latest_version()
        if not latest_version:
            logger.info("⚠️ Не вдалося отримати інформацію про останню версію")
            return False

        logger.info(f"📌 Поточна версія: {self.current_version}")
        logger.info(f"📌 Остання версія: {latest_version}")

        if self.compare_versions(self.current_version, latest_version):
            logger.info(f"🔔 Доступне оновлення: v{latest_version}")

            new_exe = self.download_update(latest_version)
            if new_exe and new_exe.exists():
                logger.info(f"✅ Оновлення завантажено! Запуск скрипту оновлення...")
                self.run_update_script(new_exe)
                return True
            else:
                logger.error("❌ Не вдалося завантажити оновлення.")
        else:
            logger.info(f"✅ У вас остання версія: v{self.current_version}")

        return False


def check_and_update():
    updater = UpdaterManager()
    return updater.check_and_update()
