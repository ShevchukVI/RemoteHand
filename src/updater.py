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
        """Отримати поточну версію з файлу"""
        if self.version_file.exists():
            try:
                import re
                version = self.version_file.read_text(encoding='utf-8-sig').strip()
                # Залишити тільки цифри та крапки
                version = re.sub(r'[^0-9.]', '', version)
                return version if version else "1.0.0"
            except Exception as e:
                logger.error(f"Помилка читання версії: {e}")
        return "1.0.0"

    def get_latest_version(self):
        """Отримати останню версію з GitHub"""
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
        """Завантажити оновлення з GitHub"""
        try:
            logger.info(f"📥 Завантаження RemoteHand v{latest_version}...")

            download_url = f"https://github.com/{self.GITHUB_REPO}/releases/download/v{latest_version}/RemoteHand.exe"

            response = requests.get(download_url, timeout=60, stream=True)
            response.raise_for_status()

            # Завантажити в ту ж папку як RemoteHand_new.exe
            new_exe_path = self.app_dir / "RemoteHand_new.exe"

            with open(new_exe_path, 'wb') as f:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"   Завантажено: {progress:.1f}%")

            logger.info(f"✅ Завантажено RemoteHand v{latest_version} → {new_exe_path}")
            return new_exe_path

        except Exception as e:
            logger.error(f"❌ Помилка завантаження оновлення: {e}")
            return None

    def run_update_script(self, new_exe_path: Path):
        """
        Створює PowerShell скрипт для оновлення (надійніший за .bat)
        """
        if not self.current_exe_path:
            logger.warning("⚠️ Неможливо створити скрипт оновлення в DEV режимі.")
            return

        current_exe_abs = str(self.current_exe_path.resolve())
        new_exe_abs = str(new_exe_path.resolve())

        # PowerShell скрипт (більш надійний!)
        ps1_content = f"""# RemoteHand Auto-Update Script
Write-Host "=====================================" -ForegroundColor Green
Write-Host " RemoteHand Auto-Update" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

Write-Host "[1/5] Closing RemoteHand..." -ForegroundColor Yellow
Stop-Process -Name "RemoteHand" -Force -ErrorAction SilentlyContinue

Write-Host "[2/5] Waiting for file unlock (5 sec)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "[3/5] Backing up old version..." -ForegroundColor Yellow
$backupPath = "{current_exe_abs}.backup"
if (Test-Path "{current_exe_abs}") {{
    Copy-Item "{current_exe_abs}" $backupPath -Force
}}

Write-Host "[4/5] Replacing with new version..." -ForegroundColor Yellow
try {{
    Move-Item "{new_exe_abs}" "{current_exe_abs}" -Force
    Write-Host "   ✓ File replaced successfully!" -ForegroundColor Green

    # Видалити backup якщо все ОК
    if (Test-Path $backupPath) {{
        Remove-Item $backupPath -Force
    }}
}} catch {{
    Write-Host "   ✗ Error replacing file: $_" -ForegroundColor Red

    # Відновити з backup
    if (Test-Path $backupPath) {{
        Write-Host "   Restoring from backup..." -ForegroundColor Yellow
        Move-Item $backupPath "{current_exe_abs}" -Force
    }}

    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}}

Write-Host "[5/5] Starting RemoteHand..." -ForegroundColor Yellow
Start-Process "{current_exe_abs}"

Write-Host ""
Write-Host "✓ Update complete!" -ForegroundColor Green
Write-Host "This window will close in 3 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Видалити сам скрипт
Remove-Item $MyInvocation.MyCommand.Path -Force
"""

        ps1_path = self.app_dir / "update.ps1"

        try:
            with open(ps1_path, 'w', encoding='utf-8') as f:
                f.write(ps1_content)

            logger.info(f"✅ Створено update.ps1 → {ps1_path}")

            # Запуск PowerShell скрипту
            subprocess.Popen(
                [
                    "powershell.exe",
                    "-ExecutionPolicy", "Bypass",
                    "-WindowStyle", "Normal",
                    "-File", str(ps1_path)
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(self.app_dir)
            )

            logger.info("🚀 Запущено update.ps1, завершую програму через 2 сек...")

            # Завершити програму
            time.sleep(2)
            sys.exit(0)

        except Exception as e:
            logger.error(f"❌ Помилка створення update.ps1: {e}")

    def check_and_update(self):
        """Перевірити та встановити оновлення"""
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
    """Функція для виклику з main.py"""
    updater = UpdaterManager()
    return updater.check_and_update()
