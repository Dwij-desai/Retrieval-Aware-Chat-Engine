# Step-4: Automated Data Ingestion

## Overview
Automatically ingest new documents without manual intervention. Perfect for:
- Production environments with continuous data updates
- Data pipelines that push new files to cloud storage
- CI/CD workflows that need to re-ingest on each deployment

## The Problem It Solves

### Without Automation
```
# New data arrives in data/ folder
# Human notices and manually runs:
python backend/ingest.py
# Repeat this 50 times a day...
```

### With Automation
```
# New data arrives
# 🤖 System auto-ingests immediately
# Zero manual intervention
```

## Quick Start

### 1. Watch Mode (Continuous Monitoring)
```bash
# Runs forever, watching data/ for new files
python backend/ingest_orchestrator.py --mode watch
```

Perfect for:
- Development
- Always-on services
- Real-time data ingestion

### 2. Scheduled Mode (Periodic Runs)
```bash
# Run ingestion every hour
python backend/ingest_orchestrator.py --mode schedule --interval hourly

# Options: hourly, daily, weekly
```

Perfect for:
- Nightly batch imports
- Regular data refreshes
- Controlled ingestion windows

### 3. One-Time Run
```bash
# Ingest once and exit
python backend/ingest_orchestrator.py --mode once
```

Perfect for:
- CI/CD pipelines
- Initial setup
- Manual triggers

### 4. Daemon Mode (Background Service)
```bash
# Run as background daemon
python backend/ingest_orchestrator.py --mode daemon
```

Perfect for:
- Production deployments
- systemd services
- Always-on ingestion

## Docker Integration

### Run in Container
```bash
# Watch mode
docker-compose exec api python backend/ingest_orchestrator.py --mode watch

# Or add to docker-compose.yml:
services:
  ingest-watcher:
    build: .
    command: python backend/ingest_orchestrator.py --mode watch
    volumes:
      - ./data:/app/data
      - ./chroma_db:/app/chroma_db
    environment:
      PYTHONUNBUFFERED: "1"
```

## Advanced: Scheduled Ingestion Service

### Create systemd Service (Linux/Mac)

1. Create `/etc/systemd/system/ai-ingest.service`:
```ini
[Unit]
Description=AI Chatbot Auto Ingestion
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/AI_SAAS(ChatBot)
ExecStart=/opt/anaconda3/envs/ai_saas/bin/python backend/ingest_orchestrator.py --mode schedule --interval daily
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-ingest
sudo systemctl start ai-ingest

# Check status
sudo systemctl status ai-ingest

# View logs
sudo journalctl -u ai-ingest -f
```

### Create Cron Job

```bash
# Edit crontab
crontab -e

# Add scheduled ingestion (daily at 2 AM)
0 2 * * * cd /path/to/AI_SAAS(ChatBot) && /opt/anaconda3/envs/ai_saas/bin/python backend/ingest_orchestrator.py --mode once
```

## Cloud Integration

### AWS: S3 + Lambda
1. Upload data to S3 bucket
2. Create Lambda function:

```python
def lambda_handler(event, context):
    # S3 event triggers this
    # Download file from S3
    # Call ingest_documents_from_directory()
```

3. Configure S3 → Lambda trigger

### GCP: Cloud Storage + Cloud Functions
```python
def ingest_from_gcs(request):
    # Cloud Storage event triggers this
    # Download blob from GCS
    # Call ingest_documents_from_directory()
```

### Azure: Blob Storage + Azure Functions
```python
def main(msg: func.InputStream):
    # Blob Storage event triggers this
    # Download blob
    # Call ingest_documents_from_directory()
```

## File Watcher Details

The `file_watcher.py` module provides low-level monitoring:

```python
from backend.file_watcher import watch_data_directory

def my_ingest_callback(file_path):
    print(f"New file: {file_path}")
    # Ingest it

observer = watch_data_directory(ingest_callback=my_ingest_callback)
observer.start()

# Later...
observer.stop()
observer.join()
```

