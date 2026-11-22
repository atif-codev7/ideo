import datetime
import logging
from typing import Callable, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from core.solar_engine import SolarEngine
from core.theme_engine import ThemeEngine
from database.repository import Repository

logger = logging.getLogger("IDEO.Scheduler")

class SchedulerEngine:
    def __init__(self, on_theme_change_callback: Optional[Callable[[str], None]] = None):
        self.scheduler = BackgroundScheduler(daemon=True)
        self.on_theme_change_callback = on_theme_change_callback
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.refresh_jobs()
            self.scheduler.start()
            self.is_running = True
            logger.info("IDEO Background Scheduler started.")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("IDEO Background Scheduler stopped.")

    def _execute_switch(self, target_theme: str, source: str, profile_id: Optional[int] = None):
        logger.info(f"Executing scheduled theme switch to {target_theme} via {source} (Profile ID: {profile_id})")
        success = ThemeEngine.set_theme(target_theme, trigger_source=source, profile_id=profile_id)
        if success and self.on_theme_change_callback:
            try:
                self.on_theme_change_callback(ThemeEngine.get_current_theme())
            except Exception as e:
                logger.error(f"Error in on_theme_change_callback: {e}")

    def refresh_jobs(self):
        self.scheduler.remove_all_jobs()

        pref = Repository.get_preferences()
        lat = pref.get("latitude", 28.6139)
        lon = pref.get("longitude", 77.2090)
        city = pref.get("city_name", "New Delhi")
        solar_enabled = pref.get("solar_schedule_enabled", True)

        dark_p = Repository.get_profile_by_name("Dark Mode")
        light_p = Repository.get_profile_by_name("Light Mode")

        # 1. Midnight job to refresh daily solar times
        self.scheduler.add_job(
            self.refresh_jobs,
            trigger=CronTrigger(hour=0, minute=1),
            id="daily_midnight_refresh",
            replace_existing=True
        )

        # 2. Add Solar schedules if enabled
        if solar_enabled:
            solar_times = SolarEngine.get_solar_times(lat=lat, lon=lon, city_name=city)
            sunrise_dt = solar_times["sunrise"]
            sunset_dt = solar_times["sunset"]

            # Sunrise -> Light Mode
            self.scheduler.add_job(
                self._execute_switch,
                trigger=CronTrigger(hour=sunrise_dt.hour, minute=sunrise_dt.minute),
                args=["light", "solar_sunrise", light_p["id"] if light_p else None],
                id="solar_sunrise_job",
                replace_existing=True
            )

            # Sunset -> Dark Mode
            self.scheduler.add_job(
                self._execute_switch,
                trigger=CronTrigger(hour=sunset_dt.hour, minute=sunset_dt.minute),
                args=["dark", "solar_sunset", dark_p["id"] if dark_p else None],
                id="solar_sunset_job",
                replace_existing=True
            )

        # 3. Add Custom Schedules from DB with wired profile_id
        schedules = Repository.get_schedules()
        for s in schedules:
            if not s.get("is_active"):
                continue

            stype = s.get("schedule_type")
            target = s.get("target_theme", "dark")
            sid = s.get("id")
            pid = s.get("profile_id")

            if stype == "custom_time" and s.get("custom_time"):
                try:
                    parts = s["custom_time"].split(":")
                    hour = int(parts[0])
                    minute = int(parts[1])
                    self.scheduler.add_job(
                        self._execute_switch,
                        trigger=CronTrigger(hour=hour, minute=minute),
                        args=[target, f"custom_schedule_{sid}", pid],
                        id=f"custom_job_{sid}",
                        replace_existing=True
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse custom schedule time {s.get('custom_time')}: {e}")

    def get_scheduled_jobs(self) -> List[dict]:
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "None",
            })
        return jobs
