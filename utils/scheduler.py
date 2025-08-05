"""
Scheduler module for the Telegram Task Bot.
This module handles scheduling of periodic tasks like weekly task reset and statistics generation.
"""

import logging
import datetime
from typing import Callable, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from pytz import timezone

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Scheduler for periodic tasks."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_jobstore(MemoryJobStore(), 'default')
        self.moscow_tz = timezone('Europe/Moscow')  # UTC+3
        self.jobs = {}
    
    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")
    
    def schedule_weekly_task_reset(self, task_reset_func: Callable[[], None]):
        """Schedule weekly task reset on Monday at 00:00 UTC+3.
        
        Args:
            task_reset_func: Function to call for task reset.
        """
        # Schedule for Monday at 00:00 Moscow time (UTC+3)
        trigger = CronTrigger(day_of_week='mon', hour=0, minute=0, timezone=self.moscow_tz)
        
        job = self.scheduler.add_job(
            task_reset_func,
            trigger=trigger,
            id='weekly_task_reset',
            replace_existing=True,
            name='Weekly Task Reset'
        )
        
        self.jobs['weekly_task_reset'] = job
        logger.info("Scheduled weekly task reset for Monday at 00:00 UTC+3")
    
    def schedule_weekly_stats_generation(self, stats_generation_func: Callable[[], None]):
        """Schedule weekly statistics generation on Friday at 17:00 UTC+3.
        
        Args:
            stats_generation_func: Function to call for statistics generation.
        """
        # Schedule for Friday at 17:00 Moscow time (UTC+3)
        trigger = CronTrigger(day_of_week='fri', hour=17, minute=0, timezone=self.moscow_tz)
        
        job = self.scheduler.add_job(
            stats_generation_func,
            trigger=trigger,
            id='weekly_stats_generation',
            replace_existing=True,
            name='Weekly Statistics Generation'
        )
        
        self.jobs['weekly_stats_generation'] = job
        logger.info("Scheduled weekly statistics generation for Friday at 17:00 UTC+3")
    
    def get_next_run_time(self, job_id: str) -> datetime.datetime:
        """Get the next run time for a scheduled job.
        
        Args:
            job_id: ID of the job.
            
        Returns:
            Next run time as a datetime object.
        """
        if job_id in self.jobs:
            return self.jobs[job_id].next_run_time
        return None
    
    def get_all_jobs_info(self) -> Dict[str, Any]:
        """Get information about all scheduled jobs.
        
        Returns:
            Dictionary with job information.
        """
        result = {}
        for job_id, job in self.jobs.items():
            result[job_id] = {
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            }
        return result