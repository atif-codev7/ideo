# IDEO — Intelligent Dynamic Environment Orchestrator

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2011-0078D6.svg)](https://microsoft.com/windows)
[![Architecture](https://img.shields.io/badge/architecture-COM%20VTable-blueviolet.svg)]()
[![Tests](https://img.shields.io/badge/pytest-15%2F15%20passing-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An autonomous Windows 11 system utility that dynamically orchestrates OS-level display themes via low-level COM VTable dispatch, offline solar ephemeris calculations, and background event scheduling.

---

## 🚀 Key Highlights

* **Direct COM VTable Dispatch:** Communicates directly with Windows 11's internal `IThemeManager2` COM interface via `ctypes`. Switches taskbar, Start menu, File Explorer, and WinRT applications silently and reliably without restarting `explorer.exe`.
* **Dual Execution Modes:**
  * **One-Shot CLI Toggle (`--toggle`):** Instant switch that exits immediately upon completion, leaving zero resident background footprint.
  * **Background Tray Service:** Sits in the notification area with a CustomTkinter dashboard for real-time solar scheduling and manual overrides.
* **100% Offline Solar Ephemeris Engine:** Computes exact astronomical sunrise and sunset cycles for any geographic coordinate locally (`astral`), requiring zero external API keys or network connectivity.
* **Modern Windows 11 UI:** Built with CustomTkinter for rounded corners, fluent styling, and real-time reactive theme matching.
* **Persistent SQLite Audit Trail:** Records theme transitions, trigger sources (GUI, system tray, solar scheduler, custom cron), execution latencies, and statuses in a local SQLite database using SQLAlchemy ORM.

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
               │      │        Windows COM Interop (ctypes)           │      │
               │      │  CLSID_ThemeManager2 -> IThemeManager2 VTable │      │
               │      │            (SetCurrentTheme Dispatch)         │      │
               │      └───────────────────────┬───────────────────────┘      │
               └──────────────────────────────┼──────────────────────────────┘
                                              │
                                              ▼
                             ┌────────────────────────────────┐
                             │    SQLite3 + SQLAlchemy ORM    │
                             │   (Preferences, Schedules,     │
                             │          SwitchLogs)           │
                             └────────────────────────────────┘
```

---

## 🗄️ Relational Database Schema

The SQLite database (`data/ideo.db`) consists of 3 relational models:
1. **`user_preferences`**: Stores active theme, configured city, geographic coordinates, and solar schedule toggle status.
2. **`schedules`**: Manages configured switch times (solar sunrise, solar sunset, or custom 24-hr cron formats).
3. **`switch_logs`**: Comprehensive audit log recording timestamp, latency (ms), trigger source, and execution status.

---

## 🧪 Testing

The project includes an automated test suite verifying database transactions, solar ephemeris accuracy, scheduler registration, and COM state validation:

```bash
python -m pytest tests -v
```

**Test Status:** `15 passed in 0.74s`

---

## 💻 Quick Start

### 1. Run from Source
```bash
python -m pip install -r requirements.txt
python main.py
```

### 2. Standalone Build
Execute `build.bat` to package into a standalone binary (`dist/IDEO.exe`) via PyInstaller.

---

## 👨‍💻 Project Information

* **Author:** Atif Farooqui
* **Program:** Bachelor of Technology in Computer Science & Engineering (B.Tech CSE)
* **Institution:** Jamia Hamdard, New Delhi
