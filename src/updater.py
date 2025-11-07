import os
import sys
import requests
import subprocess
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class UpdaterManager:
    """Менеджер для перевірки та встановлення оновлень"""

    GITHUB_REPO = "ShevchukVI/RemoteHand"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.version_file = self.app_dir / "version.txt"
        self.current_version = self.get_current_version()

    def get_current_version(self):
        """Отримати поточну версію з version.txt"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'remotehand' in line.lower() and 'ver' in line.lower():
                            version = line.split(':')[-1].strip()
                            return version
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
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            return latest_parts > current_parts
        except:
            return False

    def check_and_update(self):
        """Перевірити та встановити оновлення"""
        # Не оновлювати в DEV режимі!
        if os.getenv('REMOTEHAND_DEV_MODE') == '1':
            logger.info("🔧 DEV режим - пропускаємо оновлення")
            return False

        logger.info("Перевірка оновлень...")

        latest_version = self.get_latest_version()
        if not latest_version:
            logger.info("Не вдалося перевірити оновлення")
            return False

        if self.compare_versions(self.current_version, latest_version):
            logger.info(f"Доступне оновлення: {latest_version}")
            # Оновлення буде завантажено EXE, не у .py версії
            return True

        logger.info(f"Версія актуальна: {self.current_version}")
        return False


# Глобальна функція для використання в main.py
def check_and_update():
    """Функція для імпорту в main.py"""
    updater = UpdaterManager()
    return updater.check_and_update()
