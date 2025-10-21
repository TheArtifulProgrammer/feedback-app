# Feedback App - DevOps Monitoring Stack

Flask application with comprehensive monitoring using Prometheus, Loki, and Grafana.

## Features

- **Web UI**: Clean, responsive interface for managing feedback
- **RESTful API**: Complete CRUD operations for feedback management
- **SQLite Database**: Lightweight, persistent data storage
- **Prometheus Metrics**: Custom application metrics and monitoring
- **Loki Logging**: Centralized, structured JSON logging
- **Grafana Dashboards**: Pre-configured visualizations for metrics and logs
- **Docker Compose**: Single-command deployment of entire stack
- **Clean Code**: Follows KISS, DRY, YAGNI, and separation of concerns principles

## Architecture

### Monitoring Stack Flow

```text
┌─────────────────────────────────────────┐
│ feedback-app container     Port 8090    │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Flask App                           │ │
│ │  - prometheus_client creates metrics│ │──┐
│ │  - Exposes /metrics endpoint        │ │  │ HTTP GET /metrics
│ │  - Writes JSON logs to stdout/file  │ │  │ every 15s
│ └─────────────────────────────────────┘ │  │
│              │ logs                     │  │
│              ▼                          │  │
│         stdout + /app/logs              │  │
└─────────────────┬───────────────────────┘  │
                  │                          │
                  │                          ▼
           ┌──────┴────────┐      ┌──────────────────┐
           │   Promtail    │      │   Prometheus     │
           │               │      │    Port 9090     │
           │  - Reads logs │      │  - Scrapes data  │
           │  - Parses JSON│      │  - Stores metrics│
           │   Port 9080   │      │  - 7d retention  │
           └───────┬───────┘      └────────┬─────────┘
                   │ Push logs             │ Queries
                   ▼                       │
           ┌──────────────┐                │
           │    Loki      │                │
           │  Port 3100   │                │
           │ - Stores logs│                │
           │ - 168h retain│                │
           └──────┬───────┘                │
                  │ Queries                │
                  │                        │
                  ▼                        ▼
           ┌─────────────────────────────────┐
           │         Grafana                 │
           │         Port 3000               │
           │  - Visualizes metrics (from     │
           │    Prometheus)                  │
           │  - Visualizes logs (from Loki)  │
           │  - Creates dashboards           │
           └─────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Git

> **Note**: Docker must be installed and running to use the full monitoring stack. The application depends on Docker containers for Prometheus, Loki, and Grafana services.

### 1. Clone Repository

```bash
git clone https://github.com/TheArtifulProgrammer/feedback-app.git DevOpsPracticalAssignment_Munashe
cd DevOpsPracticalAssignment_Munashe
```

### 2. Start All Services

```bash
docker-compose up -d
```

This single command will:

- Build the Flask application
- Start Prometheus, Loki, Promtail, and Grafana
- Configure all monitoring components
- Set up networking between services

### 3. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Web UI** | <http://localhost:8090> | - |
| Feedback API | <http://localhost:8090/feedback> | - |
| Prometheus | <http://localhost:9090> | - |
| Grafana | <http://localhost:3000> | admin / admin |
| cAdvisor | <http://localhost:8081> | - |

### 4. Use the Application

**Web Interface (Recommended):**

1. Open <http://localhost:8090> in your browser
2. Use the clean, modern interface to:
   - View all feedback in card format
   - Add new feedback using the "+ Add Feedback" button
   - Edit existing feedback inline
   - Delete feedback with confirmation
   - See real-time health status
   - Monitor feedback count

**API Testing:**
See the "Testing the API" section below for curl examples.

### 5. View Monitoring Dashboards

1. Open Grafana: <http://localhost:3000>
2. Login with `admin` / `admin`
3. Navigate to: **Dashboards** → **Feedback Application**
4. Available dashboards:
   - **Application Metrics**: Request rates, latency, operations
   - **Application Logs**: Real-time log streaming and analysis

## API Endpoints

### Health Check

```bash
GET /health
```

### Create Feedback

```bash
POST /feedback
Content-Type: application/json

