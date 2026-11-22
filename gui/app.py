from pathlib import Path
import customtkinter as ctk
from gui.tabs.home_tab import HomeTab
from gui.tabs.schedule_tab import ScheduleTab
from gui.tabs.history_tab import HistoryTab
from core.theme_engine import ThemeEngine
from database.repository import Repository

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

class IdeoApp(ctk.CTk):
    def __init__(self, scheduler_engine=None, tray_manager=None):
        super().__init__()

        self.scheduler_engine = scheduler_engine
        self.tray_manager = tray_manager

        # Window Setup
        self.title("IDEO — Intelligent Dynamic Environment Orchestrator")
        self.geometry("740x550")
        self.minsize(680, 500)

        # Set Window Icon
        icon_path = ASSETS_DIR / "icon_dark.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Configure Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sync appearance mode
        self.sync_appearance()

        # Left Sidebar for Navigation
        self.sidebar = ctk.CTkFrame(self, width=170, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🌗 IDEO",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(25, 20))

        self.btn_home = ctk.CTkButton(
            self.sidebar,
            text="Dashboard",
            height=36,
            corner_radius=8,
            command=lambda: self.select_tab("home")
        )
        self.btn_home.grid(row=1, column=0, padx=15, pady=8, sticky="ew")

        self.btn_schedule = ctk.CTkButton(
            self.sidebar,
            text="Scheduler",
            height=36,
            corner_radius=8,
            command=lambda: self.select_tab("schedule")
        )
        self.btn_schedule.grid(row=2, column=0, padx=15, pady=8, sticky="ew")

        self.btn_history = ctk.CTkButton(
            self.sidebar,
            text="Switch Logs",
            height=36,
            corner_radius=8,
            command=lambda: self.select_tab("history")
        )
        self.btn_history.grid(row=3, column=0, padx=15, pady=8, sticky="ew")

        # Sidebar Footer
        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="v1.0 • B.Tech Minor\nJamia Hamdard",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.version_label.grid(row=5, column=0, padx=10, pady=15)

        # Content Frame
        self.content_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # Initialize Tabs
        self.tab_home = HomeTab(self.content_container, on_theme_switched_callback=self.on_theme_switched)
        self.tab_schedule = ScheduleTab(self.content_container, on_schedule_changed_callback=self.on_schedule_changed)
        self.tab_history = HistoryTab(self.content_container)

        self.select_tab("home")

        # Bring window to foreground on launch
        self.lift()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.focus_force()

        # Intercept Window Close to minimize to tray
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def sync_appearance(self):
        current_theme = ThemeEngine.get_current_theme()
        ctk.set_appearance_mode(current_theme)

    def select_tab(self, tab_name):
        self.tab_home.grid_forget()
        self.tab_schedule.grid_forget()
        self.tab_history.grid_forget()

        # Reset button styles
        for btn in (self.btn_home, self.btn_schedule, self.btn_history):
            btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])

        if tab_name == "home":
            self.tab_home.grid(row=0, column=0, sticky="nsew")
            self.tab_home.refresh_display()
            self.btn_home.configure(fg_color=["#2563EB", "#1D4ED8"])
        elif tab_name == "schedule":
            self.tab_schedule.grid(row=0, column=0, sticky="nsew")
            self.tab_schedule.refresh()
            self.btn_schedule.configure(fg_color=["#2563EB", "#1D4ED8"])
        elif tab_name == "history":
            self.tab_history.grid(row=0, column=0, sticky="nsew")
            self.tab_history.refresh()
            self.btn_history.configure(fg_color=["#2563EB", "#1D4ED8"])

    def on_theme_switched(self, new_theme):
        self.sync_appearance()
        self.tab_home.refresh_display()
        self.tab_history.refresh()
        if self.tray_manager:
            self.tray_manager.update_state()

    def on_schedule_changed(self):
        if self.scheduler_engine:
            self.scheduler_engine.refresh_jobs()
        self.tab_home.refresh_display()

    def show(self):
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def on_close(self):
        pref = Repository.get_preferences()
        if pref.get("minimize_to_tray_on_close", True):
            self.withdraw()  # Hide window to tray
        else:
            self.quit()
