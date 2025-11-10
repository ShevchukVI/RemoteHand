import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
import threading
import ctypes
import subprocess
import time

# ✅ НАЛАШТУВАННЯ ЛОГУВАННЯ В ФАЙЛ (НА ПОЧАТКУ!)
if getattr(sys, 'frozen', False):
    # EXE режим - логи поруч з exe
    log_dir = Path(sys.executable).parent / "logs"
else:
    # DEV режим
    log_dir = Path(__file__).parent.parent / "logs"

log_dir.mkdir(exist_ok=True)

# Створити лог файл з датою та часом
log_file = log_dir / f"RemoteHand_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Налаштувати логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"📝 Лог файл створено: {log_file}")
logger.info(f"🚀 Запуск RemoteHand...")

# Видалити старі логи (старше 7 днів)
try:
    current_time = time.time()
    for old_log in log_dir.glob("RemoteHand_*.log"):
        if current_time - old_log.stat().st_mtime > 7 * 24 * 3600:
            old_log.unlink()
            logger.info(f"🗑️ Видалено старий лог: {old_log.name}")
except Exception as e:
    logger.warning(f"⚠️ Не вдалося видалити старі логи: {e}")

# Завантажити .env файл
from dotenv import load_dotenv


def get_resource_path(relative_path):
    """Отримати коректний шлях до ресурсу (для .exe та DEV)"""
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path.cwd()
    return base_path / relative_path


# ============ ПЕРЕВІРКА DEV РЕЖИМУ ============
DEV_MODE = os.getenv('REMOTEHAND_DEV_MODE') == '1'
logger.info(f"{'🔧 DEV РЕЖИМ' if DEV_MODE else '✅ PRODUCTION РЕЖИМ'}")

# Завантажуємо .env
if DEV_MODE:
    env_path = get_resource_path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"🔧 DEV: Завантажено .env файл з {env_path}")
    else:
        logger.warning(f"⚠️ DEV: .env файл не знайдено за шляхом {env_path}")
else:
    # PRODUCTION - .env вбудований в EXE
    env_path = get_resource_path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"✅ PROD: Завантажено .env з {env_path}")

# ============ ОНОВЛЕННЯ (ТІЛЬКИ В PROD) ============
if not DEV_MODE:
    try:
        from updater import check_and_update

        check_and_update()
    except Exception as e:
        logger.warning(f"Помилка перевірки оновлень: {e}")

# ============ ІМПОРТИ ============
from utils import close_all_rdp_sessions, test_connection
from config import RDP_HOST, RDP_PORT, PING_HOST, APP_NAME, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from config_manager import ConfigManager
from telegram_api import TelegramAPI
from setup_wizard import SetupWizard
from network_test import NetworkTest

try:
    from rdp_manager import RDPManager

    rdp_manager_available = True
except ImportError as e:
    rdp_manager_available = False
    logger.warning(f"rdp_manager не доступна: {e}")

try:
    from anydesk_manager import AnyDeskManager

    anydesk_available = True
except ImportError as e:
    anydesk_available = False
    logger.warning(f"anydesk_manager не доступна: {e}")

# ============ iOS СТИЛЬ ============
IOS_BG_COLOR = "#f2f2f7"
IOS_CARD_COLOR = "#ffffff"
IOS_TEXT_COLOR = "#000000"
IOS_SUBTEXT_COLOR = "#8A8A8E"
IOS_CARD_BORDER = "#E0E0E0"
IOS_CARD_RADIUS = 15
IOS_BUTTON_RADIUS = 12


