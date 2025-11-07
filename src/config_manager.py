import os
import json
from pathlib import Path


class ConfigManager:
    """Менеджер для зберігання конфігурації в %APPDATA%"""

    def __init__(self):
        self.app_name = "RemoteHand"
        self.config_dir = Path(os.getenv('APPDATA')) / self.app_name
        self.config_file = self.config_dir / "settings.json"
        self.ensure_config_dir()
        self.load_or_create_config()

    def ensure_config_dir(self):
        """Створити папку якщо її немає"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_or_create_config(self):
        """Завантажити конфіг або створити новий"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # Конфіг за замовчуванням
            self.config = {
                "store": None,
                "location": None,
                "rdp_password": None,
                "telegram_token": "7803515020:AAG3pEfxtXWB5MaVtH2VSFxzNMYoaCnOQxg",
                "telegram_chat_id": "527405868"
            }
            self.save_config()

    def save_config(self):
        """Зберегти конфіг"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get(self, key, default=None):
        """Отримати значення з конфігу"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Встановити значення в конфігу"""
        self.config[key] = value
        self.save_config()

    def is_first_run(self):
        """Перевірити, це перший запуск"""
        return self.config.get("store") is None or self.config.get("location") is None

    @property
    def store_location_text(self):
        """Текст для відображення магазину та локації"""
        store = self.get("store", "?")
        location = self.get("location", "?")
        return f"{store} - {location}"
