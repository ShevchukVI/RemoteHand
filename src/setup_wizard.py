import customtkinter as ctk


class SetupWizard(ctk.CTkToplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)

        self.title("RemoteHand - Налаштування")
        self.geometry("400x350")
        self.resizable(False, False)

        self.on_complete = on_complete

        # Встановлення теми
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="Перше налаштування",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=20)

        # ===== МАГАЗИН =====
        ctk.CTkLabel(self, text="Номер магазину:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=20,
                                                                                                  pady=(10, 5))
        self.store_entry = ctk.CTkEntry(self, placeholder_text="Наприклад: 1", height=35)
        self.store_entry.pack(padx=20, fill="x", pady=(0, 15))

        # ===== ЛОКАЦІЯ =====
        ctk.CTkLabel(self, text="Локація:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=20,
                                                                                           pady=(10, 5))
        self.location_entry = ctk.CTkEntry(self, placeholder_text="Наприклад: Діалог - Каса", height=35)
        self.location_entry.pack(padx=20, fill="x", pady=(0, 15))

        # ===== ПІБ (ОПЦІЙНО) =====
        ctk.CTkLabel(self, text="ПІБ користувача (опційно):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w",
                                                                                                             padx=20,
                                                                                                             pady=(10,
                                                                                                                   5))
        self.user_name_entry = ctk.CTkEntry(self, placeholder_text="Наприклад: Іван Петренко", height=35)
        self.user_name_entry.pack(padx=20, fill="x", pady=(0, 20))

        # Кнопка
        btn = ctk.CTkButton(
            self,
            text="✅ Зберегти",
            command=self.save_settings,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn.pack(padx=20, fill="x", pady=10)

    def save_settings(self):
        """Зберегти налаштування"""
        store = self.store_entry.get().strip()
        location = self.location_entry.get().strip()
        user_name = self.user_name_entry.get().strip()

        if not store or not location:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Помилка", "Заповніть магазин і локацію!")
            return

        self.on_complete({
            "store": store,
            "location": location,
            "user_name": user_name  # Опційне поле
        })
        self.destroy()
