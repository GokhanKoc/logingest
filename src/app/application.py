# logingest/src/app.py
import asyncio
from typing import List, Dict, Any
from ..utils.logger import logger
from ..utils.config import config
from ..database.connection import DatabaseConnection
from ..services import ServiceFactory

class LogIngestApp:
    def __init__(self):
        self.db = DatabaseConnection(config.get_database_config())
        self.services = []
        
    async def initialize(self):
        """Initialize the application."""
        logger.info("Initializing LogIngest application")
        await self._setup_database()
        self._setup_services()
        
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
                """)
            logger.info("Database setup completed")
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise
    
    def _setup_services(self):
        """Initialize services from configuration."""
        logger.info("Setting up services")
        services_config = config.get('sources', [])
        
        for service_config in services_config:
            if not service_config.get('enabled', True):
                logger.info(f"Skipping disabled service: {service_config.get('name')}")
                continue
                
            try:
                service = ServiceFactory.from_config(service_config)
                self.services.append(service)
                logger.info(f"Initialized service: {service_config.get('name')}")
            except Exception as e:
                logger.error(f"Failed to initialize service {service_config.get('name')}: {str(e)}")
    
    async def run(self):
        """Run the application."""
        if not self.services:
            logger.warning("No services configured or enabled")
            return
            
        logger.info("Starting log ingestion")
        tasks = [self._process_service(service) for service in self.services]
        await asyncio.gather(*tasks)
        logger.info("Log ingestion completed")
    
    async def _process_service(self, service):
        """Process a single service."""
        service_name = service.config.get('name', 'unknown')
        logger.info(f"Processing service: {service_name}")
        
        try:
            # Fetch data from the service
            data = await service.fetch_data()
            
            # Transform the data
            log_entries = service.transform(data)
            
            # Store the logs
            await self._store_logs(log_entries)
            
            logger.info(f"Processed {len(log_entries)} logs from {service_name}")
        except Exception as e:
            logger.error(f"Error processing service {service_name}: {str(e)}", exc_info=True)
    
    async def _store_logs(self, logs: List[Dict[str, Any]]) -> None:
        """Store logs in the database."""
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
        except Exception as e:
            logger.error(f"Error storing logs: {str(e)}")
            raise