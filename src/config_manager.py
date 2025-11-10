import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Менеджер конфігурації"""

    def __init__(self):
        self.config_dir = Path.home() / ".remotehand"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"

        self.config = self.load()

    def load(self):
        """Завантажити конфіг"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save(self):
        """Зберегти конфіг в JSON файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Помилка збереження конфігу: {e}")

    def set(self, key, value):
        """Встановити значення"""
        self.config[key] = value
        self.save()

    def get(self, key, default=""):
        """Отримати значення"""
        return self.config.get(key, default)

    def is_first_run(self):
        """Перевірити чи перший запуск"""
        store = self.config.get('store', '')
        location = self.config.get('location', '')
        return not store or not location

    @property
    def store_location_text(self):
        """Отримати текст магазину/локації"""
        store = self.config.get('store', 'Невідомо')
        location = self.config.get('location', 'Невідомо')
        return f"{store} / {location}"
