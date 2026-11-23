"""
IDEO - Standalone 1-Click System Tray Toggle
Sits directly in the Windows System Tray (next to the clock / ENG IN).
A single click or menu selection instantly toggles Windows Dark/Light mode in 0.02s.
"""

import sys
from pathlib import Path
from PIL import Image
import pystray
from pystray import MenuItem as item, Menu

# Import the core toggle
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from toggle_theme import toggle_theme

ASSETS_DIR = PROJECT_ROOT / "assets"

def get_icon_image():
    icon_path = ASSETS_DIR / "icon_dark.png"
    if icon_path.exists():
        return Image.open(str(icon_path))
    return Image.new("RGBA", (16, 16), (90, 105, 240))

def handle_toggle(icon=None, item=None):
    toggle_theme()

def handle_exit(icon=None, item=None):
    if icon:
        icon.stop()
    sys.exit(0)

def main():
    menu = Menu(
        item("Toggle Theme (0.02s)", handle_toggle, default=True),
        Menu.SEPARATOR,
        item("Exit", handle_exit)
    )

    icon = pystray.Icon(
        "IDEO-InstantToggle",
        get_icon_image(),
        "IDEO Instant Theme Toggle (Click to Switch)",
        menu=menu
    )
    icon.run()

if __name__ == "__main__":
    main()
