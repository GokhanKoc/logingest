# Log Ingest

A scalable log ingestion service that collects logs from various sources and stores them in a PostgreSQL database.

## Features

- Modular architecture with pluggable services
- Asynchronous processing
- Centralized configuration
- Structured logging
- Database migrations
- Unit and integration tests

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

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/logingest.git
   cd logingest
   ```

2. Start the services:
   ```bash
   docker-compose up -d
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

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Run the application:
   ```bash
   python -m src.main
   ```

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