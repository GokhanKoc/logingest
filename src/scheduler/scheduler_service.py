# src/scheduler/scheduler_service.py
import asyncio
from typing import Dict, Any, List
from ..utils.logger import logger
from ..utils.config import config
from ..database.connection import DatabaseConnection
from ..services import ServiceFactory
from .scheduler import Scheduler


class SchedulerService:
    """
    Service that manages scheduled execution of data ingestion services.

    This service:
    - Loads service configurations from config.yaml
    - Schedules each service according to its cron expression
    - Manages service execution, data fetching, and storage
    - Handles errors and retries
    """

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.scheduler = Scheduler()
        self.services = {}

    def initialize_services(self):
        """
        Initialize all services from configuration and schedule them.
        """
        logger.info("Initializing scheduler service")

        sources_config = config.get('sources', [])

        if not sources_config:
            logger.warning("No sources configured in config.yaml")
            return

        for service_config in sources_config:
            service_name = service_config.get('name', 'unknown')

            # Check if service is enabled
            if not service_config.get('enabled', True):
                logger.info(f"Skipping disabled service: {service_name}")
                continue

            # Validate schedule
            schedule = service_config.get('schedule')
            if not schedule:
                logger.warning(
                    f"Service '{service_name}' has no schedule configured, skipping"
                )
                continue

            try:
                # Create service instance
                service = ServiceFactory.from_config(service_config)
                self.services[service_name] = {
                    'instance': service,
                    'config': service_config
                }

                # Schedule the service
                self.scheduler.add_job(
                    job_id=service_name,
                    func=self._execute_service,
                    schedule=schedule,
                    job_config=service_config,
                    service_name=service_name
                )

                logger.info(
                    f"Scheduled service '{service_name}' with cron '{schedule}'"
                )

            except Exception as e:
                logger.error(
                    f"Failed to initialize service '{service_name}': {str(e)}",
                    exc_info=True
                )

    async def _execute_service(self, service_name: str):
        """
        Execute a single service: fetch data, transform, and store.

        Args:
            service_name: Name of the service to execute
        """
        if service_name not in self.services:
            logger.error(f"Service '{service_name}' not found")
            return

        service_info = self.services[service_name]
        service = service_info['instance']
        service_config = service_info['config']

        logger.info(f"Executing service: {service_name}")

        try:
            # Fetch data from the service
            logger.debug(f"Fetching data from {service_name}")
            data = await service.fetch_data()

            if not data:
                logger.warning(f"No data received from {service_name}")
                return

            # Transform the data
            logger.debug(f"Transforming data from {service_name}")
            log_entries = service.transform(data)

            if not log_entries:
                logger.warning(f"No log entries generated from {service_name}")
                return

            # Store the logs
            logger.debug(f"Storing {len(log_entries)} logs from {service_name}")
            await self._store_logs(log_entries)

            logger.info(
                f"Successfully processed {len(log_entries)} logs from {service_name}"
            )

        except Exception as e:
            logger.error(
                f"Error executing service '{service_name}': {str(e)}",
                exc_info=True
            )
            raise  # Re-raise to trigger retry logic

    async def _store_logs(self, logs: List[Dict[str, Any]]) -> None:
        """
        Store logs in the database.

        Args:
            logs: List of log entries to store
        """
        if not logs:
            return

        try:
            with self.db.get_cursor() as cursor:
                for log in logs:
                    cursor.execute("""
                        INSERT INTO logs
                        (source, product, event_type, severity, timestamp, raw_data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        log['source'],
                        log['product'],
                        log['event_type'],
                        log['severity'],
                        log['timestamp'],
                        log['raw_data']
                    ))
            logger.debug(f"Stored {len(logs)} logs in database")

        except Exception as e:
            logger.error(f"Error storing logs: {str(e)}", exc_info=True)
            raise

    def start(self):
        """Start the scheduler."""
        if not self.services:
            logger.warning("No services to schedule")
            return

        logger.info(f"Starting scheduler with {len(self.services)} services")
        self.scheduler.start()

    def shutdown(self, wait: bool = True):
        """
        Shutdown the scheduler gracefully.

        Args:
            wait: Whether to wait for running jobs to complete
        """
        logger.info("Shutting down scheduler service")
        self.scheduler.shutdown(wait=wait)

    async def run_forever(self):
        """
        Run the scheduler indefinitely.
        Useful for Docker containers.
        """
        logger.info("Starting scheduler service in continuous mode")
        await self.scheduler.run_forever()

    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of all scheduled jobs.

        Returns:
            Dictionary containing scheduler status and job information
        """
        return {
            'running': self.scheduler.is_running(),
            'total_services': len(self.services),
            'jobs': self.scheduler.get_all_jobs_status()
        }
