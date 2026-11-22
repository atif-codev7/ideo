import sys
import socket
import threading
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_session import init_db
from core.theme_engine import ThemeEngine
from core.scheduler_engine import SchedulerEngine
from tray.tray_manager import TrayManager
from gui.app import IdeoApp

SINGLE_INSTANCE_PORT = 49285

def try_notify_existing_instance() -> bool:
    """
    Checks if an instance of IDEO is already running.
    If so, sends a 'SHOW' signal to bring its window to the foreground and returns True.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(("127.0.0.1", SINGLE_INSTANCE_PORT))
        s.sendall(b"SHOW\n")
        s.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False

def start_instance_listener(on_show_callback):
    """
    Listens for messages from subsequent launches to show the window.
    """
    def listen():
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
            server.listen(5)
            while True:
                conn, _ = server.accept()
                data = conn.recv(1024).strip()
                if data == b"SHOW":
                    on_show_callback()
                conn.close()
        except Exception:
            pass

    t = threading.Thread(target=listen, daemon=True)
    t.start()

def main():
    # Handle quick command-line toggle flag (0.02s execution)
    if "--toggle" in sys.argv:
        new_theme = ThemeEngine.toggle(trigger_source="hotkey_or_cli")
        print(f"IDEO: Switched to {new_theme.upper()} mode.")
        sys.exit(0)

    # Single-instance check: If already running, focus existing window and exit
    if try_notify_existing_instance():
        sys.exit(0)

    # 1. Initialize SQLite Database & seed defaults
    init_db()

    # 2. Shared references
    app = None
    scheduler = None
    tray = None

    def on_theme_changed(target_theme):
        if app:
            app.after(0, lambda: app.on_theme_switched(target_theme))
        if tray:
            tray.update_state()

    def on_open_gui():
        if app:
            app.after(0, app.show)

    def on_exit_app():
        if scheduler:
            scheduler.stop()
        if app:
            app.after(0, app.destroy)
        sys.exit(0)

    # 3. Start Single-Instance Listener
    start_instance_listener(on_open_gui)

    # 4. Initialize Scheduler Engine
    scheduler = SchedulerEngine(on_theme_change_callback=on_theme_changed)
    scheduler.start()

    # 5. Initialize System Tray Manager
    tray = TrayManager(
        on_toggle_callback=on_theme_changed,
        on_open_gui_callback=on_open_gui,
        on_exit_callback=on_exit_app
    )
    tray.start()

    # 6. Initialize GUI Application
    app = IdeoApp(scheduler_engine=scheduler, tray_manager=tray)

    if "--minimized" in sys.argv:
        app.withdraw()

    # 7. Run Tkinter Main Event Loop
    try:
        app.mainloop()
    except KeyboardInterrupt:
        on_exit_app()

if __name__ == "__main__":
    main()
