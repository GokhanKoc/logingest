# Scheduler Documentation

## Overview

The LogIngest scheduler is a general-purpose job scheduling system that automatically executes data ingestion services based on cron expressions defined in `config/config.yaml`. The scheduler runs continuously in Docker and manages multiple services concurrently.

## Features

- **Cron-based Scheduling**: Each service runs on its own schedule using standard cron syntax
- **Parallel Execution**: Configurable maximum parallel jobs (default: 3)
- **Automatic Retries**: Exponential backoff retry logic for failed jobs
- **Timeout Protection**: Configurable timeouts per service
- **Graceful Shutdown**: Handles SIGTERM/SIGINT for clean container stops
- **Job Monitoring**: Track execution counts, errors, and next run times
- **Timezone Support**: Configure timezone for scheduling (default: UTC)

## Architecture

```
LogIngestApp (application.py)
    └── SchedulerService (scheduler_service.py)
        └── Scheduler (scheduler.py)
            └── APScheduler
```

### Components

1. **Scheduler** (`src/scheduler/scheduler.py`)
   - Low-level job scheduling using APScheduler
   - Manages job lifecycle, retries, and execution
   - Provides job status and monitoring

2. **SchedulerService** (`src/scheduler/scheduler_service.py`)
   - High-level service that connects scheduler with data sources
   - Initializes services from config.yaml
   - Handles data fetching, transformation, and storage

3. **LogIngestApp** (`src/app/application.py`)
   - Main application entry point
   - Manages database setup and scheduler lifecycle
   - Handles graceful shutdown

## Configuration

### Global Scheduler Settings

In `config/config.yaml`:

```yaml
scheduler:
  # Core settings
  timezone: "UTC"
  max_parallel_jobs: 3
  log_level: "INFO"

  # Default retry settings (can be overridden per service)
  default_retry:
    attempts: 3
    delay: 60  # seconds
    backoff: 2  # exponential backoff multiplier

  # Monitoring settings
  monitoring:
    enabled: true
    health_check_interval: 300  # seconds
```

### Service Configuration

Each service in the `sources` array requires a `schedule` field:

```yaml
sources:
  - name: json_placeholder_posts
    type: json_placeholder
    endpoint: "https://jsonplaceholder.typicode.com/posts"
    enabled: true

    # Scheduling: cron expression (minute hour day month day_of_week)
    schedule: "*/30 * * * *"  # Every 30 minutes

    # Timeout for this service
    timeout: 300  # 5 minutes

    # Retry configuration (overrides global settings)
    retry:
      attempts: 2
      delay: 30
      backoff: 2
```

### Cron Expression Examples

| Expression | Description |
|------------|-------------|
| `*/30 * * * *` | Every 30 minutes |
| `0 * * * *` | Every hour at minute 0 |
| `0 2 * * *` | Daily at 2:00 AM |
| `15 * * * *` | Every hour at minute 15 |
| `0 */6 * * *` | Every 6 hours |
| `0 9 * * 1` | Every Monday at 9:00 AM |
| `30 14 1 * *` | Monthly on the 1st at 2:30 PM |

## Running the Scheduler

### Using Docker Compose (Recommended)

1. Build and start the services:
```bash
docker-compose up --build -d
```

2. View logs:
```bash
docker-compose logs -f app
```

3. Stop the services:
```bash
docker-compose down
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python -m src.main
```

3. Stop with Ctrl+C (graceful shutdown)

## How It Works

### Startup Sequence

1. Application loads configuration from `config/config.yaml`
2. Database connection is established and tables are created
3. SchedulerService initializes:
   - Reads all sources from config
   - Creates service instances for enabled sources
   - Schedules each service with its cron expression
4. Scheduler starts and jobs run according to their schedules
5. Application runs indefinitely until shutdown signal

### Job Execution Flow

For each scheduled job:

1. **Trigger**: Cron expression triggers job execution
2. **Fetch**: Service fetches data from configured endpoint
3. **Transform**: Raw data is transformed into log entries
4. **Store**: Log entries are inserted into PostgreSQL
5. **Retry**: On failure, retry with exponential backoff
6. **Log**: Success/failure is logged with statistics

### Retry Logic

When a job fails:
- Attempt 1: Execute immediately
- Attempt 2: Wait `delay` seconds (default: 60s)
- Attempt 3: Wait `delay * backoff` seconds (default: 120s)
- Attempt N: Wait `delay * backoff^(N-1)` seconds

