import customtkinter as ctk
import tkinter.messagebox as messagebox


class SetupWizard(ctk.CTkToplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)

        self.title("RemoteHand - Первоначальная настройка")
        self.geometry("450x500")
        self.resizable(False, False)

        # Центрувати на екрані
        self.transient(parent)
        self.grab_set()

        # ⚠️ ЗАБОРОНИТИ ЗАКРИТТЯ БЕЗ ЗБЕРЕЖЕННЯ
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.on_complete = on_complete
        self.setup_complete = False

        # Встановлення теми
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="Первоначальная настройка",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=20)

        # ===== МАГАЗИН (ВЫБІР) =====
        ctk.CTkLabel(
            self,
            text="Виберіть магазин:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.store_var = ctk.StringVar(value="")
        store_options = [
            "0 / Офіс",
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

        self.store_menu = ctk.CTkComboBox(
            self,
            values=store_options,
            variable=self.store_var,
            font=ctk.CTkFont(size=11),
            height=35
        )
        self.store_menu.pack(padx=20, fill="x", pady=(0, 20))

        # ===== ЛОКАЦІЯ (ВЫБІР) =====
        ctk.CTkLabel(
            self,
            text="Виберіть локацію:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.location_var = ctk.StringVar(value="")
        location_options = [
            "каса",
            "каса 2",
            "підсобка",
            "особистий"
        ]

        self.location_menu = ctk.CTkComboBox(
            self,
            values=location_options,
            variable=self.location_var,
            font=ctk.CTkFont(size=11),
            height=35
        )
        self.location_menu.pack(padx=20, fill="x", pady=(0, 20))

        # ===== ПІБ (ОПЦІЙНО) =====
        ctk.CTkLabel(
            self,
            text="ПІБ користувача (опційно):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.user_name_entry = ctk.CTkEntry(
            self,
            placeholder_text="Наприклад: Іван Петренко",
            height=35,
            font=ctk.CTkFont(size=11)
        )
        self.user_name_entry.pack(padx=20, fill="x", pady=(0, 30))

        # Кнопка
        btn = ctk.CTkButton(
            self,
            text="✅ Зберегти",
            command=self.save_settings,
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10
        )
        btn.pack(padx=20, fill="x", pady=10)

    def on_closing(self):
        """Заборонити закриття без введення даних"""
        if not self.setup_complete:
            messagebox.showwarning(
                "Помилка",
                "Виберіть магазин і локацію перед закриттям!"
            )
            return
        self.destroy()

    def save_settings(self):
        """Зберегти налаштування - обов'язково перевірити"""
        store = self.store_var.get().strip()
        location = self.location_var.get().strip()
        user_name = self.user_name_entry.get().strip()

        # ⚠️ ОБОВ'ЯЗКОВА ПЕРЕВІРКА
        if not store:
            messagebox.showerror("Помилка", "Виберіть магазин!")
            return

        if not location:
            messagebox.showerror("Помилка", "Виберіть локацію!")
            return

        # Все ок - збережемо
        self.setup_complete = True
        self.on_complete({
            "store": store,
            "location": location,
            "user_name": user_name
        })
        self.destroy()
