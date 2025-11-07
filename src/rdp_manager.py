import os
import subprocess
import time
import winreg
import logging
import keyring
from pathlib import Path

logger = logging.getLogger(__name__)


class RDPManager:
    """Менеджер для RDP підключень з автоматичним логіном"""

    def __init__(self, config_manager, telegram_api):
        self.config = config_manager
        self.telegram = telegram_api

    def save_credentials(self, host, username, password):
        """Зберегти RDP дані в Windows Credential Manager"""
        try:
            keyring.set_password(f"RDP_{host}", username, password)
            self.config.set("rdp_password", password)
            logger.info(f"✅ Дані збережені для {host}")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка збереження: {e}")
            return False

    def get_credentials(self, host, username):
        """Отримати пароль з Credential Manager"""
        try:
            password = keyring.get_password(f"RDP_{host}", username)
            return password
        except:
            return None

    def connect_rdp(self, host, port, username, password=None):
        """Підключитися до RDP"""
        try:
            # Кодування пароля для .RDP файлу
            encrypted_password = self._encrypt_rdp_password(password) if password else ""

            rdp_content = f"""screen mode id:i:2
use multimon:i:0
desktopwidth:i:1920
desktopheight:i:1080
session bpp:i:32
connection type:i:7
disable wallpaper:i:0
allow font smoothing:i:1
allow desktop composition:i:1
disable full window drag:i:0
disable menu anims:i:0
disable themes:i:0
disable cursor setting:i:0
bitmapcachepersistenable:i:1
full address:s:{host}:{port}
audiomode:i:0
redirectprinters:i:0
redirectcomports:i:0
redirectsmartcards:i:0
redirectclipboard:i:1
redirectposdevices:i:0
autoreconnection enabled:i:1
authentication level:i:0
prompt for credentials on client:i:0
negotiate security layer:i:1
enablecredsspsupport:i:1
username:s:{username}
password 51:b:{encrypted_password}
"""

            rdp_file = f"{host}_{username}_session.rdp"
            with open(rdp_file, "w") as f:
                f.write(rdp_content)

            subprocess.Popen(f"mstsc {rdp_file}")
            logger.info(f"✅ RDP підключення запущено")

            # Відправити в Telegram
#            self.telegram.send_rdp_info(
#                self.config.store_location_text,
#                os.environ.get('COMPUTERNAME', 'Unknown')
#            )

            return True
        except Exception as e:
            logger.error(f"❌ Помилка підключення: {e}")
            return False

    def _encrypt_rdp_password(self, password):
        """Простое шифрування пароля для .RDP"""
        encrypted = ""
        for char in password:
            encrypted += format(ord(char) ^ 0xAA, '02x')
        return encrypted
