from pathlib import Path
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item, Menu
from core.theme_engine import ThemeEngine

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

class TrayManager:
    def __init__(self, on_toggle_callback=None, on_open_gui_callback=None, on_exit_callback=None):
        self.on_toggle_callback = on_toggle_callback
        self.on_open_gui_callback = on_open_gui_callback
        self.on_exit_callback = on_exit_callback
        self.icon = None
        self._thread = None

    def _get_icon_image(self):
        state = ThemeEngine.get_current_theme_state()
        icon_file = "icon_dark.png" if state["is_dark"] else "icon_light.png"
        path = ASSETS_DIR / icon_file
        if path.exists():
            return Image.open(str(path))
        return Image.new("RGBA", (16, 16), (255, 185, 0) if not state["is_dark"] else (90, 105, 240))

    def _create_menu(self):
        state = ThemeEngine.get_current_theme_state()
        current_profile = state["profile_name"]

        return Menu(
            item(f"Active: {current_profile}", lambda: None, enabled=False),
            Menu.SEPARATOR,
            item("🌙 Full Dark", lambda: self._handle_switch_profile("Full Dark")),
            item("☀️ Full Light", lambda: self._handle_switch_profile("Full Light")),
            item("⚡ Hybrid Focus", lambda: self._handle_switch_profile("Hybrid Focus")),
            Menu.SEPARATOR,
            item("🖥️ Open Dashboard", self._handle_open_gui, default=True),
            item("❌ Exit IDEO", self._handle_exit)
        )

    def _handle_switch_profile(self, profile_name):
        ThemeEngine.apply_profile(profile_name, trigger_source="tray_menu")
        self.update_state()
        if self.on_toggle_callback:
            self.on_toggle_callback(ThemeEngine.get_current_theme())

    def _handle_open_gui(self, icon=None, item=None):
        if self.on_open_gui_callback:
            self.on_open_gui_callback()

    def _handle_exit(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        if self.on_exit_callback:
            self.on_exit_callback()

    def update_state(self):
        if self.icon:
            try:
                self.icon.icon = self._get_icon_image()
                self.icon.menu = self._create_menu()
                state = ThemeEngine.get_current_theme_state()
                self.icon.title = f"IDEO — {state['profile_name']}"
            except Exception:
                pass

    def start(self):
        state = ThemeEngine.get_current_theme_state()
        self.icon = pystray.Icon(
            "IDEO",
            self._get_icon_image(),
            f"IDEO — {state['profile_name']}",
            menu=self._create_menu()
        )
        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        if self.icon:
            self.icon.stop()
