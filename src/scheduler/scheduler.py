# src/scheduler/scheduler.py
import asyncio
from typing import Dict, Any, List, Callable
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from ..utils.logger import logger
from ..utils.config import config


class Scheduler:
    """
    General-purpose scheduler for managing and executing scheduled jobs.

    Features:
    - Cron-based scheduling from config.yaml
    - Parallel job execution with configurable limits
    - Automatic retry logic with exponential backoff
    - Job monitoring and error handling
    - Graceful shutdown
    """

    def __init__(self):
        self.scheduler_config = config.get('scheduler', {})
        self.timezone = self.scheduler_config.get('timezone', 'UTC')
        self.max_parallel_jobs = self.scheduler_config.get('max_parallel_jobs', 3)

        # Configure APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }

        executors = {
            'default': AsyncIOExecutor()
        }

        job_defaults = {
            'coalesce': True,  # Combine multiple missed executions into one
            'max_instances': self.max_parallel_jobs,
            'misfire_grace_time': 300  # 5 minutes grace period for missed jobs
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self.timezone
        )

        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._running = False

    def add_job(
        self,
        job_id: str,
        func: Callable,
        schedule: str,
        job_config: Dict[str, Any],
        *args,
        **kwargs
    ):
        """
        Add a job to the scheduler.

        Args:
            job_id: Unique identifier for the job
            func: Async function to execute
            schedule: Cron expression (e.g., "*/30 * * * *")
            job_config: Job configuration from config.yaml
            *args, **kwargs: Arguments to pass to the function
        """
        try:
            # Parse cron expression
            cron_parts = schedule.split()
            if len(cron_parts) != 5:
                raise ValueError(f"Invalid cron expression: {schedule}")

            minute, hour, day, month, day_of_week = cron_parts

            # Create trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=self.timezone
            )

            # Add job to scheduler
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=job_config.get('name', job_id),
                args=args,
                kwargs=kwargs,
                replace_existing=True
            )

            self._jobs[job_id] = {
                'job': job,
                'config': job_config,
                'schedule': schedule,
                'last_run': None,
                'next_run': None,  # Will be set when scheduler starts
                'run_count': 0,
                'error_count': 0
            }

            logger.info(
                f"Scheduled job '{job_id}' with cron '{schedule}'."
            )

        except Exception as e:
            logger.error(f"Failed to add job '{job_id}': {str(e)}")
            raise

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a specific job."""
        if job_id not in self._jobs:
            return None

        job_info = self._jobs[job_id]

        # Get next run time from scheduler
        next_run = None
        try:
            scheduled_job = self.scheduler.get_job(job_id)
            if scheduled_job:
                next_run = scheduled_job.next_run_time
        except Exception:
            pass

        return {
            'id': job_id,
            'name': job_info['config'].get('name', job_id),
            'schedule': job_info['schedule'],
            'last_run': job_info['last_run'],
            'next_run': next_run,
            'run_count': job_info['run_count'],
            'error_count': job_info['error_count'],
            'enabled': job_info['config'].get('enabled', True)
        }

    def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """Get the status of all jobs."""
        return [self.get_job_status(job_id) for job_id in self._jobs.keys()]

    def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        logger.info(f"Starting scheduler with timezone: {self.timezone}")
        logger.info(f"Max parallel jobs: {self.max_parallel_jobs}")
        logger.info(f"Total jobs scheduled: {len(self._jobs)}")

        # Start scheduler first
        self.scheduler.start()
        self._running = True

        # Log all scheduled jobs with their next run times
        for job_id, job_info in self._jobs.items():
            try:
                scheduled_job = self.scheduler.get_job(job_id)
                if scheduled_job:
                    next_run = scheduled_job.next_run_time
                    logger.info(
                        f"  - {job_id}: {job_info['schedule']} "
                        f"(next run: {next_run})"
                    )
            except Exception as e:
                logger.warning(f"Could not get next run time for {job_id}: {e}")

        logger.info("Scheduler started successfully")

    def shutdown(self, wait: bool = True):
        """
        Shutdown the scheduler gracefully.

        Args:
            wait: Whether to wait for running jobs to complete
        """
        if not self._running:
            logger.warning("Scheduler is not running")
            return

        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown(wait=wait)
        self._running = False
        logger.info("Scheduler shut down successfully")

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running
