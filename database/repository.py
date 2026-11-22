from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import func
import psutil
from database.db_session import SessionLocal
from database.models import UserPreference, Schedule, SwitchLog, ThemeProfile

def utc_now():
    return datetime.now(timezone.utc)

class Repository:
    # --- Profile Operations ---
    @staticmethod
    def get_profiles() -> List[Dict[str, Any]]:
        session = SessionLocal()
        try:
            profiles = session.query(ThemeProfile).all()
            return [p.to_dict() for p in profiles]
        finally:
            session.close()

    @staticmethod
    def get_profile_by_id(profile_id: int) -> Optional[Dict[str, Any]]:
        session = SessionLocal()
        try:
            profile = session.query(ThemeProfile).filter(ThemeProfile.id == profile_id).first()
            return profile.to_dict() if profile else None
        finally:
            session.close()

    @staticmethod
    def get_profile_by_name(name: str) -> Optional[Dict[str, Any]]:
        session = SessionLocal()
        try:
            profile = session.query(ThemeProfile).filter(ThemeProfile.name == name).first()
            return profile.to_dict() if profile else None
        finally:
            session.close()

    @staticmethod
    def create_profile(name: str, system_theme: str, apps_theme: str, wallpaper_path: Optional[str] = None) -> Dict[str, Any]:
        system_theme = system_theme.lower()
        apps_theme = apps_theme.lower()
        if system_theme not in ("dark", "light") or apps_theme not in ("dark", "light"):
            raise ValueError("system_theme and apps_theme must be 'dark' or 'light'")

        session = SessionLocal()
        try:
            existing = session.query(ThemeProfile).filter(ThemeProfile.name == name).first()
            if existing:
                raise ValueError(f"Profile with name '{name}' already exists.")

            new_profile = ThemeProfile(
                name=name,
                system_theme=system_theme,
                apps_theme=apps_theme,
                wallpaper_path=wallpaper_path
            )
            session.add(new_profile)
            session.commit()
            return new_profile.to_dict()
        finally:
            session.close()

    @staticmethod
    def delete_profile(profile_id: int) -> bool:
        session = SessionLocal()
        try:
            # Check if referenced by active schedules
            active_refs = session.query(Schedule).filter(Schedule.profile_id == profile_id).count()
            if active_refs > 0:
                raise ValueError("Cannot delete profile: actively referenced by configured schedules.")

            profile = session.query(ThemeProfile).filter(ThemeProfile.id == profile_id).first()
            if profile:
                session.delete(profile)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # --- Preference Operations ---
    @staticmethod
    def get_preferences() -> Dict[str, Any]:
        session = SessionLocal()
        try:
            pref = session.query(UserPreference).first()
            if not pref:
                pref = UserPreference()
                session.add(pref)
                session.commit()
            return pref.to_dict()
        finally:
            session.close()

    @staticmethod
    def update_preferences(data: Dict[str, Any]) -> Dict[str, Any]:
        session = SessionLocal()
        try:
            pref = session.query(UserPreference).first()
            if not pref:
                pref = UserPreference()
                session.add(pref)

            for key, val in data.items():
                if hasattr(pref, key):
                    setattr(pref, key, val)
            pref.updated_at = utc_now()
            session.commit()
            return pref.to_dict()
        finally:
            session.close()

    # --- Schedule Operations ---
    @staticmethod
    def get_schedules() -> List[Dict[str, Any]]:
        session = SessionLocal()
        try:
            schedules = session.query(Schedule).all()
            return [s.to_dict() for s in schedules]
        finally:
            session.close()

    @staticmethod
    def add_schedule(name: str, profile_id: int, target_theme: str, schedule_type: str, custom_time: Optional[str] = None) -> Dict[str, Any]:
        session = SessionLocal()
        try:
            # Verify profile exists
            profile = session.query(ThemeProfile).filter(ThemeProfile.id == profile_id).first()
            if not profile:
                raise ValueError(f"Target theme profile with id {profile_id} does not exist.")

            new_schedule = Schedule(
                name=name,
                profile_id=profile_id,
                target_theme=target_theme,
                schedule_type=schedule_type,
                custom_time=custom_time,
                is_active=True
            )
            session.add(new_schedule)
            session.commit()
            return new_schedule.to_dict()
        finally:
            session.close()

    @staticmethod
    def toggle_schedule(schedule_id: int, is_active: bool) -> bool:
        session = SessionLocal()
        try:
            schedule = session.query(Schedule).filter(Schedule.id == schedule_id).first()
            if schedule:
                schedule.is_active = is_active
                session.commit()
                return True
            return False
        finally:
            session.close()

    @staticmethod
    def delete_schedule(schedule_id: int) -> bool:
        session = SessionLocal()
        try:
            schedule = session.query(Schedule).filter(Schedule.id == schedule_id).first()
            if schedule:
                session.delete(schedule)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # --- Switch Log & Audit Operations ---
    @staticmethod
    def log_switch(switched_to: str, trigger_source: str, duration_ms: float = 0.0, status: str = "SUCCESS", profile_id: Optional[int] = None) -> Dict[str, Any]:
        session = SessionLocal()
        try:
            log_entry = SwitchLog(
                profile_id=profile_id,
                switched_to=switched_to,
                trigger_source=trigger_source,
                execution_duration_ms=round(duration_ms, 2),
                status=status,
                timestamp=datetime.now()
            )
            session.add(log_entry)

            # Update current_theme in UserPreference
            pref = session.query(UserPreference).first()
            if pref:
                pref.current_theme = switched_to
                if profile_id:
                    pref.active_profile_id = profile_id
                pref.updated_at = utc_now()

            session.commit()
            return log_entry.to_dict()
        finally:
            session.close()

    @staticmethod
    def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
        session = SessionLocal()
        try:
            logs = session.query(SwitchLog).order_by(SwitchLog.timestamp.desc()).limit(limit).all()
            return [l.to_dict() for l in logs]
        finally:
            session.close()

    @staticmethod
    def clear_logs() -> bool:
        session = SessionLocal()
        try:
            session.query(SwitchLog).delete()
            session.commit()
            return True
        finally:
            session.close()

    # --- Empirical Metrics Operations ---
    @staticmethod
    def get_empirical_metrics() -> Dict[str, Any]:
        """
        Calculates honest measured benchmarks from the SQLite database and psutil.
        """
        session = SessionLocal()
        try:
            avg_latency = session.query(
                func.avg(SwitchLog.execution_duration_ms)
            ).filter(SwitchLog.status == "SUCCESS").scalar() or 0.0

            total_switches = session.query(func.count(SwitchLog.id)).scalar() or 0

            # Measure actual Resident Set Size (RSS) memory of current process
            try:
                process = psutil.Process()
                mem_rss_mb = process.memory_info().rss / (1024 * 1024)
            except Exception:
                mem_rss_mb = 0.0

            return {
                "average_latency_ms": round(float(avg_latency), 2),
                "total_switches": int(total_switches),
                "resident_memory_mb": round(float(mem_rss_mb), 2)
            }
        finally:
            session.close()
