import customtkinter as ctk
from tkinter import messagebox
import sys
import os
import threading
import logging
from pathlib import Path
import ctypes
import subprocess
import time

# (ВИПРАВЛЕНО) Імпорт та налаштування шляхів
from dotenv import load_dotenv


def get_resource_path(relative_path):
    """ (ОНОВЛЕНО) Отримати коректний шлях до ресурсу (для .exe та DEV) """
    try:
        # PyInstaller створює тимчасову папку _MEIPASS
        # для ресурсів, що *всередині* .exe
        base_path = Path(sys._MEIPASS)
    except Exception:
        # В DEV-режимі _MEIPASS не існує, беремо корінь проєкту
        # Або для .exe шукаємо *поруч* з ним
        if getattr(sys, 'frozen', False):
            # Якщо запущено як .exe, шукаємо поруч з .exe
            base_path = Path(sys.executable).parent
        else:
            # Якщо запущено як .py (dev_run.py), шукаємо звідки запущено
            base_path = Path.cwd()
    return base_path / relative_path


# ============ ПЕРЕВІРКА DEV РЕЖИМУ ============
DEV_MODE = os.getenv('REMOTEHAND_DEV_MODE') == '1'

# (ВИПРАВЛЕНО) Завантажуємо .env ТІЛЬКИ в DEV-режимі
if DEV_MODE:
    # dev_run.py встановлює CWD в корінь проєкту, тому .env знайдеться
    env_path = get_resource_path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"🔧 DEV: Завантажено .env файл з {env_path}")
    else:
        print(f"⚠️ DEV: .env файл не знайдено за шляхом {env_path}, сподіваємось на системні змінні.")

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f"{'🔧 DEV РЕЖИM' if DEV_MODE else '✅ PRODUCTION РЕЖИМ'}")

# ============ ОНОВЛЕННЯ (ТІЛЬКИ В PROD) ============
if not DEV_MODE:
    try:
        from updater import check_and_update

        # Ця функція тепер надійно оновить програму
        check_and_update()
    except Exception as e:
        logger.warning(f"Помилка перевірки оновлень: {e}")

# ============ ІМПОРТИ ============
# (ВАЖЛИВО) Ці імпорти мають бути ПІСЛЯ налаштування DEV_MODE
from utils import close_all_rdp_sessions, test_connection
# (ВИПРАВЛЕНО) Імпортуємо токени з config, де вони ВЖЕ взяті з os.getenv()
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

# (ПОКРАЩЕННЯ) Налаштування стилю iOS
IOS_BG_COLOR = "#f2f2f7"
IOS_CARD_COLOR = "#ffffff"
IOS_TEXT_COLOR = "#000000"
IOS_SUBTEXT_COLOR = "#8A8A8E"
IOS_CARD_BORDER = "#E0E0E0"
IOS_CARD_RADIUS = 15
IOS_BUTTON_RADIUS = 12


