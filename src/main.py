import customtkinter as ctk
from tkinter import messagebox
import sys
from config import RDP_HOST, RDP_PORT, PING_HOST, APP_NAME
from utils import SingleInstance, open_rdp_connection, close_all_rdp_sessions, test_connection
from updater import check_and_update


class RemoteHandApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування вікна
        self.title(APP_NAME)
        self.geometry("400x350")
        self.resizable(False, False)

        # Встановлення теми iOS-style
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.setup_ui()

    def setup_ui(self):
        """Створення інтерфейсу"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="RemoteHand",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=20)

        # Кнопка відкриття 1С
        open_1c_btn = ctk.CTkButton(
            self,
            text="🖥️ Відкрити 1С (RDP)",
            command=self.open_1c,
            width=300,
            height=50,
            font=ctk.CTkFont(size=16),
            corner_radius=15
        )
        open_1c_btn.pack(pady=10)

        # Кнопка закриття сесій
        close_sessions_btn = ctk.CTkButton(
            self,
            text="❌ Закрити всі RDP сесії",
            command=self.close_sessions_confirm,
            width=300,
            height=50,
            font=ctk.CTkFont(size=16),
            corner_radius=15,
            fg_color="#FF3B30",
            hover_color="#D70015"
        )
        close_sessions_btn.pack(pady=10)

        # Кнопка тесту з'єднання
        test_btn = ctk.CTkButton(
            self,
            text="🌐 Тест з'єднання",
            command=self.test_ping,
            width=300,
            height=50,
            font=ctk.CTkFont(size=16),
            corner_radius=15,
            fg_color="#34C759",
            hover_color="#248A3D"
        )
        test_btn.pack(pady=10)

        # Статус
        self.status_label = ctk.CTkLabel(
            self,
            text="Готово до роботи",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=20)

    def open_1c(self):
        """Відкриття RDP підключення до 1С"""
        open_rdp_connection(RDP_HOST, RDP_PORT)
        self.status_label.configure(text=f"Підключення до {RDP_HOST}:{RDP_PORT}")

    def close_sessions_confirm(self):
        """Підтвердження закриття сесій"""
        result = messagebox.askyesno(
            "Підтвердження",
            "Ви впевнені, що хочете закрити всі віддалені RDP сесії?"
        )
        if result:
            close_all_rdp_sessions()
            self.status_label.configure(text="Всі RDP сесії закрито")
            messagebox.showinfo("Успіх", "Всі RDP сесії закрито")

    def test_ping(self):
        """Тест ping з'єднання"""
        self.status_label.configure(text="Перевірка з'єднання...")
        self.update()

        if test_connection(PING_HOST):
            self.status_label.configure(text=f"✅ З'єднання з {PING_HOST} успішне")
            messagebox.showinfo("Успіх", f"З'єднання з {PING_HOST} працює")
        else:
            self.status_label.configure(text=f"❌ З'єднання з {PING_HOST} не вдалося")
            messagebox.showerror("Помилка", f"Не вдалося з'єднатися з {PING_HOST}")


def main():
    # Перевірка на єдиний екземпляр
    instance = SingleInstance()
    if instance.is_running():
        messagebox.showwarning("Увага", f"{APP_NAME} вже запущено!")
        sys.exit(0)

    # Перевірка оновлень
    check_and_update()

    # Запуск програми
    app = RemoteHandApp()
    app.mainloop()


if __name__ == "__main__":
    main()
