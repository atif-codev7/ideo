import customtkinter as ctk
from core.theme_engine import ThemeEngine
from core.solar_engine import SolarEngine
from database.repository import Repository

class HomeTab(ctk.CTkFrame):
    def __init__(self, master, on_theme_switched_callback=None):
        super().__init__(master, fg_color="transparent")
        self.on_theme_switched_callback = on_theme_switched_callback

        self.grid_columnconfigure(0, weight=1)

        # Title Banner
        self.title_label = ctk.CTkLabel(
            self,
            text="Intelligent Dynamic Environment Orchestrator",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, pady=(15, 8), sticky="ew")

        # Current Status Card
        self.status_card = ctk.CTkFrame(self, corner_radius=12)
        self.status_card.grid(row=1, column=0, padx=25, pady=6, sticky="ew")
        self.status_card.grid_columnconfigure(0, weight=1)

        self.status_subtitle = ctk.CTkLabel(
            self.status_card,
            text="ACTIVE ENVIRONMENT PROFILE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray"
        )
        self.status_subtitle.pack(pady=(10, 2))

        self.theme_display = ctk.CTkLabel(
            self.status_card,
            text="FULL DARK",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.theme_display.pack(pady=(0, 4))

        self.theme_detail_label = ctk.CTkLabel(
            self.status_card,
            text="System: Dark  |  Apps: Dark",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.theme_detail_label.pack(pady=(0, 10))

        # Profile Switch Buttons Row (Full Dark, Full Light, Hybrid Focus)
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, padx=25, pady=8, sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_dark = ctk.CTkButton(
            self.btn_frame,
            text="🌙 Full Dark",
            height=38,
            corner_radius=8,
            command=lambda: self.handle_apply_profile("Full Dark")
        )
        self.btn_dark.grid(row=0, column=0, padx=4, sticky="ew")

        self.btn_light = ctk.CTkButton(
            self.btn_frame,
            text="☀️ Full Light",
            height=38,
            corner_radius=8,
            command=lambda: self.handle_apply_profile("Full Light")
        )
        self.btn_light.grid(row=0, column=1, padx=4, sticky="ew")

        self.btn_hybrid = ctk.CTkButton(
            self.btn_frame,
            text="⚡ Hybrid Focus",
            height=38,
            corner_radius=8,
            command=lambda: self.handle_apply_profile("Hybrid Focus")
        )
        self.btn_hybrid.grid(row=0, column=2, padx=4, sticky="ew")

        # Solar & Telemetry Card
        self.solar_card = ctk.CTkFrame(self, corner_radius=12)
        self.solar_card.grid(row=3, column=0, padx=25, pady=6, sticky="ew")
        self.solar_card.grid_columnconfigure((0, 1), weight=1)

        self.solar_title = ctk.CTkLabel(
            self.solar_card,
            text="🌞 Solar Ephemeris Engine (100% Offline)",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.solar_title.grid(row=0, column=0, columnspan=2, pady=(10, 6))

        self.sunrise_label = ctk.CTkLabel(self.solar_card, text="Sunrise: --:-- AM", font=ctk.CTkFont(size=12))
        self.sunrise_label.grid(row=1, column=0, padx=10, pady=2)

        self.sunset_label = ctk.CTkLabel(self.solar_card, text="Sunset: --:-- PM", font=ctk.CTkFont(size=12))
        self.sunset_label.grid(row=1, column=1, padx=10, pady=2)

        self.city_info_label = ctk.CTkLabel(
            self.solar_card,
            text="Location: New Delhi, India",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.city_info_label.grid(row=2, column=0, columnspan=2, pady=(2, 4))

        self.solar_toggle_switch = ctk.CTkSwitch(
            self.solar_card,
            text="Enable Solar Auto-Switch",
            command=self.handle_solar_switch_toggle
        )
        self.solar_toggle_switch.grid(row=3, column=0, columnspan=2, pady=(4, 10))

        # Empirical Benchmark Card
        self.metrics_card = ctk.CTkFrame(self, corner_radius=10)
        self.metrics_card.grid(row=4, column=0, padx=25, pady=6, sticky="ew")
        self.metrics_card.grid_columnconfigure((0, 1, 2), weight=1)

        self.metric_latency_label = ctk.CTkLabel(
            self.metrics_card,
            text="Avg Latency: -- ms",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.metric_latency_label.grid(row=0, column=0, padx=10, pady=8)

        self.metric_count_label = ctk.CTkLabel(
            self.metrics_card,
            text="Switches: --",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.metric_count_label.grid(row=0, column=1, padx=10, pady=8)

        self.metric_ram_label = ctk.CTkLabel(
            self.metrics_card,
            text="Process RSS: -- MB",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.metric_ram_label.grid(row=0, column=2, padx=10, pady=8)

        # Footer
        self.footer_label = ctk.CTkLabel(
            self,
            text="⚡ Low-Level COM IThemeManager2 | Native VTable Dispatch | 0 Explorer Restarts",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.footer_label.grid(row=5, column=0, pady=(6, 10))

        self.refresh_display()

    def refresh_display(self):
        state = ThemeEngine.get_current_theme_state()
        pref = Repository.get_preferences()
        profile_name = state["profile_name"]

        self.theme_display.configure(text=f"{profile_name.upper()}")
        self.theme_detail_label.configure(
            text=f"System (Taskbar): {state['system_theme'].title()}  |  Apps (Chrome/Explorer): {state['apps_theme'].title()}"
        )

        if profile_name == "Full Dark":
            self.theme_display.configure(text_color="#60a5fa")
            self.btn_dark.configure(fg_color="#1d4ed8")
            self.btn_light.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.btn_hybrid.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        elif profile_name == "Full Light":
            self.theme_display.configure(text_color="#f59e0b")
            self.btn_dark.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.btn_light.configure(fg_color="#d97706")
            self.btn_hybrid.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        elif profile_name == "Hybrid Focus":
            self.theme_display.configure(text_color="#10b981")
            self.btn_dark.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.btn_light.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.btn_hybrid.configure(fg_color="#059669")

        # Update solar info
        lat = pref.get("latitude", 28.6139)
        lon = pref.get("longitude", 77.2090)
        city = pref.get("city_name", "New Delhi")
        solar_enabled = pref.get("solar_schedule_enabled", True)

        solar = SolarEngine.get_solar_times(lat=lat, lon=lon, city_name=city)
        self.sunrise_label.configure(text=f"🌅 Sunrise: {solar['sunrise_display']}")
        self.sunset_label.configure(text=f"🌇 Sunset: {solar['sunset_display']}")
        self.city_info_label.configure(text=f"Location: {city} (Lat: {lat:.2f}, Lon: {lon:.2f})")

        if solar_enabled:
            self.solar_toggle_switch.select()
        else:
            self.solar_toggle_switch.deselect()

        # Update empirical metrics
        metrics = Repository.get_empirical_metrics()
        self.metric_latency_label.configure(text=f"⏱️ Avg Latency: {metrics['average_latency_ms']} ms")
        self.metric_count_label.configure(text=f"🔄 Switches: {metrics['total_switches']}")
        self.metric_ram_label.configure(text=f"💾 Memory: {metrics['resident_memory_mb']} MB")

    def handle_apply_profile(self, profile_name):
        ThemeEngine.apply_profile(profile_name, trigger_source="manual_gui")
        self.refresh_display()
        if self.on_theme_switched_callback:
            self.on_theme_switched_callback(ThemeEngine.get_current_theme())

    def handle_solar_switch_toggle(self):
        is_on = bool(self.solar_toggle_switch.get())
        Repository.update_preferences({"solar_schedule_enabled": is_on})
        if self.on_theme_switched_callback:
            self.on_theme_switched_callback(ThemeEngine.get_current_theme())
