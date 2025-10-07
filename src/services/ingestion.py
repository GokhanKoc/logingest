import yaml
import json
import requests
from datetime import datetime
from src.database.connection import DatabaseConnection
from src.utils.config import config

def load_config():
    """Loads the YAML configuration file."""
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def transform_to_log(data, source_config):
    """Transform API response data into log format."""
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source': source_config['name'],
        'product': source_config.get('product', 'unknown'),
        'event_type': source_config.get('event_type', 'api_request'),
        'severity': source_config.get('severity', 'info'),
        'raw_data': json.dumps(data)
    }

def fetch_and_insert_logs(source_config, db):
    """Fetches logs from a source and inserts them into the database."""
    source_name = source_config['name']
    print(f"\n=== Fetching logs for {source_name} ===")
    
    try:
        endpoint = source_config['endpoint']
        method = source_config.get('method', 'GET').upper()
        params = source_config.get('params', {})
        
        print(f"  -> Calling {endpoint}")
        
        if method == 'GET':
            response = requests.get(endpoint, params=params)
        elif method == 'POST':
            response = requests.post(endpoint, json=params)
        else:
            print(f"  -> Unsupported HTTP method: {method}")
            return
        
        response.raise_for_status()
        data = response.json()
        
        # Handle list or single object responses
        items = data if isinstance(data, list) else [data]
        
        print(f"  -> Processing {len(items)} items...")
        with db.get_cursor() as cursor:
            for item in items:
                log_entry = transform_to_log(item, source_config)
                cursor.execute("""
                    INSERT INTO logs 
                    (source, product, event_type, severity, timestamp, raw_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    log_entry['source'],
                    log_entry['product'],
                    log_entry['event_type'],
                    log_entry['severity'],
                    log_entry['timestamp'],
                    log_entry['raw_data']
                ))
        
        print(f"  -> Successfully inserted {len(items)} logs")
        
    except requests.RequestException as e:
        print(f"  -> Error calling {source_name}: {e}")
    except Exception as e:
        print(f"  -> Unexpected error with {source_name}: {e}")

def main():
    """Main function to orchestrate the log ingestion process."""
    print("=== Log Ingestion Orchestrator ===")
    
    try:
        cfg = load_config()
        db_config = cfg.get('database', {})
        db = DatabaseConnection(db_config)
        
        # Create table if not exists
        with db.get_cursor() as cursor:
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
        print("✓ Database initialized\n")
    except Exception as e:
        print(f"✗ Database error: {e}")
        return
    
    try:
        sources = [s for s in cfg.get('sources', []) if s.get('enabled', False)]
        
        if not sources:
            print("No enabled sources found in config.yaml")
            return
        
        for source in sources:
            fetch_and_insert_logs(source, db)
        
        print("\n=== Ingestion Completed ===")
        
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
