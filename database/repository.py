from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from database.db_session import SessionLocal
from database.models import UserPreference, Schedule, SwitchLog

def utc_now():
    return datetime.now(timezone.utc)

class Repository:
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

    @staticmethod
    def get_schedules() -> List[Dict[str, Any]]:
        session = SessionLocal()
        try:
            schedules = session.query(Schedule).all()
            return [s.to_dict() for s in schedules]
        finally:
            session.close()

    @staticmethod
    def add_schedule(name: str, target_theme: str, schedule_type: str, custom_time: Optional[str] = None) -> Dict[str, Any]:
        session = SessionLocal()
        try:
            new_schedule = Schedule(
                name=name,
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

    @staticmethod
    def log_switch(switched_to: str, trigger_source: str, duration_ms: float = 0.0, status: str = "SUCCESS") -> Dict[str, Any]:
        session = SessionLocal()
        try:
            log_entry = SwitchLog(
                switched_to=switched_to,
                trigger_source=trigger_source,
                execution_duration_ms=round(duration_ms, 2),
                status=status,
                timestamp=datetime.now()
            )
            session.add(log_entry)

            # Update current_theme in UserPreference as well
            pref = session.query(UserPreference).first()
            if pref:
                pref.current_theme = switched_to
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
