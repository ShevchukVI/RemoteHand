import requests
import logging
import time
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class TelegramAPI:
    """Розширена Telegram API для звітування"""

    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

        # ⚠️ ПЕРЕВІРА ТОКЕНІВ
        if not token:
            logger.error("❌ Telegram токен не встановлено!")
            self.api_url = None
        elif not chat_id:
            logger.error("❌ Telegram chat_id не встановлено!")
            self.api_url = None
        else:
            self.api_url = f"https://api.telegram.org/bot{token}"
            logger.info(f"✅ Telegram налаштовано (токен: {token[:20]}...)")

    def send_message(self, text, parse_mode="HTML"):
        """Відправити текстове повідомлення"""
        if not self.api_url:
            logger.error("❌ Telegram не налаштовано")
            return False

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("✅ Повідомлення надіслано в Telegram")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка відправки Telegram: {e}")
            return False

    def send_file(self, file_path, caption="", file_type="document"):
        """Відправити файл (document або photo)"""
        if not self.api_url:
            logger.error("❌ Telegram не налаштовано")
            return False

        try:
            with open(file_path, 'rb') as f:
                files = {file_type: f}
                payload = {
                    "chat_id": self.chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                endpoint = "sendDocument" if file_type == "document" else "sendPhoto"
                response = requests.post(
                    f"{self.api_url}/{endpoint}",
                    files=files,
                    data=payload,
                    timeout=30
                )
                response.raise_for_status()
            logger.info(f"✅ Файл надіслано в Telegram")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка відправки файлу: {e}")
            return False

    def send_network_report(self, store_location, pc_name, test_results):
        """Відправити звіт про стан мережі"""
        report = (
            f"<b>📊 Звіт про стан мережі</b>\n\n"
            f"<b>Магазин/Локація:</b> {store_location}\n"
            f"<b>ПК:</b> <code>{pc_name}</code>\n"
            f"<b>Час:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"<b>Результати:</b>\n"
            f"{test_results}"
        )
        return self.send_message(report)

    def send_anydesk_info(self, store_location, user_name, pc_name, anydesk_id, password):
        """
        (ОНОВЛЕНО)
        Відправити AnyDesk інформацію (покращене форматування)
        """
        # Додати ПІБ якщо є
        user_info = f"<b>👤 Користувач:</b> {user_name}" if user_name else ""

        message = (
            f"<b>🌐 Запит на AnyDesk</b>\n\n"
            f"<b>📍 Магазин:</b> {store_location}\n"
            f"<b>💻 Комп'ютер:</b> <code>{pc_name}</code>\n"
            f"{user_info}\n\n"
            f"<b>--- Дані для входу ---</b>\n"
            f"<b>🆔 ID:</b> <code>{anydesk_id}</code>\n"
            f"<b>🔐 Пароль:</b> <code>{password}</code>"
        )
        return self.send_message(message)

    def send_rdp_info(self, store_location, pc_name):
        """Відправити сповіщення про RDP підключення"""
        message = (
            f"<b>🖥️ RDP Підключення</b>\n\n"
            f"<b>Магазин/Локація:</b> {store_location}\n"
            f"<b>ПК:</b> <code>{pc_name}</code>\n"
            f"<b>Час:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"✅ Користувач підключився до 1С"
        )
        return self.send_message(message)

    def send_error_report(self, store_location, pc_name, error_text):
        """Відправити звіт про помилку"""
        message = (
            f"<b>❌ Помилка</b>\n\n"
            f"<b>Магазин/Локація:</b> {store_location}\n"
            f"<b>ПК:</b> <code>{pc_name}</code>\n"
            f"<b>Час:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"<b>Деталі:</b>\n<code>{error_text}</code>"
        )
        return self.send_message(message)