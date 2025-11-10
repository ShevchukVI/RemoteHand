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

            # ✅ ШУКАТИ version.txt В _MEIPASS (всередині EXE)
            version_in_meipass = Path(sys._MEIPASS) / "version.txt"
            if version_in_meipass.exists():
                self.version_file = version_in_meipass
                logger.info(f"✅ version.txt знайдено в _MEIPASS: {self.version_file}")
            else:
                # Fallback - поруч з EXE
                self.version_file = self.app_dir / "version.txt"
                logger.warning(f"⚠️ version.txt НЕ в _MEIPASS, шукаю поруч з EXE: {self.version_file}")
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
                version = re.sub(r'[^0-9.]', '', version)
                logger.info(f"📌 Версія з файлу: {version}")
                return version if version else "1.0.0"
            except Exception as e:
                logger.error(f"Помилка читання версії: {e}")

        logger.warning(f"⚠️ version.txt не знайдено за шляхом {self.version_file}, використовую 1.0.0")
        return "1.0.0"

    def get_latest_version(self):
        """Отримати останню версію з GitHub"""
        try:
            logger.info(f"🔍 Запит до GitHub API: {self.GITHUB_API_URL}")
            response = requests.get(self.GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            tag = data.get("tag_name", "v1.0.0")
            version = tag.lstrip("v")
            logger.info(f"📌 Остання версія на GitHub: {version}")
            return version
        except Exception as e:
            logger.error(f"❌ Помилка отримання останньої версії з GitHub: {e}")
            return None

    def compare_versions(self, current, latest):
        """Порівняти версії"""
        try:
            from packaging.version import parse
            result = parse(latest) > parse(current)
            logger.info(
                f"🔄 Порівняння версій: {current} vs {latest} = {'ПОТРІБНЕ ОНОВЛЕННЯ' if result else 'Версії однакові або старіші'}")
            return result
        except ImportError:
            try:
                current_parts = [int(x) for x in current.split('.')]
                latest_parts = [int(x) for x in latest.split('.')]

                while len(current_parts) < len(latest_parts):
                    current_parts.append(0)
                while len(latest_parts) < len(current_parts):
                    latest_parts.append(0)

                result = latest_parts > current_parts
                logger.info(
                    f"🔄 Порівняння версій (без packaging): {current} vs {latest} = {'ПОТРІБНЕ ОНОВЛЕННЯ' if result else 'Версії однакові або старіші'}")
                return result
            except Exception as e:
                logger.error(f"❌ Помилка порівняння версій: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Помилка порівняння версій: {e}")
            return False

    def download_update(self, latest_version):
        """Завантажити оновлення з GitHub"""
        try:
            logger.info(f"📥 Початок завантаження RemoteHand v{latest_version}...")

            download_url = f"https://github.com/{self.GITHUB_REPO}/releases/download/v{latest_version}/RemoteHand.exe"
            logger.info(f"🔗 URL завантаження: {download_url}")

            response = requests.get(download_url, timeout=60, stream=True)
            response.raise_for_status()

            new_exe_path = self.app_dir / "RemoteHand_new.exe"
            logger.info(f"💾 Збереження в: {new_exe_path}")

            with open(new_exe_path, 'wb') as f:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                last_logged_progress = 0

                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if progress - last_logged_progress >= 10:
                            logger.info(f"   Завантажено: {progress:.1f}%")
                            last_logged_progress = progress

            logger.info(f"✅ Завантажено RemoteHand v{latest_version} успішно!")
            logger.info(f"📊 Розмір файлу: {new_exe_path.stat().st_size / 1024 / 1024:.2f} MB")
            return new_exe_path

        except Exception as e:
            logger.error(f"❌ Помилка завантаження оновлення: {e}")
            return None

    def run_update_script(self, new_exe_path: Path):
        """Створює PowerShell скрипт для оновлення"""
        if not self.current_exe_path:
            logger.warning("⚠️ Неможливо створити скрипт оновлення в DEV режимі.")
            return

        current_exe_abs = str(self.current_exe_path.resolve())
        new_exe_abs = str(new_exe_path.resolve())
        log_file = self.app_dir / "logs" / "update.log"

        logger.info(f"📝 Створення PowerShell скрипту оновлення...")
        logger.info(f"   Старий файл: {current_exe_abs}")
        logger.info(f"   Новий файл: {new_exe_abs}")

        # ✅ ВИПРАВЛЕНИЙ PowerShell скрипт (всі дужки на місці!)
        ps1_content = f"""# RemoteHand Auto-Update Script
$logFile = "{log_file}"
$ErrorActionPreference = "Continue"

function Write-Log {{
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage -Encoding UTF8
}}

Write-Log "======================================"
Write-Log " RemoteHand Auto-Update STARTED"
Write-Log "======================================"
Write-Log ""

Write-Log "[1/5] Closing RemoteHand..."
Stop-Process -Name "RemoteHand" -Force -ErrorAction SilentlyContinue
Write-Log "   Process stopped"

Write-Log "[2/5] Waiting for file unlock (5 sec)..."
Start-Sleep -Seconds 5
Write-Log "   Wait complete"

Write-Log "[3/5] Backing up old version..."
$backupPath = "{current_exe_abs}.backup"
if (Test-Path "{current_exe_abs}") {{
    Copy-Item "{current_exe_abs}" $backupPath -Force
    Write-Log "   Backup created: $backupPath"
}} else {{
    Write-Log "   WARNING: Old file not found!"
}}

Write-Log "[4/5] Replacing with new version..."
try {{
    if (-not (Test-Path "{new_exe_abs}")) {{
        Write-Log "   ERROR: New file not found: {new_exe_abs}"
        throw "New file not found"
    }}

    Move-Item "{new_exe_abs}" "{current_exe_abs}" -Force
    Write-Log "   File replaced successfully!"

    if (Test-Path $backupPath) {{
        Remove-Item $backupPath -Force
        Write-Log "   Backup removed"
    }}
}} catch {{
    Write-Log "   Error replacing file: $_"

    if (Test-Path $backupPath) {{
        Write-Log "   Restoring from backup..."
        Move-Item $backupPath "{current_exe_abs}" -Force
        Write-Log "   Restored from backup"
    }}

    Write-Log "Update FAILED! Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}}

Write-Log "[5/5] Starting RemoteHand..."
Start-Process "{current_exe_abs}"
Write-Log "   RemoteHand started"

Write-Log ""
Write-Log "Update complete!"
Write-Log "This window will close in 3 seconds..."
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

            logger.info("🚀 Запущено update.ps1")
            logger.info("⏱️ Завершення програми через 2 секунди...")

            time.sleep(2)
            sys.exit(0)

        except Exception as e:
            logger.error(f"❌ Помилка створення update.ps1: {e}")

    def check_and_update(self):
        """Перевірити та встановити оновлення"""
        try:
            if os.getenv("REMOTEHAND_DEV_MODE") == '1' or not getattr(sys, 'frozen', False):
                logger.info("🔧 DEV режим - пропуск оновлень")
                return False

            logger.info("=" * 60)
            logger.info("🔄 ПЕРЕВІРКА ОНОВЛЕНЬ ЗАПУЩЕНА")
            logger.info("=" * 60)

            latest_version = self.get_latest_version()
            if not latest_version:
                logger.warning("⚠️ Не вдалося отримати інформацію про останню версію")
                return False

            logger.info(f"📌 Поточна версія: {self.current_version}")
            logger.info(f"📌 Остання версія: {latest_version}")

            if self.compare_versions(self.current_version, latest_version):
                logger.info(f"🔔 ДОСТУПНЕ ОНОВЛЕННЯ: v{latest_version}")

                new_exe = self.download_update(latest_version)
                if new_exe and new_exe.exists():
                    logger.info(f"✅ Оновлення завантажено! Запуск скрипту оновлення...")
                    self.run_update_script(new_exe)
                    return True
                else:
                    logger.error("❌ Не вдалося завантажити оновлення.")
            else:
                logger.info(f"✅ У вас остання версія: v{self.current_version}")

            logger.info("=" * 60)
            return False

        except Exception as e:
            logger.error(f"❌ КРИТИЧНА ПОМИЛКА в check_and_update: {e}", exc_info=True)
            return False


def check_and_update():
    """Функція для виклику з main.py"""
    updater = UpdaterManager()
    return updater.check_and_update()