Example with default settings (delay=60, backoff=2):
- Attempt 1: Immediate
- Attempt 2: After 60 seconds
- Attempt 3: After 120 seconds

## Monitoring

### View Scheduler Status

Add a status endpoint or check logs for:
- Running jobs
- Next execution times
- Execution counts
- Error counts

### Example Log Output

```
2025-01-15 10:00:00 - INFO - Starting scheduler with timezone: UTC
2025-01-15 10:00:00 - INFO - Max parallel jobs: 3
2025-01-15 10:00:00 - INFO - Total jobs scheduled: 3
2025-01-15 10:00:00 - INFO -   - json_placeholder_posts: */30 * * * * (next run: 2025-01-15 10:30:00+00:00)
2025-01-15 10:00:00 - INFO -   - json_placeholder_users: 0 2 * * * (next run: 2025-01-16 02:00:00+00:00)
2025-01-15 10:00:00 - INFO -   - json_placeholder_todos: 15 * * * * (next run: 2025-01-15 10:15:00+00:00)
2025-01-15 10:00:00 - INFO - Scheduler started successfully
2025-01-15 10:00:00 - INFO - Application is now running. Press Ctrl+C to stop.
```

### Job Execution Logs

```
2025-01-15 10:30:00 - INFO - Executing job 'json_placeholder_posts' (attempt 1/2)
2025-01-15 10:30:00 - INFO - Executing service: json_placeholder_posts
2025-01-15 10:30:01 - INFO - Successfully processed 5 logs from json_placeholder_posts
2025-01-15 10:30:01 - INFO - Job 'json_placeholder_posts' completed successfully
```

## Graceful Shutdown

The scheduler supports graceful shutdown to avoid data loss:

1. Application receives SIGTERM or SIGINT
2. Scheduler stops accepting new jobs
3. Currently running jobs are allowed to complete (configurable)
4. Database connections are closed
5. Application exits cleanly

### In Docker

```bash
docker stop logingest-app  # Sends SIGTERM, waits 10 seconds, then SIGKILL
```

### Local

Press `Ctrl+C` to trigger graceful shutdown.

## Troubleshooting

### Job Not Running

1. Check if service is enabled in config.yaml:
```yaml
enabled: true
```

2. Verify cron expression is valid (5 fields, space-separated)

3. Check logs for scheduling errors:
```bash
docker-compose logs app | grep ERROR
```

### Jobs Running Too Frequently

- Adjust the cron expression to a less frequent schedule
- Increase the `timeout` value if jobs are timing out

### Jobs Failing

1. Check retry configuration
2. Verify endpoint URLs are accessible
3. Check authentication credentials
4. Review timeout settings

### Database Connection Issues

1. Verify database is healthy:
```bash
docker-compose ps
```

2. Check database connection settings in config.yaml
3. Ensure database container is running before app starts

## Environment Variables

Override config values with environment variables:

```bash
SCHEDULER_TIMEZONE=America/New_York
SCHEDULER_MAX_JOBS=5
SCHEDULER_RETRY_ATTEMPTS=5
SCHEDULER_RETRY_DELAY=120
DB_HOST=db
DB_PORT=5432
DB_NAME=logingest
DB_USER=postgres
DB_PASSWORD=password
```

## Best Practices

1. **Start with Conservative Schedules**: Use longer intervals initially (e.g., hourly) and adjust based on data volume

2. **Set Appropriate Timeouts**: Match timeout to expected execution time + buffer (e.g., if job takes 30s, set timeout to 60s)

3. **Configure Retries**: Use fewer retries (2-3) with longer delays for external API calls

4. **Monitor Logs**: Regularly check logs for errors and adjust configurations

5. **Use Timezone Consistently**: Keep all schedules in the same timezone (UTC recommended)

6. **Limit Parallel Jobs**: Set `max_parallel_jobs` based on system resources and API rate limits

## Advanced Usage

### Custom Service Implementation

To add a new data source type:

1. Create a new service class in `src/services/api_services/`
2. Inherit from `BaseService`
3. Implement `fetch_data()` and `transform()` methods
4. Register in `ServiceFactory`
5. Add configuration to `config.yaml`


## Dependencies

- **APScheduler**: Advanced Python Scheduler for cron-based job scheduling
- **psycopg2**: PostgreSQL database adapter
- **asyncio**: Asynchronous I/O for concurrent job execution
