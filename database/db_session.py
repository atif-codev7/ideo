import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, UserPreference, Schedule, ThemeProfile

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "ideo.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        # 1. Seed Default Theme Profiles if empty
        profiles = session.query(ThemeProfile).all()
        if not profiles:
            p_dark = ThemeProfile(
                name="Full Dark",
                system_theme="dark",
                apps_theme="dark"
            )
            p_light = ThemeProfile(
                name="Full Light",
                system_theme="light",
                apps_theme="light"
            )
            p_hybrid = ThemeProfile(
                name="Hybrid Focus",
                system_theme="dark",
                apps_theme="light"
            )
            session.add_all([p_dark, p_light, p_hybrid])
            session.commit()

        # Re-fetch profiles for foreign keys
        dark_p = session.query(ThemeProfile).filter_by(name="Full Dark").first()
        light_p = session.query(ThemeProfile).filter_by(name="Full Light").first()

        # 2. Seed Default User Preferences
        pref = session.query(UserPreference).first()
        if not pref:
            pref = UserPreference(
                current_theme="Full Dark",
                active_profile_id=dark_p.id if dark_p else None,
                solar_schedule_enabled=True,
                city_name="New Delhi",
                latitude=28.6139,
                longitude=77.2090,
                minimize_to_tray_on_close=True
            )
            session.add(pref)

        # 3. Seed Default Schedules
        schedules = session.query(Schedule).all()
        if not schedules and dark_p and light_p:
            sunset_schedule = Schedule(
                name="Evening Sunset Auto-Dark",
                profile_id=dark_p.id,
                target_theme="Full Dark",
                schedule_type="solar_sunset",
                custom_time=None,
                is_active=True
            )
            sunrise_schedule = Schedule(
                name="Morning Sunrise Auto-Light",
                profile_id=light_p.id,
                target_theme="Full Light",
                schedule_type="solar_sunrise",
                custom_time=None,
                is_active=True
            )
            session.add_all([sunset_schedule, sunrise_schedule])

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
