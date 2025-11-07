import os
import subprocess
import keyring
import json
from pathlib import Path


class RDPManager:
    """Менеджер для RDP підключень з автоматичним логіном"""

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

    def save_config(self, config):
        """Зберегти конфіг"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def save_credentials(self, host, username, password):
        """Зберегти RDP дані в Windows Credential Manager"""
        try:
            keyring.set_password(f"RDP_{host}", username, password)
            print(f"✅ Дані збережені для {host}")
            return True
        except Exception as e:
            print(f"❌ Помилка збереження: {e}")
            return False

    def get_credentials(self, host, username):
        """Отримати пароль з Credential Manager"""
        try:
            password = keyring.get_password(f"RDP_{host}", username)
            return password
        except:
            return None

    def create_rdp_file(self, host, port, username, password, filename="temp.rdp"):
        """Створити .RDP файл з CredSSP для автоматичного входу"""
        try:
            # Кодування пароля для .RDP файлу
            import struct

            # RDP формат пароля (простий XOR кодування)
            encrypted_password = self._encrypt_rdp_password(password)

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

            with open(filename, "w") as f:
                f.write(rdp_content)

            return True
        except Exception as e:
            print(f"❌ Помилка створення .RDP файлу: {e}")
            return False

    def _encrypt_rdp_password(self, password):
        """Простое шифрування пароля для .RDP"""
        # RDP використовує простий алгоритм
        encrypted = ""
        for char in password:
            encrypted += format(ord(char) ^ 0xAA, '02x')
        return encrypted

    def connect_rdp_auto(self, host, port, username):
        """Підключитися до RDP з автоматичним логіном"""
        # Отримати пароль з Credential Manager
        password = self.get_credentials(host, username)

        if not password:
            print("❌ Пароль не знайдено. Спочатку збережіть дані.")
            return False

        # Створити та запустити .RDP файл
        rdp_file = f"{host}_{username}_auto.rdp"

        if self.create_rdp_file(host, port, username, password, rdp_file):
            try:
                subprocess.Popen(f"mstsc {rdp_file}")
                print(f"✅ Підключення до {host} з автоматичним логіном")
                return True
            except Exception as e:
                print(f"❌ Помилка запуску: {e}")
                return False

        return False

    def connect_rdp_manual(self, host, port):
        """Запустити звичайне RDP підключення"""
        subprocess.Popen(f"mstsc /v:{host}:{port}")