{
  "message": "Great service!"
}
```

### Get All Feedback

```bash
GET /feedback
```

### Get Single Feedback

```bash
GET /feedback/<id>
```

### Update Feedback

```bash
PUT /feedback/<id>
Content-Type: application/json

{
  "message": "Updated feedback message"
}
```

### Delete Feedback

```bash
DELETE /feedback/<id>
```

### Metrics (Prometheus)

```bash
GET /metrics
```

## Testing the API

### Using curl

```bash
# Create feedback
curl -X POST http://localhost:8090/feedback \
  -H "Content-Type: application/json" \
  -d '{"message": "This is awesome!"}'

# Get all feedback
curl http://localhost:8090/feedback

# Get specific feedback
curl http://localhost:8090/feedback/1

# Update feedback
curl -X PUT http://localhost:8090/feedback/1 \
  -H "Content-Type: application/json" \
  -d '{"message": "Updated message"}'

# Delete feedback
curl -X DELETE http://localhost:8090/feedback/1

# Check health
curl http://localhost:8090/health
```

## Project Structure

```text
DevOpsPracticalAssignment_Munashe/
├── app/                        # Application code
│   ├── __init__.py            # Flask factory
│   ├── config.py              # Configuration management
│   ├── database.py            # Database operations (DRY)
│   ├── models.py              # Data models
│   ├── routes.py              # API endpoints
│   ├── metrics.py             # Prometheus instrumentation
│   ├── logging_config.py      # Structured logging
│   ├── static/                # Frontend assets
│   │   ├── css/style.css     # Clean, modern stylesheet
│   │   └── js/app.js         # Vanilla JavaScript (no frameworks)
│   └── templates/
│       └── index.html         # Main web interface
├── monitoring/                 # Monitoring configurations
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── loki/
│   │   └── loki-config.yml
│   ├── promtail/
│   │   └── promtail-config.yml
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   └── dashboards/
│       └── dashboards/
│           ├── feedback-app-metrics.json
│           └── feedback-app-logs.json
├── data/                       # SQLite database (persistent)
├── logs/                       # Application logs
├── Dockerfile                  # Application container
├── docker-compose.yml          # Service orchestration
├── requirements.txt            # Python dependencies
├── main.py                     # Application entry point
└── README.md                   # This file
```

## Monitoring & Observability

### Metrics Collected

- **HTTP Request Rate**: Requests per second by endpoint
- **Request Latency**: P50, P95, P99 percentiles
- **Feedback Operations**: Create, read, update, delete counts
- **Active Feedback Count**: Total feedback entries
- **Error Rate**: Application errors by type
- **Container Metrics**: CPU, memory, network via cAdvisor
- **Host Metrics**: System resources via Node Exporter

### Log Management

- **Structured JSON Logs**: Easy parsing and querying
- **Real-time Streaming**: Live log tailing in Grafana
- **Log Levels**: INFO, WARNING, ERROR with filtering
- **Retention**: 7-day log retention (configurable)

## Development

### Local Development (without Docker)

> **Note**: Running locally without Docker is **not recommended**. While the Flask application will run, you will not have access to the monitoring stack (Prometheus, Loki, Grafana), limiting your ability to view metrics and logs through the dashboards.

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `data/feedback.db` | SQLite database path |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `logs/app.log` | Log file path |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8090` | Server port |

## Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f feedback-app
```

### Stop Services

```bash
docker-compose down
```

### Reset Everything

```bash
# Stop and remove all containers, volumes
docker-compose down -v

# Remove database and logs
rm -rf data/* logs/*

# Start fresh
docker-compose up -d
```

### Update Application

```bash
# Rebuild and restart
docker-compose up -d --build feedback-app
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :8090  # Windows
lsof -i :8090                  # Mac/Linux

# Change ports in docker-compose.yml
```

### Container Won't Start

```bash
# Check logs
docker-compose logs feedback-app

# Rebuild
docker-compose up -d --build --force-recreate
```

### Database Locked

```bash
# Stop all services
docker-compose down

# Remove database lock
rm data/feedback.db-shm data/feedback.db-wal

# Restart
docker-compose up -d
```

## License

MIT License

## Author

Munashe Chinake - DevOps Practical Assignment
