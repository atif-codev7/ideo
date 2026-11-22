import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.theme_engine import ThemeEngine
from core.scheduler_engine import SchedulerEngine
from database.repository import Repository

def test_query_theme_state():
    state = ThemeEngine.get_current_theme_state()
    assert "system_theme" in state
    assert "apps_theme" in state
    assert "profile_name" in state
    assert state["system_theme"] in ("dark", "light")
    assert state["apps_theme"] in ("dark", "light")

def test_hybrid_focus_switch():
    # Test setting system=dark, apps=light
    success = ThemeEngine.apply_profile("Hybrid Focus", trigger_source="pytest_hybrid")
    assert success is True

    state = ThemeEngine.get_current_theme_state()
    assert state["system_theme"] == "dark"
    assert state["apps_theme"] == "light"
    assert state["profile_name"] == "Hybrid Focus"

def test_defensive_fallback_execution():
    # Test fallback directly
    fallback_res = ThemeEngine._fallback_registry_switch("dark", "dark")
    assert fallback_res is True

def test_scheduler_init():
    sched = SchedulerEngine()
    assert sched.is_running is False
    sched.start()
    assert sched.is_running is True

    jobs = sched.get_scheduled_jobs()
    assert len(jobs) > 0
    job_ids = [j["id"] for j in jobs]
    assert "daily_midnight_refresh" in job_ids

    sched.stop()
    assert sched.is_running is False

def test_scheduler_with_profile_job():
    light_p = Repository.get_profile_by_name("Full Light")
    assert light_p is not None

    sched_entry = Repository.add_schedule(
        name="Pytest Light Schedule",
        profile_id=light_p["id"],
        target_theme="Full Light",
        schedule_type="custom_time",
        custom_time="08:15"
    )

    sched = SchedulerEngine()
    sched.start()
    jobs = sched.get_scheduled_jobs()
    job_ids = [j["id"] for j in jobs]
    assert f"custom_job_{sched_entry['id']}" in job_ids

    sched.stop()
    Repository.delete_schedule(sched_entry["id"])

def test_restore_state():
    # Restore to Full Dark after test runs
    res = ThemeEngine.apply_profile("Full Dark", trigger_source="pytest_cleanup")
    assert res is True
