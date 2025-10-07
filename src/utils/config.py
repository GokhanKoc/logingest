# logingest/src/utils/config.py
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class ConfigError(Exception):
    pass

class _Config:
    def __init__(self):
        self._config = {}
        self._initialized = False
        
    def initialize(self):
        if not self._initialized:
            self._config = {}
            self._initialized = True
            self.load_environment()
            
    def load_environment(self, env_file: str = ".env") -> None:
        """Load environment variables from .env file."""
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
    
    def load_yaml(self, config_path: str = "config/config.yaml") -> None:
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {config_path}")
        
        try:
            with open(path, 'r') as f:
                content = f.read()
                # Simple environment variable substitution
                import re
                def replace_env(match):
                    var_name = match.group(1)
                    default = match.group(2) if match.group(2) else ''
                    return os.getenv(var_name, default)
                content = re.sub(r'\$\{(\w+)(?::-(.*?))?\}', replace_env, content)
                self._config = yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration."""
        # Try to get from YAML config first, then fall back to env vars
        db_config = self._config.get('database', {})
        return {
            'DB_HOST': db_config.get('DB_HOST') or os.getenv('DB_HOST', 'localhost'),
            'DB_PORT': db_config.get('DB_PORT') or os.getenv('DB_PORT', '5432'),
            'DB_NAME': db_config.get('DB_NAME') or os.getenv('DB_NAME', 'logingest'),
            'DB_USER': db_config.get('DB_USER') or os.getenv('DB_USER', 'postgres'),
            'DB_PASSWORD': db_config.get('DB_PASSWORD') or os.getenv('DB_PASSWORD', 'password')
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file': os.getenv('LOG_FILE', 'logs/application.log'),
            'max_size': int(os.getenv('LOG_MAX_SIZE', '10485760')),  # 10MB
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
        }

# Module-level instance
config = _Config()