class RemoteHandApp(ctk.CTk):

    def get_resource_path(self, relative_path):
        """Отримати коректний шлях до ресурсу"""
        try:
            base_path = Path(sys._MEIPASS)
        except Exception:
            if getattr(sys, 'frozen', False):
                base_path = Path(sys.executable).parent
            else:
                base_path = Path.cwd()
        return base_path / relative_path

    def __init__(self):
        super().__init__()

        # Налаштування вікна
        self.title(APP_NAME)
        self.geometry("520x800")
        self.resizable(True, True)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=IOS_BG_COLOR)

        # Встановлення іконки
        try:
            icon_path = self.get_resource_path("assets/icon.ico")
            if icon_path.exists():
                self.iconbitmap(icon_path)
                logger.info(f"✅ Іконку завантажено з: {icon_path}")
            else:
                logger.warning(f"⚠️ Іконку не знайдено: {icon_path}")
        except Exception as e:
            logger.error(f"❌ Помилка встановлення іконки: {e}")

        # Ініціалізація менеджерів
        self.config = ConfigManager()

        logger.info(f"Telegram token: {'✅ встановлено' if TELEGRAM_TOKEN else '❌ НЕ встановлено'}")
        logger.info(f"Telegram chat_id: {'✅ встановлено' if TELEGRAM_CHAT_ID else '❌ НЕ встановлено'}")

        self.telegram = TelegramAPI(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

        if rdp_manager_available:
            self.rdp_manager = RDPManager(self.config, self.telegram)
        else:
            self.rdp_manager = None

        if anydesk_available:
            self.anydesk_manager = AnyDeskManager(self.config, self.telegram)
        else:
            self.anydesk_manager = None

        self.network_test = NetworkTest(self.config, self.telegram)

        self.setup_ui()

        if self.config.is_first_run():
            self.show_setup_wizard()

    def get_app_version(self):
        """Отримати версію програми"""
        try:
            import re

            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(__file__).parent.parent

            version_file = base_path / "version.txt"

            if version_file.exists():
                version = version_file.read_text(encoding='utf-8-sig').strip()
                version = re.sub(r'[^0-9.]', '', version)
                logger.info(f"📌 Версія програми: {version}")
                return version if version else "1.0.0"
        except Exception as e:
            logger.error(f"Помилка читання версії: {e}")

        return "1.0.0"

    def show_setup_wizard(self):
        """Показати вікно налаштування"""

        def on_setup_complete(result):
            self.config.set("store", result["store"])
            self.config.set("location", result["location"])
            if result.get("user_name"):
                self.config.set("user_name", result["user_name"])
            self.refresh_ui()

        wizard = SetupWizard(self, on_setup_complete)
        self.wait_window(wizard)

    def refresh_ui(self):
        """Оновити UI"""
        user_info = self.config.store_location_text
        user_name = self.config.get("user_name", "")
        if user_name:
            user_info += f" | 👤 {user_name}"
        self.info_label.configure(text=f"📍 {user_info}")

    def setup_ui(self):
        """Створення UI в стилі iOS"""

        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="RemoteHand",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=IOS_TEXT_COLOR
        )
        title_label.pack(pady=(10, 0), padx=20, anchor="w")

        # Інформація
        user_info = self.config.store_location_text
        user_name = self.config.get("user_name", "")
        if user_name:
            user_info += f" | 👤 {user_name}"

        self.info_label = ctk.CTkLabel(
            self,
            text=f"📍 {user_info}",
            font=ctk.CTkFont(size=12),
            text_color=IOS_SUBTEXT_COLOR
        )
        self.info_label.pack(pady=(0, 15), padx=20, anchor="w")

        # ==================== RDP КАРТКА ====================
        rdp_frame = ctk.CTkFrame(
            self,
            fg_color=IOS_CARD_COLOR,
            corner_radius=IOS_CARD_RADIUS,
            border_width=1,
            border_color=IOS_CARD_BORDER
        )
        rdp_frame.pack(pady=8, padx=20, fill="x")

        ctk.CTkLabel(
            rdp_frame,
            text="Підключення до 1С",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=IOS_TEXT_COLOR
        ).pack(anchor="w", pady=(10, 10), padx=15)

        rdp_btn = ctk.CTkButton(
            rdp_frame,
            text="🖥️ Відкрити 1С (RDP)",
            command=self.open_rdp,
            height=50,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=IOS_BUTTON_RADIUS,
            fg_color="#007AFF",
            hover_color="#0051D5"
        )
        rdp_btn.pack(fill="x", pady=(0, 15), padx=15)

        # ==================== ANYDESK КАРТКА ====================
        if anydesk_available:
            anydesk_frame = ctk.CTkFrame(
                self,
                fg_color=IOS_CARD_COLOR,
                corner_radius=IOS_CARD_RADIUS,
                border_width=1,
                border_color=IOS_CARD_BORDER
            )
            anydesk_frame.pack(pady=8, padx=20, fill="x")

            ctk.CTkLabel(
                anydesk_frame,
                text="Віддалений доступ",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=IOS_TEXT_COLOR
            ).pack(anchor="w", pady=(10, 10), padx=15)

            anydesk_btn = ctk.CTkButton(
                anydesk_frame,
                text="🚀 Запустити AnyDesk",
                command=self.start_anydesk,
                height=50,
                font=ctk.CTkFont(size=12, weight="bold"),
                corner_radius=IOS_BUTTON_RADIUS,
                fg_color="#FF6B35",
                hover_color="#CC5529"
            )
            anydesk_btn.pack(fill="x", pady=(0, 15), padx=15)

        # ==================== ДІАГНОСТИКА КАРТКА ====================
        test_frame = ctk.CTkFrame(
            self,
            fg_color=IOS_CARD_COLOR,
            corner_radius=IOS_CARD_RADIUS,
            border_width=1,
            border_color=IOS_CARD_BORDER
        )
        test_frame.pack(pady=8, padx=20, fill="x")

        ctk.CTkLabel(
            test_frame,
            text="Діагностика та Управління",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=IOS_TEXT_COLOR
        ).pack(anchor="w", pady=(10, 10), padx=15)

        test_btn = ctk.CTkButton(
            test_frame,
            text="📡 Тест з'єднання",
            command=self.run_network_test,
            height=50,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=IOS_BUTTON_RADIUS,
            fg_color="#34C759",
            hover_color="#248A3D"
        )
        test_btn.pack(fill="x", pady=(0, 10), padx=15)

        # Розділювач
        separator = ctk.CTkFrame(test_frame, height=1, fg_color=IOS_CARD_BORDER)
        separator.pack(fill="x", padx=15, pady=5)

        close_sessions_btn = ctk.CTkButton(
            test_frame,
            text="❌ Закрити всі RDP сесії",
            command=self.close_sessions_confirm,
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=IOS_BUTTON_RADIUS,
            fg_color="#FF3B30",
            hover_color="#D70015"
        )
        close_sessions_btn.pack(fill="x", pady=(10, 15), padx=15)

        # ==================== НАЛАШТУВАННЯ КАРТКА ====================
        settings_frame = ctk.CTkFrame(
            self,
            fg_color=IOS_CARD_COLOR,
            corner_radius=IOS_CARD_RADIUS,
            border_width=1,
            border_color=IOS_CARD_BORDER
        )
        settings_frame.pack(pady=8, padx=20, fill="x")

        settings_btn = ctk.CTkButton(
            settings_frame,
            text="⚙️ Змінити магазин/локацію/ПІБ",
            command=self.show_setup_wizard,
            height=40,
            font=ctk.CTkFont(size=11),
            corner_radius=IOS_BUTTON_RADIUS,
            fg_color="#999999",
            hover_color="#666666"
        )
        settings_btn.pack(fill="x", pady=15, padx=15)

        # ==================== СТАТУС ====================
        self.status_label = ctk.CTkLabel(
            self,
            text="✅ Готово до роботи",
            font=ctk.CTkFont(size=10),
            text_color=IOS_SUBTEXT_COLOR
        )
        self.status_label.pack(pady=8)

        # ==================== ВЕРСІЯ ====================
        version_frame = ctk.CTkFrame(self, fg_color="transparent")
        version_frame.pack(anchor="s", pady=(0, 8))

        version_label = ctk.CTkLabel(
            version_frame,
            text=f"v{self.get_app_version()}",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=IOS_SUBTEXT_COLOR
        )
        version_label.pack(side="left", padx=5)

        self.update_status_label = ctk.CTkLabel(
            version_frame,
            text="✅",
            font=ctk.CTkFont(size=10),
            text_color="green"
        )
        self.update_status_label.pack(side="left", padx=5)

    def open_rdp(self):
        """Відкрити RDP"""
        if not self.rdp_manager:
            messagebox.showerror("Помилка", "RDP менеджер не доступен")
            return

        saved_password = self.rdp_manager.get_credentials(RDP_HOST, "admin")

        if saved_password:
            self.set_status("⏳ Підключення...", "processing")

            def connect():
                try:
                    if self.rdp_manager.connect_rdp(RDP_HOST, RDP_PORT, "admin", saved_password):
                        self.set_status("✅ Підключено", "success")
                    else:
                        self.set_status("❌ Помилка підключення", "error")
                except Exception as e:
                    logger.error(f"Помилка: {e}")
                    self.set_status("❌ Критична помилка", "error")

            thread = threading.Thread(target=connect, daemon=True)
            thread.start()
        else:
            dialog = ctk.CTkInputDialog(
                text="Введіть пароль для RDP:",
                title="Підключення до 1С"
            )
            password = dialog.get_input()

            if password:
                self.set_status("💾 Збереження пароля...", "processing")
                if self.rdp_manager.connect_rdp(RDP_HOST, RDP_PORT, "admin", password):
                    self.rdp_manager.save_credentials(RDP_HOST, "admin", password)
                    self.set_status("✅ Успішно підключено", "success")
                else:
                    self.set_status("❌ Помилка підключення", "error")

    def close_sessions_confirm(self):
        """Підтвердження закриття сесій"""
        result = messagebox.askyesno(
            "Підтвердження",
            "Ви впевнені, що хочете закрити всі RDP сесії?"
        )
        if result:
            self.set_status("⏳ Закриття сесій...", "processing")
            close_all_rdp_sessions()
            self.set_status("✅ Всі сесії закрито", "success")

    def start_anydesk(self):
        """Запустити AnyDesk"""
        if not self.anydesk_manager:
            messagebox.showerror("Помилка", "AnyDesk менеджер не доступен")
            return

        self.set_status("⏳ Запуск AnyDesk...", "processing")

        def anydesk_task():
            try:
                anydesk_id, pwd = self.anydesk_manager.start(None)

                if anydesk_id:
                    self.set_status(f"✅ AnyDesk запущено\n🆔 ID: {anydesk_id}", "success")
                    messagebox.showinfo(
                        "✅ AnyDesk запущено",
                        f"ID підключення: {anydesk_id}\n\n"
                        f"Дані надіслані в Telegram\n"
                        f"Пароль встановлено автоматично"
                    )
                else:
                    self.set_status("❌ Помилка AnyDesk", "error")
                    messagebox.showwarning(
                        "⚠️ Увага",
                        "Не вдалося запустити AnyDesk або отримати ID."
                    )
            except Exception as e:
                logger.error(f"Помилка: {e}")
                self.set_status("❌ Помилка виконання", "error")

        thread = threading.Thread(target=anydesk_task, daemon=True)
        thread.start()

    def run_network_test(self):
        """Запустити тест мережі"""
        self.set_status("⏳ Тест мережі...", "processing")

        def test_task():
            try:
                result = self.network_test.run_full_test()
                self.set_status(f"{result['status']}", result['color'])
            except Exception as e:
                logger.error(f"Помилка тесту: {e}")
                self.set_status("❌ Помилка тесту", "error")

        thread = threading.Thread(target=test_task, daemon=True)
        thread.start()

    def set_status(self, text, status_type="info"):
        """Встановити статус з кольором"""
        color_map = {
            "success": "green",
            "error": "red",
            "processing": "blue",
            "info": "gray"
        }
        self.status_label.configure(text=text, text_color=color_map.get(status_type, "gray"))


