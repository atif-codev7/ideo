# IDEO — Intelligent Dynamic Environment Orchestrator

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2011-0078D6.svg)](https://microsoft.com/windows)
[![Architecture](https://img.shields.io/badge/architecture-COM%20VTable%20%2B%20Fallback-blueviolet.svg)]()
[![Tests](https://img.shields.io/badge/pytest-17%2F17%20passing-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An autonomous Windows 11 system utility that dynamically orchestrates OS-level display themes via low-level COM VTable dispatch, defensive registry fallback, offline solar ephemeris calculations, and relational environment profiles.

---

## 🚀 Key Highlights

* **Direct COM VTable Dispatch with Defensive Fallback:** Communicates directly with Windows 11's internal `IThemeManager2` COM interface via `ctypes`. If running in restricted or modified environments, it gracefully falls back to Windows registry configuration and `WM_SETTINGCHANGE` broadcast notification.
* **Dual Execution Modes:**
  * **Full Application Suite (`main.py`):** Full CustomTkinter dashboard, relational SQLite database, automated solar ephemeris scheduler, and system tray integration.
  * **Standalone Zero-Dependency Script (`scripts/toggle_theme.py`):** A pure Python standard-library script that executes the COM VTable switch in **0.02s** and exits immediately, leaving **0 MB idle background RAM**.
  * **Instant System Tray Switcher (`scripts/instant_tray.py`):** Sits directly in the notification area (next to `ENG IN` / clock) for 1-click theme flipping.
* **100% Offline Solar Ephemeris Engine:** Computes exact astronomical sunrise and sunset cycles for any geographic coordinate locally (`astral`), requiring zero external API keys or network connectivity.
* **Empirical Performance Telemetry:** Continuously tracks live resident memory consumption (`psutil`) and queries SQLite for real measured switch latency across all logged events.

---

## 🏗️ Architecture

```
                               ┌────────────────────────────────┐
                               │       User Interactions        │
                               └───────┬───────────────┬────────┘
                                       │               │
                     Tray Right-Click  ▼               ▼  Dashboard (CustomTkinter)
                       ┌───────────────────┐       ┌──────────────────────┐
                       │   pystray Daemon  │       │      GUI Window      │
                       └─────────┬─────────┘       └──────────┬───────────┘
                                 │                            │
                                 ▼                            ▼
               ┌─────────────────────────────────────────────────────────────┐
               │                        IDEO Core Engine                     │
               │                                                             │
               │  ┌───────────────────────┐       ┌───────────────────────┐  │
               │  │  Solar Engine (astral)│       │  APScheduler (Daemon) │  │
               │  └───────────┬───────────┘       └───────────┬───────────┘  │
               │              │                               │              │
               │              ▼                               ▼              │
               │      ┌───────────────────────────────────────────────┐      │
               │      │  Primary: COM VTable (IThemeManager2 ctypes)  │      │
               │      │  Fallback: Registry + WM_SETTINGCHANGE        │      │
               │      └───────────────────────┬───────────────────────┘      │
               └──────────────────────────────┼──────────────────────────────┘
                                              │
                                              ▼
                             ┌────────────────────────────────┐
                             │    SQLite3 + SQLAlchemy ORM    │
                             │  theme_profiles (1) -> (N)     │
                             │     [schedules, switch_logs]   │
                             └────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
ideo/
├── main.py                     # Full application entry point (GUI + Tray + Scheduler)
├── core/
│   ├── theme_engine.py         # COM VTable IThemeManager2 + defensive fallback
│   ├── solar_engine.py         # 100% offline sunrise/sunset ephemeris math
│   └── scheduler_engine.py     # Background APScheduler daemon
├── database/
│   ├── models.py               # Relational SQLAlchemy models with Foreign Keys
│   ├── db_session.py           # SQLite connection factory & seeders
│   └── repository.py           # CRUD operations & empirical performance metrics
├── gui/
│   ├── app.py                  # CustomTkinter modern desktop window
│   └── tabs/                   # Dashboard, automated scheduler, and audit logs
├── scripts/
│   ├── toggle_theme.py         # Standalone zero-dependency 0.02s toggle (0 MB idle RAM)
│   ├── instant_tray.py         # Standalone 1-click tray switcher next to clock/ENG IN
│   └── create_desktop_shortcut.bat  # Creates desktop shortcut with Ctrl+Alt+T
├── tests/                      # 17 automated pytest test cases
└── build.bat                   # 1-click PyInstaller standalone .exe compiler
```

---

## 🗄️ Relational Database Schema (ER Diagram)

The SQLite database (`data/ideo.db`) enforces relational integrity across 4 models:

1. **`theme_profiles` (Primary Entity):**
   * Stores profile presets (`Dark Mode`, `Light Mode`, and custom entries).
   * Defines target `base_theme` ('dark' or 'light') and optional custom wallpaper pairing.
   * **Relationships:**
     * `theme_profiles (1)` ➔ `schedules (N)` (Foreign Key with orphan deletion cascade).
     * `theme_profiles (1)` ➔ `switch_logs (N)` (Foreign Key tracking profile switches).
2. **`user_preferences`:** Stores active profile reference, configured city, geographic coordinates, and solar schedule status.
3. **`schedules`:** Manages configured profile switch times (solar sunrise, solar sunset, or custom 24-hr cron formats).
4. **`switch_logs`:** High-resolution audit log recording timestamp, latency (ms), trigger source, and execution status.

---

## 🧪 Testing

The automated test suite verifies profile constraints, foreign key referential integrity, solar ephemeris accuracy, scheduler registration, and COM/fallback execution:

```bash
python -m pytest tests -v
```

**Test Status:** `17 passed in 1.39s`

---

## 💻 Quick Start

### 1. Run Full Application (Dashboard + Scheduler + Tray)
```bash
python -m pip install -r requirements.txt
python main.py
```

### 2. Run Standalone Instant Toggle (Zero Dependencies, 0 MB Idle RAM)
```bash
python scripts/toggle_theme.py
```
*(Or run `scripts/create_desktop_shortcut.bat` to add a `Ctrl+Alt+T` desktop icon).*

### 3. Standalone Build
Execute `build.bat` to package into a standalone binary (`dist/IDEO.exe`) via PyInstaller.

---

## 👨‍💻 Project Information

* **Author:** Atif Farooqui
* **Program:** Bachelor of Technology in Computer Science & Engineering (B.Tech CSE)
* **Institution:** Jamia Hamdard, New Delhi
