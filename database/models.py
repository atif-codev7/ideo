from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)

class ThemeProfile(Base):
    __tablename__ = "theme_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)  # e.g., "Full Dark", "Full Light", "Hybrid Focus"
    system_theme = Column(String(10), nullable=False, default="dark")  # "dark" or "light" (Taskbar / Start)
    apps_theme = Column(String(10), nullable=False, default="dark")    # "dark" or "light" (Windows Apps / Chrome)
    wallpaper_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    schedules = relationship("Schedule", back_populates="profile", cascade="all, delete-orphan")
    switch_logs = relationship("SwitchLog", back_populates="profile")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "system_theme": self.system_theme,
            "apps_theme": self.apps_theme,
            "wallpaper_path": self.wallpaper_path,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_theme = Column(String(20), default="Full Dark")  # Active profile name or status
    active_profile_id = Column(Integer, ForeignKey("theme_profiles.id"), nullable=True)
    solar_schedule_enabled = Column(Boolean, default=True)
    city_name = Column(String(100), default="New Delhi")
    latitude = Column(Float, default=28.6139)
    longitude = Column(Float, default=77.2090)
    minimize_to_tray_on_close = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    active_profile = relationship("ThemeProfile")

    def to_dict(self):
        return {
            "id": self.id,
            "current_theme": self.current_theme,
            "active_profile_id": self.active_profile_id,
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
    profile_id = Column(Integer, ForeignKey("theme_profiles.id"), nullable=False)
    target_theme = Column(String(20), nullable=False)  # Profile target or mode
    schedule_type = Column(String(50), nullable=False)  # "solar_sunrise", "solar_sunset", "custom_time"
    custom_time = Column(String(10), nullable=True)     # "HH:MM" in 24-hr format
    is_active = Column(Boolean, default=True)

    profile = relationship("ThemeProfile", back_populates="schedules")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "profile_id": self.profile_id,
            "target_theme": self.target_theme,
            "schedule_type": self.schedule_type,
            "custom_time": self.custom_time,
            "is_active": self.is_active
        }

class SwitchLog(Base):
    __tablename__ = "switch_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("theme_profiles.id"), nullable=True)
    switched_to = Column(String(30), nullable=False)    # e.g., "Full Dark", "Hybrid Focus", "light"
    trigger_source = Column(String(50), nullable=False) # "manual_gui", "tray_menu", "solar_sunset", etc.
    execution_duration_ms = Column(Float, default=0.0)
    status = Column(String(20), default="SUCCESS")      # "SUCCESS" or "FAILED"
    timestamp = Column(DateTime, default=datetime.now)

    profile = relationship("ThemeProfile", back_populates="switch_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "switched_to": self.switched_to,
            "trigger_source": self.trigger_source,
            "execution_duration_ms": self.execution_duration_ms,
            "status": self.status,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None
        }
