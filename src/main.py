import customtkinter as ctk
from tkinter import messagebox
import sys
import threading
import random
import string
import logging
import os
import json

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Базові функції
from utils import open_rdp_connection, close_all_rdp_sessions, test_connection
from config import RDP_HOST, RDP_PORT, PING_HOST, APP_NAME
from updater import check_and_update

# Новітні функції
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

try:
    from telegram_helper import TelegramHelper

    telegram_available = True
except ImportError as e:
    telegram_available = False
    logger.warning(f"telegram_helper не доступна: {e}")


class RemoteHandApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування вікна
        self.title(APP_NAME)
        self.geometry("500x900")
        self.resizable(False, False)

        # Встановлення теми iOS-style
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Ініціалізація менеджерів
        if rdp_manager_available:
            self.rdp_manager = RDPManager()
        else:
            self.rdp_manager = None

        if anydesk_available:
            self.anydesk_manager = AnyDeskManager()
        else:
            self.anydesk_manager = None

        if telegram_available:
            self.telegram = TelegramHelper()
        else:
            self.telegram = None

        self.setup_ui()

    def setup_ui(self):
        """Створення UI"""

        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="RemoteHand",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=20)

        # ==================== RDP БЛОК ====================
        rdp_frame = ctk.CTkFrame(self)
        rdp_frame.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(
            rdp_frame,
            text="📋 1С - RDP Підключення",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        # Кнопка звичайного RDP
        open_1c_btn = ctk.CTkButton(
            rdp_frame,
            text="🖥️ Відкрити 1С (RDP)",
            command=self.open_1c_dialog,
            height=45,
            font=ctk.CTkFont(size=12),
            corner_radius=10
        )
        open_1c_btn.pack(fill="x", pady=(0, 8))

        # Кнопка швидкого підключення
        if rdp_manager_available:
            auto_rdp_btn = ctk.CTkButton(
                rdp_frame,
                text="⚡ Швидке підключення (авто-пароль)",
                command=self.connect_rdp_auto,
                height=45,
                font=ctk.CTkFont(size=12),
                corner_radius=10,
                fg_color="#00AA00",
                hover_color="#008800"
            )
            auto_rdp_btn.pack(fill="x")

        # ==================== ЗАКРИТТЯ СЕСІЙ ====================
        close_sessions_btn = ctk.CTkButton(
            self,
            text="❌ Закрити всі RDP сесії",
            command=self.close_sessions_confirm,
            height=50,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=15,
            fg_color="#FF3B30",
            hover_color="#D70015"
        )
        close_sessions_btn.pack(pady=15, padx=20, fill="x")

        # ==================== ANYDESK БЛОК ====================
        if anydesk_available and telegram_available:
            anydesk_frame = ctk.CTkFrame(self)
            anydesk_frame.pack(pady=15, padx=20, fill="x")

            ctk.CTkLabel(
                anydesk_frame,
                text="🌐 Віддалений доступ - AnyDesk",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w", pady=(0, 10))

            anydesk_btn = ctk.CTkButton(
                anydesk_frame,
                text="🌐 Запустити AnyDesk + Telegram",
                command=self.start_anydesk,
                height=45,
                font=ctk.CTkFont(size=12),
                corner_radius=10,
                fg_color="#FF6B35",
                hover_color="#CC5529"
            )
            anydesk_btn.pack(fill="x")

        # ==================== ТЕСТ З'ЄДНАННЯ ====================
        test_frame = ctk.CTkFrame(self)
        test_frame.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(
            test_frame,
            text="🔧 Діагностика",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        test_btn = ctk.CTkButton(
            test_frame,
            text="🌐 Тест з'єднання (ping 8.8.8.8)",
            command=self.test_ping,
            height=45,
            font=ctk.CTkFont(size=12),
            corner_radius=10,
            fg_color="#34C759",
            hover_color="#248A3D"
        )
        test_btn.pack(fill="x")

        # ==================== СТАТУС ====================
        self.status_label = ctk.CTkLabel(
            self,
            text="✅ Готово до роботи",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.pack(pady=20)

    def open_1c_dialog(self):
        """Діалог для вводу пароля та запуску RDP"""
        dialog = ctk.CTkInputDialog(
            text="Введіть пароль для RDP:",
            title="Підключення до 1С"
        )
        password = dialog.get_input()

        if password:
            # Зберегти пароль якщо доступна функція
            if self.rdp_manager:
                self.rdp_manager.save_credentials(RDP_HOST, "admin", password)

            # Запустити RDP
            open_rdp_connection(RDP_HOST, RDP_PORT)
            self.status_label.configure(text=f"✅ Підключення до {RDP_HOST}:{RDP_PORT}")

    def connect_rdp_auto(self):
        """Швидке підключення з автоматичним паролем"""
        if not self.rdp_manager:
            messagebox.showerror("Помилка", "RDP менеджер не доступен")
            return

        self.status_label.configure(text="⏳ Підключення...")
        self.update()

        if self.rdp_manager.connect_rdp_auto(RDP_HOST, RDP_PORT, "admin"):
            self.status_label.configure(text="✅ Автоматичне підключення активовано")
        else:
            self.status_label.configure(text="❌ Пароль не збережено")
            messagebox.showerror(
                "Помилка",
                "Пароль не знайдено.\n\n"
                "Спочатку натисніть '🖥️ Відкрити 1С (RDP)' для збереження пароля."
            )

    def close_sessions_confirm(self):
        """Підтвердження закриття сесій"""
        result = messagebox.askyesno(
            "Підтвердження",
            "Ви впевнені, що хочете закрити всі віддалені RDP сесії?"
        )
        if result:
            close_all_rdp_sessions()
            self.status_label.configure(text="✅ Всі RDP сесії закрито")
            messagebox.showinfo("Успіх", "Всі RDP сесії закрито")

    def start_anydesk(self):
        """Запустити AnyDesk та відправити код в Telegram"""
        if not self.anydesk_manager:
            messagebox.showerror("Помилка", "AnyDesk менеджер не доступен")
            return

        if not self.telegram:
            messagebox.showerror("Помилка", "Telegram помічник не доступен")
            return

        self.status_label.configure(text="⏳ Запуск AnyDesk...")
        self.update()

        def anydesk_task():
            try:
                # Генерувати пароль
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                logger.info(f"Запуск AnyDesk з паролем: {password}")

                # Запустити AnyDesk
                anydesk_id, pwd = self.anydesk_manager.start(password)

                if anydesk_id:
                    logger.info(f"AnyDesk ID: {anydesk_id}")

                    # Відправити в Telegram
                    if self.telegram.send_anydesk_code_sync(anydesk_id, password):
                        self.status_label.configure(
                            text=f"✅ AnyDesk запущено\n🆔 ID: {anydesk_id}\n✉️ Код надісланий в Telegram"
                        )
                        messagebox.showinfo(
                            "Успіх",
                            f"AnyDesk запущено!\n\n"
                            f"ID: {anydesk_id}\n"
                            f"Пароль: {password}\n\n"
                            f"Код надісланий в Telegram"
                        )
                    else:
                        self.status_label.configure(
                            text=f"⚠️ AnyDesk запущено\n🆔 ID: {anydesk_id}\n❌ Помилка Telegram"
                        )
                        messagebox.showwarning(
                            "Частикова помилка",
                            f"AnyDesk запущено, але код не надісланий в Telegram\n\n"
                            f"ID: {anydesk_id}\n"
                            f"Пароль: {password}"
                        )
                else:
                    self.status_label.configure(text="❌ Помилка запуску AnyDesk")
                    messagebox.showerror("Помилка", "Не вдалося запустити AnyDesk")

            except Exception as e:
                logger.error(f"Помилка: {e}")
                self.status_label.configure(text="❌ Помилка виконання")
                messagebox.showerror("Помилка", f"Виникла помилка:\n{str(e)}")

        # Запустити в потоці
        thread = threading.Thread(target=anydesk_task, daemon=True)
        thread.start()

    def test_ping(self):
        """Тест ping з'єднання"""
        self.status_label.configure(text="⏳ Перевірка з'єднання...")
        self.update()

        if test_connection(PING_HOST):
            self.status_label.configure(text=f"✅ З'єднання з {PING_HOST} успішне")
            messagebox.showinfo("Успіх", f"З'єднання з {PING_HOST} працює ✅")
        else:
            self.status_label.configure(text=f"❌ З'єднання з {PING_HOST} не вдалося")
            messagebox.showerror("Помилка", f"Не вдалося з'єднатися з {PING_HOST}")


def main():
    # ⚠️ ВИДАЛЕНО ПЕРЕВІРКУ ОНОВЛЕНЬ ДЛЯ ЛОКАЛЬНОГО ТЕСТУВАННЯ
    # try:
    #     check_and_update()
    # except Exception as e:
    #     logger.warning(f"Помилка перевірки оновлень: {e}")

    # Запуск програми
    app = RemoteHandApp()
    app.mainloop()


if __name__ == "__main__":
    main()
