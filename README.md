# Log Ingest

A scalable log ingestion service that collects logs from various sources and stores them in a PostgreSQL database.

## Features

- **Scheduler-based Architecture**: Cron-based job scheduling for continuous operation
- **Parallel Execution**: Multiple services run concurrently with configurable limits
- **Automatic Retries**: Built-in retry logic with exponential backoff
- **Modular Design**: Pluggable services with easy extensibility
- **Asynchronous Processing**: Non-blocking I/O for better performance
- **Centralized Configuration**: YAML-based configuration with environment variable support
- **Structured Logging**: Comprehensive logging with different log levels
- **Database Integration**: PostgreSQL with automatic schema management
- **Graceful Shutdown**: Clean container stops with signal handling
- **Unit and Integration Tests**: Comprehensive test coverage

## Project Structure

```
logingest/
├── config/              # Configuration files
│   └── config.yaml     # Main configuration
├── scripts/            # Utility scripts
│   └── init-db.sh     # Database initialization
├── src/               # Source code
│   ├── app.py         # Main application
│   ├── main.py        # Entry point
│   ├── database/      # Database connections
│   ├── models/        # Data models
│   ├── services/      # Service implementations
│   └── utils/         # Utilities (config, logger)
├── tests/             # Test suite
├── docker-compose.yml # Docker orchestration
├── Dockerfile         # Container definition
└── requirements.txt   # Python dependencies
```

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/logingest.git
   cd logingest
   ```

2. Build and start the services:
   ```bash
   docker-compose up --build -d
   ```

3. View logs to see the scheduler in action:
   ```bash
   docker-compose logs -f app
   ```

4. Stop the services:
   ```bash
   docker-compose down
   ```

### Local Development

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Start PostgreSQL (if running locally):
   ```bash
   docker-compose up -d db
   ```

5. Run the application:
   ```bash
   python -m src.main
   ```

## How It Works

The application runs a **scheduler** that executes data ingestion jobs based on cron expressions defined in `config/config.yaml`:

1. **Startup**: Application loads configuration and initializes the scheduler
2. **Scheduling**: Each service is scheduled according to its cron expression
3. **Execution**: Jobs run automatically at their scheduled times
4. **Continuous**: Application runs indefinitely in Docker, fetching and storing data

Example schedule configuration:
```yaml
sources:
  - name: json_placeholder_posts
    schedule: "*/30 * * * *"  # Every 30 minutes
    endpoint: "https://jsonplaceholder.typicode.com/posts"
    enabled: true
```

See [SCHEDULER.md](SCHEDULER.md) for detailed documentation.

To check DB 

```bash
docker exec -it logingest-db bash
```

Connect to PostgreSQL
```bash
psql -U postgres -d logingest
```

```sql
-- List all tables
\dt

-- View logs table structure
\d logs

-- Query logs
SELECT * FROM logs LIMIT 10;

-- Count total logs
SELECT COUNT(*) FROM logs;

-- View logs by source
SELECT source, COUNT(*) as count FROM logs GROUP BY source;

-- Exit psql
\q
```