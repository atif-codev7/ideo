import pytest
import datetime
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.solar_engine import SolarEngine, CITIES

def test_delhi_solar_calculation():
    times = SolarEngine.get_solar_times(lat=28.6139, lon=77.2090, city_name="New Delhi")
    assert "sunrise" in times
    assert "sunset" in times
    assert isinstance(times["sunrise"], datetime.datetime)
    assert isinstance(times["sunset"], datetime.datetime)

def test_sunrise_precedes_sunset():
    times = SolarEngine.get_solar_times(lat=28.6139, lon=77.2090)
    assert times["sunrise"] < times["sunset"]

def test_cities_directory():
    assert "New Delhi" in CITIES
    assert "Mumbai" in CITIES
    assert "London" in CITIES
    delhi = CITIES["New Delhi"]
    assert delhi["lat"] == 28.6139
    assert delhi["lon"] == 77.2090

def test_expected_theme_format():
    theme = SolarEngine.get_expected_theme(lat=28.6139, lon=77.2090)
    assert theme in ("dark", "light")

def test_custom_date_solar():
    summer_date = datetime.date(2026, 6, 21)  # Summer solstice
    times = SolarEngine.get_solar_times(lat=28.6139, lon=77.2090, target_date=summer_date)
    assert times["date"] == "2026-06-21"
    # In Delhi summer, sunset is after 19:00
    assert times["sunset"].hour >= 19
