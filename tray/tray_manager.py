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
        theme = ThemeEngine.get_current_theme()
        icon_file = "icon_dark.png" if theme == "dark" else "icon_light.png"
        path = ASSETS_DIR / icon_file
        if path.exists():
            return Image.open(str(path))
        return Image.new("RGBA", (16, 16), (255, 185, 0) if theme == "light" else (90, 105, 240))

    def _create_menu(self):
        theme = ThemeEngine.get_current_theme()
        toggle_title = "☀️ Switch to Light Mode" if theme == "dark" else "🌙 Switch to Dark Mode"

        return Menu(
            item(f"Current: {theme.title()} Mode", lambda: None, enabled=False),
            item(toggle_title, self._handle_toggle, default=True),
            Menu.SEPARATOR,
            item("🖥️ Open Dashboard", self._handle_open_gui),
            item("❌ Exit IDEO", self._handle_exit)
        )

    def _handle_toggle(self, icon=None, item=None):
        new_theme = ThemeEngine.toggle(trigger_source="tray_menu")
        self.update_state()
        if self.on_toggle_callback:
            self.on_toggle_callback(new_theme)

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
                theme = ThemeEngine.get_current_theme().title()
                self.icon.title = f"IDEO — {theme} Mode"
            except Exception:
                pass

    def start(self):
        theme = ThemeEngine.get_current_theme().title()
        self.icon = pystray.Icon(
            "IDEO",
            self._get_icon_image(),
            f"IDEO — {theme} Mode",
            menu=self._create_menu()
        )
        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        if self.icon:
            self.icon.stop()
