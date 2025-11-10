import customtkinter as ctk
import tkinter.messagebox as messagebox

# (НОВЕ) Налаштування стилю iOS
IOS_BG_COLOR = "#f2f2f7"
IOS_CARD_COLOR = "#ffffff"
IOS_TEXT_COLOR = "#000000"
IOS_CARD_BORDER = "#E0E0E0"
IOS_CARD_RADIUS = 15
IOS_BUTTON_RADIUS = 12


class SetupWizard(ctk.CTkToplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)

        self.title("RemoteHand - Налаштування")
        self.geometry("450x520")
        self.resizable(False, False)

        # (ОНОВЛЕНО) Встановлення фону
        self.configure(fg_color=IOS_BG_COLOR)

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.on_complete = on_complete
        self.setup_complete = False

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="Перше налаштування",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=IOS_TEXT_COLOR
        )
        title.pack(pady=20, padx=20, anchor="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Вкажіть, де знаходиться цей комп'ютер.",
            font=ctk.CTkFont(size=13),
            text_color="#8A8A8E"
        )
        subtitle.pack(pady=(0, 20), padx=20, anchor="w")

        # (НОВЕ) Картка для налаштувань
        main_frame = ctk.CTkFrame(
            self,
            fg_color=IOS_CARD_COLOR,
            corner_radius=IOS_CARD_RADIUS,
            border_width=1,
            border_color=IOS_CARD_BORDER
        )
        main_frame.pack(fill="x", padx=20)

        # ===== МАГАЗИН (ВИБІР) =====
        ctk.CTkLabel(
            main_frame,
            text="Виберіть магазин:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=IOS_TEXT_COLOR
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.store_var = ctk.StringVar(value="")
        store_options = [
            "0 / Офіс", "1 / Діалог", "5 / Полтава", "7 / Оазис",
            "8 / Хмельницький", "9 / Чернівці", "17 / Кременчук",
            "18 / П_Котляревського", "20 / Щасливий", "21 / Софія молл"
        ]

        self.store_menu = ctk.CTkComboBox(
            main_frame,
            values=store_options,
            variable=self.store_var,
            font=ctk.CTkFont(size=11),
            height=35,
            corner_radius=IOS_BUTTON_RADIUS
        )
        self.store_menu.pack(padx=15, fill="x")

        # ===== ЛОКАЦІЯ (ВИБІР) =====
        ctk.CTkLabel(
            main_frame,
            text="Виберіть локацію:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=IOS_TEXT_COLOR
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.location_var = ctk.StringVar(value="")
        location_options = [
            "каса", "каса 2", "підсобка", "особистий"
        ]

        self.location_menu = ctk.CTkComboBox(
            main_frame,
            values=location_options,
            variable=self.location_var,
            font=ctk.CTkFont(size=11),
            height=35,
            corner_radius=IOS_BUTTON_RADIUS
        )
        self.location_menu.pack(padx=15, fill="x")

        # ===== ПІБ (ОПЦІЙНО) =====
        ctk.CTkLabel(
            main_frame,
            text="ПІБ користувача (опційно):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=IOS_TEXT_COLOR
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.user_name_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Наприклад: Іван Петренко",
            height=35,
            font=ctk.CTkFont(size=11),
            corner_radius=IOS_BUTTON_RADIUS
        )
        self.user_name_entry.pack(padx=15, fill="x", pady=(0, 20))

        # Кнопка збереження
        btn = ctk.CTkButton(
            self,
            text="✅ Зберегти",
            command=self.save_settings,
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=IOS_BUTTON_RADIUS
        )
        btn.pack(padx=20, fill="x", pady=20)

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

        if not store:
            messagebox.showerror("Помилка", "Виберіть магазин!")
            return

        if not location:
            messagebox.showerror("Помилка", "Виберіть локацію!")
            return

        self.setup_complete = True
        self.on_complete({
            "store": store,
            "location": location,
            "user_name": user_name
        })
        self.destroy()