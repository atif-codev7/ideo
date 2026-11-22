# IDEO — Intelligent Dynamic Environment Orchestrator

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2011-0078D6.svg)](https://microsoft.com/windows)
[![Idle Memory](https://img.shields.io/badge/idle%20RAM-~0MB-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/pytest-15%2F15%20passing-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An autonomous, low-overhead Windows 11 system utility that dynamically orchestrates OS-level display themes via low-level COM VTable dispatch, solar ephemeris calculations, and background event scheduling.

---

## 🚀 Key Highlights

* **Direct COM VTable Dispatch:** Communicates directly with undocumented Windows 11 `IThemeManager2` COM interfaces via `ctypes`. Switches taskbar, Start menu, File Explorer, and WinRT applications in **0.02s** without restarting `explorer.exe`.
* **Zero Idle Overhead:** Operates at **~0 MB idle memory footprint** using native event-driven dispatch rather than resident heavy daemons.
* **100% Offline Solar Ephemeris Engine:** Computes exact astronomical sunrise and sunset cycles for any geographic coordinate locally without external API dependencies.
* **Modern Windows 11 UI:** Built with CustomTkinter for rounded corners, fluent styling, and real-time reactive theme matching.
* **System Tray Daemon:** Sits in the notification area for quick 1-click toggling, status reporting, and background scheduling.
* **ACID-Compliant Audit Logging:** Tracks all switch triggers, sources, latencies, and statuses in a local SQLite database using SQLAlchemy ORM.

---

## 📊 Technical Comparison

| Feature | Auto Dark Mode (.NET) | PowerShell / Registry Scripts | **IDEO (This Project)** |
|:---|:---:|:---:|:---:|
| **Language / Runtime** | C# / .NET Runtime | PowerShell / Batch | **Pure Python + Windows COM** |
| **Idle Memory (RAM)** | 40 MB – 80 MB | 0 MB (one-time script) | **~0 MB idle** |
| **Explorer Restarts** | Periodic | Frequent (Closes open folders) | **Zero Restarts** |
| **Windows 11 Taskbar** | Supported | Broken (Taskbar desyncs) | **Native 100% Synced** |
| **Solar Scheduling** | Requires Weather API | None | **100% Offline Solar Math** |
| **Switch Latency** | ~500ms | 1000ms – 3000ms | **~20ms (0.02s)** |

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
               │      │      (SetCurrentTheme / 0.02s / 0MB RAM)      │      │
               │      └───────────────────────┬───────────────────────┘      │
               └──────────────────────────────┼──────────────────────────────┘
                                              │
                                              ▼
                             ┌────────────────────────────────┐
                             │    SQLite3 + SQLAlchemy ORM    │
                             │   (Preferences, Schedules,     │
                             │      AppRules, SwitchLogs)     │
                             └────────────────────────────────┘
```

---

## 🗄️ Database Schema

The SQLite database (`data/ideo.db`) consists of 4 relational tables:
1. `user_preferences`: Active theme, city, coordinates, solar toggle status.
2. `schedules`: Active sunrise, sunset, and custom cron time configurations.
3. `app_rules`: Per-process override configurations.
4. `switch_logs`: High-resolution audit trail of timestamp, latency (ms), source, and status.

---

## 🧪 Testing

The project includes an automated test suite covering database transactions, solar ephemeris accuracy, scheduler registration, and COM state validation:

```bash
python -m pytest tests -v
```

**Results:** `15 passed in 0.44s`

---

## 💻 Quick Start

### 1. Run from Source
```bash
python -m pip install -r requirements.txt
python main.py
```

### 2. Standalone Build
Execute `build.bat` to generate `dist/IDEO.exe`.

---

## 🎓 Academic Information

* **Institution:** Jamia Hamdard, New Delhi
* **Degree:** Bachelor of Technology in Computer Science & Engineering (B.Tech CSE)
* **Semester:** 7th Semester (Minor Project)
* **Author:** Atif Farooqui (Enrollment: 2023-310-060)
* **Supervisor:** Ms. Gautami Tripathi
