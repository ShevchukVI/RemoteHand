import asyncio
import json
import logging
from telegram import Bot

logger = logging.getLogger(__name__)


class TelegramHelper:
    """Допоміжник для відправлення повідомлень в Telegram"""

    def __init__(self, config_path="bot_config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        """Завантажити конфіг"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    async def send_anydesk_code(self, anydesk_id, password):
        """Відправити AnyDesk дані в Telegram"""
        try:
            token = self.config.get("TELEGRAM_TOKEN")
            chat_id = self.config.get("CHAT_ID")

            if not token or not chat_id:
                logger.error("❌ Не встановлені TELEGRAM_TOKEN або CHAT_ID")
                return False

            bot = Bot(token=token)

            message = (
                f"🖥️ **AnyDesk сесія активована**\n\n"
                f"🆔 ID: `{anydesk_id}`\n"
                f"🔐 Пароль: `{password}`\n\n"
                f"Для підключення використовуйте ці дані."
            )

            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )

            logger.info("✅ Дані відправлені в Telegram")
            return True

        except Exception as e:
            logger.error(f"❌ Помилка відправки: {e}")
            return False

    async def send_message(self, text):
        """Відправити довільне повідомлення"""
        try:
            token = self.config.get("TELEGRAM_TOKEN")
            chat_id = self.config.get("CHAT_ID")

            if not token or not chat_id:
                return False

            bot = Bot(token=token)
            await bot.send_message(chat_id=chat_id, text=text)

            return True

        except Exception as e:
            logger.error(f"❌ Помилка: {e}")
            return False

    def send_anydesk_code_sync(self, anydesk_id, password):
        """Синхронна версія (для GUI)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.send_anydesk_code(anydesk_id, password)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"❌ Помилка: {e}")
            return False