def run_password_setter(anydesk_path, password):
    """
    Встановлення пароля AnyDesk в адмін режимі
    Створює прапорець після завершення
    """
    FLAG_FILE_PATH = Path(os.environ.get("PROGRAMDATA", "C:/")) / ".rh_pass_set_flag"

    logger.info(f"[*] Запуск в режимі встановлення пароля для: {anydesk_path}")
    logger.info(f"[*] Шлях до прапорця: {FLAG_FILE_PATH}")

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            logger.error("[!] Потрібні адмін права для --set-anydesk-password")
            sys.exit(1)
    except Exception as e:
        logger.error(f"[!] Не вдалося перевірити права: {e}")
        sys.exit(1)

    if not anydesk_path or not os.path.exists(anydesk_path):
        logger.error(f"[!] Шлях AnyDesk не знайдено: {anydesk_path}")
        sys.exit(1)

    try:
        logger.info(f"[*] Встановлюю пароль AnyDesk (у адмін режимі)...")
        time.sleep(1)

        cmd = [anydesk_path, "--set-password", "_full_access"]

        result = subprocess.run(
            cmd,
            input=password + "\n",
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        logger.info(f"[CODE] {result.returncode}")
        if result.returncode in [0, 8000]:
            logger.info("[✓] Пароль встановлено!")
        else:
            logger.error(f"[!] Код помилки: {result.returncode}")
            logger.error(f"[STDOUT] {result.stdout}")
            logger.error(f"[STDERR] {result.stderr}")

        # Створюємо прапорець
        try:
            with open(FLAG_FILE_PATH, 'w') as f:
                f.write('ok')
            logger.info(f"✅ Створено прапорець: {FLAG_FILE_PATH}")
        except Exception as e:
            logger.error(f"❌ Не вдалося створити прапорець: {e}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"[!] Критична помилка: {e}")
        sys.exit(1)


def main():
    """Головна функція"""
    # Обробка адмін-режиму для AnyDesk
    if len(sys.argv) > 1 and sys.argv[1] == '--set-anydesk-password':
        try:
            anydesk_path = sys.argv[2] if len(sys.argv) > 2 else None
            password = os.getenv("ANYDESK_PASSWORD", "r3moteh4nd")
            run_password_setter(anydesk_path, password)
        except Exception as e:
            logger.error(f"Помилка запуску password_setter: {e}")
            sys.exit(1)
        sys.exit(0)

    # Звичайний запуск
    try:
        logger.info("=" * 60)
        logger.info("ЗАПУСК REMOTEHAND")
        logger.info("=" * 60)

        app = RemoteHandApp()
        app.mainloop()

        logger.info("=" * 60)
        logger.info("REMOTEHAND ЗАВЕРШЕНО")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"КРИТИЧНА ПОМИЛКА: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
