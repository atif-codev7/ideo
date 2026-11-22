import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_session import init_db
from database.repository import Repository

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_get_preferences():
    pref = Repository.get_preferences()
    assert pref is not None
    assert "city_name" in pref
    assert "current_theme" in pref
    assert pref["city_name"] == "New Delhi"

def test_update_preferences():
    updated = Repository.update_preferences({"city_name": "Mumbai", "solar_schedule_enabled": False})
    assert updated["city_name"] == "Mumbai"
    assert updated["solar_schedule_enabled"] is False

    # Restore
    Repository.update_preferences({"city_name": "New Delhi", "solar_schedule_enabled": True})

def test_add_and_delete_schedule():
    sched = Repository.add_schedule(
        name="Test Bedtime Dark",
        target_theme="dark",
        schedule_type="custom_time",
        custom_time="23:30"
    )
    assert sched["id"] is not None
    assert sched["custom_time"] == "23:30"

    # Delete
    deleted = Repository.delete_schedule(sched["id"])
    assert deleted is True

def test_toggle_schedule():
    sched = Repository.add_schedule(
        name="Test Morning Light",
        target_theme="light",
        schedule_type="custom_time",
        custom_time="07:00"
    )
    assert sched["is_active"] is True

    toggled = Repository.toggle_schedule(sched["id"], False)
    assert toggled is True

    # Cleanup
    Repository.delete_schedule(sched["id"])

def test_log_switch_and_history():
    log_entry = Repository.log_switch(
        switched_to="dark",
        trigger_source="pytest_test",
        duration_ms=18.5,
        status="SUCCESS"
    )
    assert log_entry["switched_to"] == "dark"
    assert log_entry["trigger_source"] == "pytest_test"
    assert log_entry["execution_duration_ms"] == 18.5

    logs = Repository.get_recent_logs(limit=10)
    assert len(logs) > 0
    assert any(l["trigger_source"] == "pytest_test" for l in logs)
