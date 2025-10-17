# logingest/src/app/application.py
import asyncio
import signal
from typing import Dict, Any
from ..utils.logger import logger
from ..utils.config import config
from ..database.connection import DatabaseConnection
from ..scheduler.scheduler_service import SchedulerService


class LogIngestApp:
    """
    Main application that manages the log ingestion system.

    This application can run in two modes:
    1. One-time execution: Fetch and store logs immediately (legacy mode)
    2. Scheduled execution: Run continuously with scheduled jobs (default)
    """

    def __init__(self, run_mode: str = 'scheduled'):
        """
        Initialize the application.

        Args:
            run_mode: 'scheduled' for continuous running, 'once' for one-time execution
        """
        self.db = DatabaseConnection(config.get_database_config())
        self.run_mode = run_mode
        self.scheduler_service = None
        self._shutdown_requested = False

    async def initialize(self):
        """Initialize the application."""
        logger.info(f"Initializing LogIngest application (mode: {self.run_mode})")
        await self._setup_database()

        if self.run_mode == 'scheduled':
            self._setup_scheduler()
        else:
            logger.warning(
                "Running in one-time execution mode. "
                "Use run_mode='scheduled' for continuous operation."
            )

    async def _setup_database(self):
        """Set up database tables if they don't exist."""
        logger.info("Setting up database")
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id SERIAL PRIMARY KEY,
                        source VARCHAR(100) NOT NULL,
                        product VARCHAR(100) NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        raw_data JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source);
                    CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_logs_event_type ON logs(event_type);
                    CREATE INDEX IF NOT EXISTS idx_logs_product ON logs(product);
                """)
            logger.info("Database setup completed")
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise

    def _setup_scheduler(self):
        """Initialize the scheduler service."""
        logger.info("Setting up scheduler")
        try:
            self.scheduler_service = SchedulerService(self.db)
            self.scheduler_service.initialize_services()
            logger.info("Scheduler setup completed")
        except Exception as e:
            logger.error(f"Scheduler setup failed: {str(e)}")
            raise

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            logger.info(f"Received signal {signal_name}, initiating shutdown...")
            self._shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self):
        """
        Run the application based on the configured mode.
        """
        if self.run_mode == 'scheduled':
            await self._run_scheduled()
        else:
            logger.info("One-time execution mode is deprecated. Please use scheduled mode.")
            logger.info("To run jobs immediately, trigger them manually or adjust schedules.")

    async def _run_scheduled(self):
        """
        Run the application in scheduled mode (continuous operation).
        """
        if not self.scheduler_service:
            logger.error("Scheduler service not initialized")
            return

        logger.info("Starting application in scheduled mode")
        self._setup_signal_handlers()

        try:
            # Start the scheduler
            self.scheduler_service.start()

            # Log the status
            status = self.scheduler_service.get_status()
            logger.info(f"Scheduler status: {status}")

            # Run forever (or until shutdown is requested)
            logger.info("Application is now running. Press Ctrl+C to stop.")
            while not self._shutdown_requested:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in scheduled mode: {str(e)}", exc_info=True)
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown the application gracefully."""
        logger.info("Shutting down application...")

        if self.scheduler_service:
            logger.info("Shutting down scheduler service...")
            self.scheduler_service.shutdown(wait=True)

        if self.db:
            logger.info("Closing database connection...")
            try:
                self.db.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")

        logger.info("Application shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current application status.

        Returns:
            Dictionary containing application status information
        """
        status = {
            'run_mode': self.run_mode,
            'database_connected': self.db is not None,
        }

        if self.scheduler_service:
            status['scheduler'] = self.scheduler_service.get_status()

        return status