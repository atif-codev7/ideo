import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.theme_engine import ThemeEngine
from core.scheduler_engine import SchedulerEngine
from database.repository import Repository

def test_query_current_theme():
    theme = ThemeEngine.get_current_theme()
    assert theme in ("dark", "light")

def test_theme_invalid_input():
    with pytest.raises(ValueError):
        ThemeEngine.set_theme("invalid_theme_color")

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

def test_scheduler_with_custom_job():
    # Add a temporary custom schedule in DB
    sched_entry = Repository.add_schedule(
        name="Pytest Custom 14:00",
        target_theme="dark",
        schedule_type="custom_time",
        custom_time="14:00"
    )

    sched = SchedulerEngine()
    sched.start()
    jobs = sched.get_scheduled_jobs()
    job_ids = [j["id"] for j in jobs]
    assert f"custom_job_{sched_entry['id']}" in job_ids

    sched.stop()
    # Cleanup DB
    Repository.delete_schedule(sched_entry["id"])

def test_theme_engine_state_consistency():
    current = ThemeEngine.get_current_theme()
    # Setting same theme returns True without error
    res = ThemeEngine.set_theme(current, trigger_source="pytest_consistency")
    assert res is True
