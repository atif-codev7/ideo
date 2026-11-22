from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_theme = Column(String(10), default="dark")  # "dark" or "light"
    solar_schedule_enabled = Column(Boolean, default=True)
    city_name = Column(String(100), default="New Delhi")
    latitude = Column(Float, default=28.6139)
    longitude = Column(Float, default=77.2090)
    minimize_to_tray_on_close = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "current_theme": self.current_theme,
            "solar_schedule_enabled": self.solar_schedule_enabled,
            "city_name": self.city_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "minimize_to_tray_on_close": self.minimize_to_tray_on_close,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    target_theme = Column(String(10), nullable=False)  # "dark" or "light"
    schedule_type = Column(String(50), nullable=False)  # "solar_sunrise", "solar_sunset", "custom_time"
    custom_time = Column(String(10), nullable=True)     # "HH:MM" in 24-hr format
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "target_theme": self.target_theme,
            "schedule_type": self.schedule_type,
            "custom_time": self.custom_time,
            "is_active": self.is_active
        }

class AppRule(Base):
    __tablename__ = "app_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    process_name = Column(String(100), nullable=False)  # e.g., "code.exe"
    enforce_theme = Column(String(10), default="dark")  # "dark", "light", "system"
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "process_name": self.process_name,
            "enforce_theme": self.enforce_theme,
            "is_active": self.is_active
        }

class SwitchLog(Base):
    __tablename__ = "switch_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    switched_to = Column(String(10), nullable=False)    # "dark" or "light"
    trigger_source = Column(String(50), nullable=False) # "manual_gui", "tray_menu", "solar_sunset", "solar_sunrise", "hotkey"
    execution_duration_ms = Column(Float, default=0.0)
    status = Column(String(20), default="SUCCESS")      # "SUCCESS" or "FAILED"
    timestamp = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "switched_to": self.switched_to,
            "trigger_source": self.trigger_source,
            "execution_duration_ms": self.execution_duration_ms,
            "status": self.status,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None
        }
