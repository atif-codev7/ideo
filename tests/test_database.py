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

def test_seeded_profiles():
    profiles = Repository.get_profiles()
    names = [p["name"] for p in profiles]
    assert "Full Dark" in names
    assert "Full Light" in names
    assert "Hybrid Focus" in names

def test_create_and_delete_custom_profile():
    p = Repository.create_profile(
        name="Reading Night",
        system_theme="dark",
        apps_theme="light",
        wallpaper_path="C:/wallpapers/night.jpg"
    )
    assert p["id"] is not None
    assert p["name"] == "Reading Night"

    # Delete
    deleted = Repository.delete_profile(p["id"])
    assert deleted is True

def test_prevent_duplicate_profile_name():
    with pytest.raises(ValueError, match="already exists"):
        Repository.create_profile("Full Dark", "dark", "dark")

def test_prevent_invalid_theme_in_profile():
    with pytest.raises(ValueError, match="must be 'dark' or 'light'"):
        Repository.create_profile("Invalid Theme", "blue", "yellow")

def test_schedule_profile_foreign_key():
    dark_p = Repository.get_profile_by_name("Full Dark")
    assert dark_p is not None

    sched = Repository.add_schedule(
        name="Late Night Coding",
        profile_id=dark_p["id"],
        target_theme="Full Dark",
        schedule_type="custom_time",
        custom_time="01:30"
    )
    assert sched["profile_id"] == dark_p["id"]

    # Deleting dark_p should be blocked by business constraint
    with pytest.raises(ValueError, match="actively referenced"):
        Repository.delete_profile(dark_p["id"])

    # Cleanup schedule
    Repository.delete_schedule(sched["id"])

def test_log_switch_and_empirical_metrics():
    dark_p = Repository.get_profile_by_name("Full Dark")
    log_entry = Repository.log_switch(
        switched_to="Full Dark",
        trigger_source="pytest_telemetry",
        duration_ms=42.5,
        status="SUCCESS",
        profile_id=dark_p["id"] if dark_p else None
    )
    assert log_entry["switched_to"] == "Full Dark"
    assert log_entry["execution_duration_ms"] == 42.5

    # Check empirical metrics
    metrics = Repository.get_empirical_metrics()
    assert "average_latency_ms" in metrics
    assert "total_switches" in metrics
    assert "resident_memory_mb" in metrics
    assert isinstance(metrics["average_latency_ms"], float)
    assert isinstance(metrics["total_switches"], int)
    assert isinstance(metrics["resident_memory_mb"], float)
    assert metrics["total_switches"] >= 1
    assert metrics["resident_memory_mb"] > 0.0
