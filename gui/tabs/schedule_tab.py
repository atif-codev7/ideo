import customtkinter as ctk
from core.solar_engine import CITIES, SolarEngine
from database.repository import Repository

class ScheduleTab(ctk.CTkFrame):
    def __init__(self, master, on_schedule_changed_callback=None):
        super().__init__(master, fg_color="transparent")
        self.on_schedule_changed_callback = on_schedule_changed_callback

        self.grid_columnconfigure(0, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Automated Theme Schedules",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(15, 8))

        # Solar Config Section
        self.solar_section = ctk.CTkFrame(self, corner_radius=10)
        self.solar_section.pack(padx=20, pady=6, fill="x")

        self.solar_header = ctk.CTkLabel(
            self.solar_section,
            text="Geographic Location (Solar Ephemeris)",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.solar_header.grid(row=0, column=0, columnspan=2, padx=15, pady=(8, 4), sticky="w")

        self.city_label = ctk.CTkLabel(self.solar_section, text="Select City:")
        self.city_label.grid(row=1, column=0, padx=15, pady=4, sticky="w")

        city_names = list(CITIES.keys())
        self.city_menu = ctk.CTkOptionMenu(
            self.solar_section,
            values=city_names,
            command=self.handle_city_changed
        )
        self.city_menu.grid(row=1, column=1, padx=15, pady=4, sticky="e")

        self.solar_desc = ctk.CTkLabel(
            self.solar_section,
            text="Sunrise ➔ Light Mode  |  Sunset ➔ Dark Mode automatically.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.solar_desc.grid(row=2, column=0, columnspan=2, padx=15, pady=(2, 8), sticky="w")

        # Custom Time Schedules Section
        self.custom_header = ctk.CTkLabel(
            self,
            text="Custom Time Schedules",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.custom_header.pack(pady=(10, 4), padx=20, anchor="w")

        # Add New Schedule Bar
        self.add_frame = ctk.CTkFrame(self, corner_radius=8)
        self.add_frame.pack(padx=20, pady=4, fill="x")

        self.time_entry = ctk.CTkEntry(self.add_frame, placeholder_text="HH:MM (e.g. 23:00)", width=140)
        self.time_entry.pack(side="left", padx=10, pady=8)

        self.target_menu = ctk.CTkOptionMenu(
            self.add_frame,
            values=["dark", "light"],
            width=100
        )
        self.target_menu.pack(side="left", padx=5, pady=8)

        self.add_btn = ctk.CTkButton(
            self.add_frame,
            text="Add Schedule",
            width=100,
            command=self.handle_add_schedule
        )
        self.add_btn.pack(side="left", padx=10, pady=8)

        # Schedules List (Scrollable)
        self.schedules_scroll = ctk.CTkScrollableFrame(self, height=160, corner_radius=8)
        self.schedules_scroll.pack(padx=20, pady=8, fill="both", expand=True)

        self.refresh()

    def refresh(self):
        pref = Repository.get_preferences()
        current_city = pref.get("city_name", "New Delhi")
        if current_city in CITIES:
            self.city_menu.set(current_city)

        for widget in self.schedules_scroll.winfo_children():
            widget.destroy()

        schedules = Repository.get_schedules()
        if not schedules:
            empty_lbl = ctk.CTkLabel(self.schedules_scroll, text="No active schedules configured.", text_color="gray")
            empty_lbl.pack(pady=20)
            return

        for s in schedules:
            row = ctk.CTkFrame(self.schedules_scroll, corner_radius=6)
            row.pack(fill="x", pady=3, padx=5)

            target = s.get("target_theme", "dark")
            icon = "🌙" if target == "dark" else "☀️"
            stype = s.get("schedule_type")
            timing = s.get("custom_time") if stype == "custom_time" else stype.replace("_", " ").title()

            info_text = f"{icon} {s.get('name', 'Schedule')}  •  {timing}  •  Target: {target.upper()}"
            lbl = ctk.CTkLabel(row, text=info_text, font=ctk.CTkFont(size=11))
            lbl.pack(side="left", padx=10, pady=5)

            sid = s.get("id")
            del_btn = ctk.CTkButton(
                row,
                text="Delete",
                width=55,
                height=22,
                fg_color="#ef4444",
                hover_color="#dc2626",
                command=lambda id=sid: self.handle_delete_schedule(id)
            )
            del_btn.pack(side="right", padx=10, pady=5)

    def handle_city_changed(self, selected_city):
        if selected_city in CITIES:
            data = CITIES[selected_city]
            Repository.update_preferences({
                "city_name": selected_city,
                "latitude": data["lat"],
                "longitude": data["lon"]
            })
            if self.on_schedule_changed_callback:
                self.on_schedule_changed_callback()

    def handle_add_schedule(self):
        raw_time = self.time_entry.get().strip()
        target = self.target_menu.get().lower()

        if not raw_time or ":" not in raw_time:
            return

        try:
            parts = raw_time.split(":")
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                return
            formatted_time = f"{h:02d}:{m:02d}"
        except Exception:
            return

        # Fetch profile
        p_name = "Dark Mode" if target == "dark" else "Light Mode"
        profile = Repository.get_profile_by_name(p_name)
        if not profile:
            return

        name = f"{target.title()} Mode at {formatted_time}"
        Repository.add_schedule(
            name=name,
            profile_id=profile["id"],
            target_theme=target,
            schedule_type="custom_time",
            custom_time=formatted_time
        )
        self.time_entry.delete(0, "end")
        self.refresh()
        if self.on_schedule_changed_callback:
            self.on_schedule_changed_callback()

    def handle_delete_schedule(self, schedule_id):
        Repository.delete_schedule(schedule_id)
        self.refresh()
        if self.on_schedule_changed_callback:
            self.on_schedule_changed_callback()
