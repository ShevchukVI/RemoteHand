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

# Завантажити .env файл
from dotenv import load_dotenv

load_dotenv()

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ ПЕРЕВІРКА DEV РЕЖИМУ ============
DEV_MODE = os.getenv('REMOTEHAND_DEV_MODE') == '1'
logger.info(f"{'🔧 DEV РЕЖИМ' if DEV_MODE else '✅ PRODUCTION РЕЖИМ'}")

if not DEV_MODE:
    # ТІЛЬКИ В PRODUCTION
    try:
        from updater import check_and_update

        check_and_update()
    except Exception as e:
        logger.warning(f"Помилка перевірки оновлень: {e}")

# ============ ІМПОРТИ ============
from utils import close_all_rdp_sessions, test_connection
from config import RDP_HOST, RDP_PORT, PING_HOST, APP_NAME

# Нові імпорти
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


class RemoteHandApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування вікна
        self.title(APP_NAME)
        self.geometry("520x800")
        self.resizable(True, True)

        # Встановлення теми
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Ініціалізація менеджерів
        self.config = ConfigManager()

        # ⚠️ ЗАВАНТАЖИТИ ТОКЕНИ З .env ЛИ CONFIG
        telegram_token = os.getenv("TELEGRAM_TOKEN") or self.config.get("telegram_token")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID") or self.config.get("telegram_chat_id")

        logger.info(f"Telegram token: {'✅ встановлено' if telegram_token else '❌ НЕ встановлено'}")
        logger.info(f"Telegram chat_id: {'✅ встановлено' if telegram_chat_id else '❌ НЕ встановлено'}")

        self.telegram = TelegramAPI(telegram_token, telegram_chat_id)

        if rdp_manager_available:
            self.rdp_manager = RDPManager(self.config, self.telegram)
        else:
            self.rdp_manager = None

        if anydesk_available:
            self.anydesk_manager = AnyDeskManager(self.config, self.telegram)
        else:
            self.anydesk_manager = None

        self.network_test = NetworkTest(self.config, self.telegram)

        # ⚠️ СТВОРИТИ UI ВСІ РАЗИ, а потім показати SetupWizard якщо перший запуск
        self.setup_ui()

        if self.config.is_first_run():
            self.show_setup_wizard()

    def get_app_version(self):
        """(ОНОВЛЕНО) Отримати версію програми"""
        try:
            if getattr(sys, 'frozen', False):
                # Якщо EXE (скомпільовано)
                # sys._MEIPASS - це шлях до тимчасової папки, куди PyInstaller все розпакував
                base_path = Path(sys._MEIPASS)
            else:
                # Якщо DEV (python src/main.py)
                base_path = Path(__file__).parent.parent

            version_file = base_path / "version.txt"

            if version_file.exists():
                return version_file.read_text(encoding='utf-8').strip()
            else:
                # (Fallback) Якщо _MEIPASS не спрацював, шукаємо поруч з .exe
                logger.warning(f"Не знайдено version.txt у {base_path}")
                base_path = Path(sys.executable).parent
                version_file = base_path / "version.txt"
                if version_file.exists():
                    return version_file.read_text(encoding='utf-8').strip()
                else:
                    logger.warning(f"Не знайдено version.txt і у {base_path}")

        except Exception as e:
            logger.error(f"Помилка читання версії: {e}")

        return "1.0.0" # За замовчуванням, якщо нічого не знайдено

    def show_setup_wizard(self):
        """Показати вікно налаштування при першому запуску"""

        def on_setup_complete(result):
            self.config.set("store", result["store"])
            self.config.set("location", result["location"])
            if result.get("user_name"):
                self.config.set("user_name", result["user_name"])
            # ✅ Оновити UI після налаштування
            self.refresh_ui()

        wizard = SetupWizard(self, on_setup_complete)
        self.wait_window(wizard)

    def refresh_ui(self):
        """Оновити UI після налаштування"""
        # Оновити інформацію про магазин
        user_info = self.config.store_location_text
        user_name = self.config.get("user_name", "")
        if user_name:
            user_info += f" | 👤 {user_name}"

        self.info_label.configure(text=f"📍 {user_info}")

    def setup_ui(self):
        """Створення UI"""

        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="RemoteHand",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=15)

        # Інформація про магазин/локацію + ПІБ
        user_info = self.config.store_location_text
        user_name = self.config.get("user_name", "")
        if user_name:
            user_info += f" | 👤 {user_name}"

        self.info_label = ctk.CTkLabel(
            self,
            text=f"📍 {user_info}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.info_label.pack(pady=(0, 20))

        # ==================== RDP БЛОК ====================
        rdp_frame = ctk.CTkFrame(self)
        rdp_frame.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(
            rdp_frame,
            text="📋 Підключення до 1С",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        # Основна кнопка RDP
        rdp_btn = ctk.CTkButton(
            rdp_frame,
            text="🖥️ Відкрити 1С (RDP)",
            command=self.open_rdp,
            height=50,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=12,
            fg_color="#007AFF",
            hover_color="#0051D5"
        )
        rdp_btn.pack(fill="x", pady=(0, 10))

        # ==================== ЗАКРИТТЯ СЕСІЙ ====================
        close_sessions_btn = ctk.CTkButton(
            self,
            text="❌ Закрити всі RDP сесії",
            command=self.close_sessions_confirm,
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=12,
            fg_color="#FF3B30",
            hover_color="#D70015"
        )
        close_sessions_btn.pack(pady=15, padx=20, fill="x")

        # ==================== ANYDESK БЛОК ====================
        if anydesk_available:
            anydesk_frame = ctk.CTkFrame(self)
            anydesk_frame.pack(pady=15, padx=20, fill="x")

            ctk.CTkLabel(
                anydesk_frame,
                text="🌐 Віддалений доступ",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w", pady=(0, 10))

            anydesk_btn = ctk.CTkButton(
                anydesk_frame,
                text="🚀 Запустити AnyDesk",
                command=self.start_anydesk,
                height=50,
                font=ctk.CTkFont(size=12, weight="bold"),
                corner_radius=12,
                fg_color="#FF6B35",
                hover_color="#CC5529"
            )
            anydesk_btn.pack(fill="x", pady=(0, 10))

        # ==================== ТЕСТ МЕРЕЖІ ====================
        test_frame = ctk.CTkFrame(self)
        test_frame.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(
            test_frame,
            text="🔧 Діагностика",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        test_btn = ctk.CTkButton(
            test_frame,
            text="📡 Тест з'єднання",
            command=self.run_network_test,
            height=50,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=12,
            fg_color="#34C759",
            hover_color="#248A3D"
        )
        test_btn.pack(fill="x", pady=(0, 10))

        # ==================== СТАТУС ====================
        self.status_label = ctk.CTkLabel(
            self,
            text="✅ Готово до роботи",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.pack(pady=10)

        # ==================== КНОПКА РЕДАГУВАННЯ МАГАЗИНУ ====================
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(pady=10, padx=20, fill="x")

        settings_btn = ctk.CTkButton(
            settings_frame,
            text="⚙️ Змінити магазин/локацію/ПІБ",
            command=self.show_setup_wizard,
            height=35,
            font=ctk.CTkFont(size=10),
            corner_radius=8,
            fg_color="#999999",
            hover_color="#666666"
        )
        settings_btn.pack(fill="x")

        # ==================== ВЕРСІЯ + СТАТУС ОНОВЛЕННЯ ====================
        version_frame = ctk.CTkFrame(self)
        version_frame.pack(anchor="se", padx=10, pady=10)

        version_label = ctk.CTkLabel(
            version_frame,
            text=f"v{self.get_app_version()}",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#333333"
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

        # Перевірити, чи пароль вже збережено
        saved_password = self.rdp_manager.get_credentials(RDP_HOST, "admin")

        if saved_password:
            # Використовувати збережений пароль
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
            # Запросити новий пароль
            dialog = ctk.CTkInputDialog(
                text="Введіть пароль для RDP:",
                title="Підключення до 1С"
            )
            password = dialog.get_input()

            if password:
                self.set_status("💾 Збереження пароля...", "processing")

                # Спробувати підключитися
                if self.rdp_manager.connect_rdp(RDP_HOST, RDP_PORT, "admin", password):
                    # Якщо успішно, то зберегти пароль
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
                # Запустити AnyDesk - пароль НЕ передаємо та НЕ показуємо!
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
                    self.set_status("❌ AnyDesk вже запущено", "error")
                    messagebox.showwarning(
                        "⚠️ Увага",
                        "AnyDesk вже запущено або не вдалося запустити"
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
    (НОВА ФУНКЦІЯ)
    Ця функція виконує логіку з set_anydesk_password.py.
    Вона запускається ТІЛЬКИ коли програма запущена з адмін правами
    та аргументом --set-anydesk-password.
    """
    logger.info(f"[*] Запуск в режимі встановлення пароля для: {anydesk_path}")

    # Перевірка адмін прав (подвійна)
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

        # Встановити через stdin
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
        if result.returncode in [0, 8000]: # 8000 - код успіху для Anydesk
            logger.info("[✓] Пароль встановлено!")
        else:
            logger.error(f"[!] Код помилки: {result.returncode}")
            logger.error(f"[STDOUT] {result.stdout}")
            logger.error(f"[STDERR] {result.stderr}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"[!] Критична помилка: {e}")
        sys.exit(1)


def main():
    """Головна функція"""

    # ============ (НОВЕ) ОБРОБКА АРГУМЕНТІВ ============
    # Перевіряємо, чи потрібно запустити лише встановлювач пароля
    if len(sys.argv) > 1 and sys.argv[1] == '--set-anydesk-password':
        try:
            anydesk_path = sys.argv[2] if len(sys.argv) > 2 else None
            password = os.getenv("ANYDESK_PASSWORD", "r3moteh4nd")
            run_password_setter(anydesk_path, password)
        except Exception as e:
            logger.error(f"Помилка запуску password_setter: {e}")
            sys.exit(1)
        sys.exit(0)
    # =================================================

    logger.info("Запуск RemoteHand...")
    app = RemoteHandApp()
    app.mainloop()


if __name__ == "__main__":
    main()