class RemoteHandApp(ctk.CTk):

    # (ОНОВЛЕНО) get_resource_path тепер метод класу
    def get_resource_path(self, relative_path):
        """ Отримати коректний шлях до ресурсу (для .exe та DEV) """
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

        # (ПОКРАЩЕННЯ) Встановлення іконки
        try:
            icon_path = self.get_resource_path("assets/icon.ico")
            if icon_path.exists():
                self.iconbitmap(icon_path)
                logger.info(f"Іконку успішно завантажено з: {icon_path}")
            else:
                logger.warning(f"Іконку не знайдено за шляхом: {icon_path}")
        except Exception as e:
            logger.error(f"Помилка встановлення іконки: {e}")

        # Ініціалізація менеджерів
        self.config = ConfigManager()

        # (ВИПРАВЛЕНО) Токени ВЖЕ завантажені з config
        logger.info(f"Telegram token: {'✅ встановлено' if TELEGRAM_TOKEN else '❌ НЕ ВСТАНОВЛЕНО!'}")
        logger.info(f"Telegram chat_id: {'✅ встановлено' if TELEGRAM_CHAT_ID else '❌ НЕ ВСТАНОВЛЕНО!'}")

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

        self.setup_ui()  # (ПОКРАЩЕННЯ) Використовуємо iOS-подібний UI

        if self.config.is_first_run():
            self.show_setup_wizard()

    def get_app_version(self):
        """Отримати версію програми (з обробкою кодувань)"""
        try:
            version_file = self.get_resource_path("version.txt")

            if not version_file.exists():
                logger.warning(f"Не знайдено version.txt у {version_file}")
                return "1.0.14"  # Fallback

            try:
                # Спробувати UTF-8-SIG (стандарт з BOM)
                return version_file.read_text(encoding='utf-8-sig').strip()
            except UnicodeDecodeError:
                try:
                    # Якщо не вийшло (byte 0xff), спробувати UTF-16
                    logger.warning("version.txt не в UTF-8, пробую UTF-16...")
                    return version_file.read_text(encoding='utf-16').strip()
                except Exception as e_inner:
                    logger.error(f"Не вдалося прочитати version.txt ні в UTF-8, ні в UTF-16: {e_inner}")
            except Exception as e_outer:
                logger.error(f"Помилка читання версії: {e_outer}")

        except Exception as e:
            logger.error(f"Критична помилка get_app_version: {e}")

        return "1.0.14"  # За замовчуванням

    def show_setup_wizard(self):
        """Показати вікно налаштування при першому запуску"""

        def on_setup_complete(result):
            self.config.set("store", result["store"])
            self.config.set("location", result["location"])
            if result.get("user_name"):
                self.config.set("user_name", result["user_name"])
            self.refresh_ui()

        wizard = SetupWizard(self, on_setup_complete)
        self.wait_window(wizard)

    def refresh_ui(self):
        """Оновити UI після налаштування"""
        user_info = self.config.store_location_text
        user_name = self.config.get("user_name", "")
        if user_name:
            user_info += f" | 👤 {user_name}"
        self.info_label.configure(text=f"📍 {user_info}")

    # (ПОКРАЩЕННЯ) Повністю замінений UI з версії ...151306
    def setup_ui(self):
        """Створення UI в стилі iOS (компактно)"""

        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="RemoteHand",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=IOS_TEXT_COLOR
        )
        title_label.pack(pady=(10, 0), padx=20, anchor="w")

        # Інформація про магазин/локацію + ПІБ
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

        # ==================== RDP БЛОК (КАРТКА 1) ====================
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

        # ==================== ANYDESK БЛОК (КАРТКА 2) ====================
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

        # ==================== ДІАГНОСТИКА (КАРТКА 3) ====================
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

        # ==================== НАЛАШТУВАННЯ (КАРТКА 4) ====================
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

        # ==================== СТАТУС (Внизу) ====================
        self.status_label = ctk.CTkLabel(
            self,
            text="✅ Готово до роботи",
            font=ctk.CTkFont(size=10),
            text_color=IOS_SUBTEXT_COLOR
        )
        self.status_label.pack(pady=8)

        # ==================== ВЕРСІЯ (Внизу) ====================
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
        """Запустити AnyDesk - БЕЗ показу пароля!"""
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
    (ОНОВЛЕНО)
    Ця функція виконує логіку з set_anydesk_password.py.
    Вона запускається ТІЛЬКИ коли програма запущена з адмін правами
    та аргументом --set-anydesk-password.
    СТВОРЮЄ ФАЙЛ-ПРАПОРЕЦЬ ПІСЛЯ ЗАВЕРШЕННЯ.
    """

    # (ОНОВЛЕНО) Використовуємо C:\ProgramData - спільну папку
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

        # (ОНОВЛЕНО) Створюємо прапорець, що робота виконана
        try:
            with open(FLAG_FILE_PATH, 'w') as f:
                f.write('ok')
            logger.info(f"Створено прапорець: {FLAG_FILE_PATH}")
        except Exception as e:
            logger.error(f"Не вдалося створити прапорець: {e}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"[!] Критична помилка: {e}")
        sys.exit(1)


def main():
    """Головна функція"""
    # (ОНОВЛЕНО) Ця логіка тепер обробляє запуск адмін-частини AnyDesk
    if len(sys.argv) > 1 and sys.argv[1] == '--set-anydesk-password':
        try:
            anydesk_path = sys.argv[2] if len(sys.argv) > 2 else None
            password = os.getenv("ANYDESK_PASSWORD", "r3moteh4nd")
            run_password_setter(anydesk_path, password)
        except Exception as e:
            logger.error(f"Помилка запуску password_setter: {e}")
            sys.exit(1)
        sys.exit(0)  # Важливо вийти після виконання

    logger.info("Запуск RemoteHand...")
    app = RemoteHandApp()
    app.mainloop()


if __name__ == "__main__":
    main()