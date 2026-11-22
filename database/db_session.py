import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, UserPreference, Schedule

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
    
    # Seed default user preferences and default schedules if empty
    session = SessionLocal()
    try:
        pref = session.query(UserPreference).first()
        if not pref:
            pref = UserPreference(
                current_theme="dark",
                solar_schedule_enabled=True,
                city_name="New Delhi",
                latitude=28.6139,
                longitude=77.2090,
                minimize_to_tray_on_close=True
            )
            session.add(pref)
        
        # Seed default schedules
        schedules = session.query(Schedule).all()
        if not schedules:
            sunset_schedule = Schedule(
                name="Evening Sunset Auto-Dark",
                target_theme="dark",
                schedule_type="solar_sunset",
                custom_time=None,
                is_active=True
            )
            sunrise_schedule = Schedule(
                name="Morning Sunrise Auto-Light",
                target_theme="light",
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
