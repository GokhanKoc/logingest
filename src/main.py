# src/main.py
import asyncio
import sys
from pathlib import Path

from .app.application import LogIngestApp
from .utils.logger import logger
from .utils.config import config

async def main():
    try:
        # Load configuration
        # Try Docker path first, then local path
        config_path = Path("/app/config/config.yaml")
        if not config_path.exists():
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
            
        config.load_yaml(str(config_path))
        
        # Initialize and run the application
        app = LogIngestApp()
        await app.initialize()
        await app.run()
        
    except Exception as e:
        logger.critical(f"Application failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