## Features

### ✅ Smart Detection
- Auto-detects file type (PDF, CSV, JSON, etc.)
- Ignores temporary files (.tmp, .swp)
- Handles partial writes (waits for file to be ready)

### ✅ Duplicate Prevention
- Tracks processed files
- Won't ingest the same file twice
- Re-ingests if file is modified

### ✅ Error Handling
- Continues on failures (non-blocking)
- Logs all errors for debugging
- Retries on transient failures

### ✅ Performance
- Async monitoring (low CPU)
- Batch processing support
- Configurable intervals

## Monitoring & Observability

### Check Ingestion Status
```bash
# View recent ingestions
tail -50 ingest.log

# Search for errors
grep "ERROR\|FAILED" ingest.log

# Count ingestions per day
grep "Successfully ingested" ingest.log | wc -l
```

### Integrate with LangSmith
Ingestions are automatically traced if LangSmith is enabled:
```bash
export LANGCHAIN_API_KEY=your_key
python backend/ingest_orchestrator.py --mode watch
# All ingestions appear in LangSmith dashboard
```

### Integrate with Prometheus
```python
from prometheus_client import Counter

ingest_count = Counter('ingestions_total', 'Total ingestions')
ingest_errors = Counter('ingestion_errors_total', 'Failed ingestions')

try:
    ingest_documents_from_directory(data_dir)
    ingest_count.inc()
except:
    ingest_errors.inc()
```

## File Structure

```
backend/
  ├── file_watcher.py          # Low-level folder monitoring
  ├── ingest_orchestrator.py   # High-level orchestration
  └── ingest.py                # Core ingestion logic (unchanged)
docs/
  └── AUTO_INGEST.md           # This guide
.env
  └── AUTO_INGEST_MODE=watch   # Optional: default mode
```

## Configuration Options

### Environment Variables
```env
# Optional: set default mode
AUTO_INGEST_MODE=watch          # watch, once, schedule, daemon
AUTO_INGEST_INTERVAL=hourly     # hourly, daily, weekly
AUTO_INGEST_DIR=data            # directory to watch
```

### Command-Line Arguments
```bash
python backend/ingest_orchestrator.py \
  --mode watch \
  --data-dir data
```

## Troubleshooting

### Q: "Files aren't being detected"
```bash
# Check permissions
ls -la data/

# Verify file_watcher.py
python -c "from backend.file_watcher import watch_data_directory; print('OK')"

# Run in verbose mode
python backend/ingest_orchestrator.py --mode watch 2>&1 | head -20
```

### Q: "Same file ingested multiple times"
The deduplication system tracks `processed_files`. If running multiple instances:
- Use a distributed cache (Redis) for tracking
- Or use a database to log ingested files

```python
# Store ingestion history in DB
create_table ingestion_log (
    file_path TEXT PRIMARY KEY,
    ingested_at TIMESTAMP,
    status TEXT
)
```

### Q: "Performance degradation"
- Large files take time to process
- Consider increasing batch size in `ingest.py`
- Use scheduled mode instead of watch mode
- Split data into smaller batches

## Best Practices

### 1. Data Organization
```
data/
  ├── incoming/        # Drop new files here
  ├── processed/       # Move files after ingestion
  └── failed/          # Move failed files here
```

### 2. Monitoring
```bash
# Regular health checks
* * * * * pgrep -f ingest_orchestrator || systemctl start ai-ingest

# Alert on errors
grep ERROR ingest.log | mailx -s "Ingestion Error" admin@example.com
```

### 3. Retention Policy
```bash
# Clean up old data weekly
find data/processed -mtime +7 -delete
find data/failed -mtime +30 -delete
```

## Next Steps
- ✅ Step-2: Ragas Evaluation
- ✅ Step-3: LangSmith Tracing
- ✅ Step-4: Automated Ingestion
- ⏳ Step-5: Expand Tests
