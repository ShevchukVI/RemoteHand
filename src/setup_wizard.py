import customtkinter as ctk
from tkinter import ttk


class SetupWizard(ctk.CTkToplevel):
    """Вікно вибору магазину та локації при першому запуску"""

    STORES = [
        "Офіс",
        "1 / Діалог",
        "5 / Полтава",
        "7 / Оазис",
        "8 / Хмельницький",
        "9 / Чернівці",
        "17 / Кременчук",
        "18 / П_Котляревського",
        "20 / Щасливий",
        "21 / Софія молл"
    ]

    LOCATIONS = [
        "Каса",
        "Каса 2",
        "Підсобка",
        "Персональний"
    ]

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Налаштування RemoteHand")
        self.geometry("400x300")
        self.resizable(False, False)
        self.callback = callback
        self.result = None

        # Зробити вікно модальним
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        """Створення UI"""

        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="Перше налаштування",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Магазин
        ctk.CTkLabel(
            self,
            text="Оберіть магазин:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.store_combo = ttk.Combobox(
            self,
            values=self.STORES,
            state="readonly",
            width=40
        )
        self.store_combo.pack(padx=20, pady=(0, 15))
        self.store_combo.current(0)

        # Локація
        ctk.CTkLabel(
            self,
            text="Оберіть розміщення ПК:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.location_combo = ttk.Combobox(
            self,
            values=self.LOCATIONS,
            state="readonly",
            width=40
        )
        self.location_combo.pack(padx=20, pady=(0, 20))
        self.location_combo.current(0)

        # Кнопка ОК
        ok_btn = ctk.CTkButton(
            self,
            text="✅ Продовжити",
            command=self.on_ok,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        ok_btn.pack(padx=20, pady=20, fill="x")

    def on_ok(self):
        """Обробка натиснення кнопки ОК"""
        self.result = {
            "store": self.store_combo.get(),
            "location": self.location_combo.get()
        }
        self.callback(self.result)
        self.destroy()
