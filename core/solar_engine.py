import datetime
from typing import Dict, Any, Optional
from astral import LocationInfo
from astral.sun import sun
import zoneinfo

CITIES = {
    "New Delhi": {"country": "India", "timezone": "Asia/Kolkata", "lat": 28.6139, "lon": 77.2090},
    "Mumbai": {"country": "India", "timezone": "Asia/Kolkata", "lat": 19.0760, "lon": 72.8777},
    "Bengaluru": {"country": "India", "timezone": "Asia/Kolkata", "lat": 12.9716, "lon": 77.5946},
    "Kolkata": {"country": "India", "timezone": "Asia/Kolkata", "lat": 22.5726, "lon": 88.3639},
    "London": {"country": "UK", "timezone": "Europe/London", "lat": 51.5074, "lon": -0.1278},
    "New York": {"country": "USA", "timezone": "America/New_York", "lat": 40.7128, "lon": -74.0060},
    "San Francisco": {"country": "USA", "timezone": "America/Los_Angeles", "lat": 37.7749, "lon": -122.4194},
    "Tokyo": {"country": "Japan", "timezone": "Asia/Tokyo", "lat": 35.6762, "lon": 139.6503},
}

class SolarEngine:
    @staticmethod
    def get_solar_times(
        lat: float = 28.6139,
        lon: float = 77.2090,
        city_name: str = "New Delhi",
        target_date: Optional[datetime.date] = None,
        tz_name: str = "Asia/Kolkata"
    ) -> Dict[str, Any]:
        """
        Calculates exact sunrise and sunset times for given coordinates and date offline.
        """
        if target_date is None:
            target_date = datetime.date.today()

        try:
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            tz = datetime.timezone.utc

        loc = LocationInfo(name=city_name, region="Local", timezone=tz_name, latitude=lat, longitude=lon)
        s = sun(loc.observer, date=target_date, tzinfo=tz)

        sunrise_dt = s["sunrise"]
        sunset_dt = s["sunset"]

        return {
            "date": target_date.isoformat(),
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "sunrise": sunrise_dt,
            "sunset": sunset_dt,
            "sunrise_str": sunrise_dt.strftime("%H:%M"),
            "sunset_str": sunset_dt.strftime("%H:%M"),
            "sunrise_display": sunrise_dt.strftime("%I:%M %p"),
            "sunset_display": sunset_dt.strftime("%I:%M %p")
        }

    @classmethod
    def get_expected_theme(
        cls,
        lat: float = 28.6139,
        lon: float = 77.2090,
        tz_name: str = "Asia/Kolkata"
    ) -> str:
        """
        Determines if current local time is daytime (Light) or nighttime (Dark).
        """
        try:
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            tz = datetime.timezone.utc

        now = datetime.datetime.now(tz)
        solar = cls.get_solar_times(lat, lon, target_date=now.date(), tz_name=tz_name)

        if solar["sunrise"] <= now < solar["sunset"]:
            return "light"
        return "dark"
