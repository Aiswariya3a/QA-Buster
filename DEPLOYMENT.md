# QA-Buster Deployment Guide

This guide covers deployment strategies for production environments.

## Prerequisites

- Docker & Docker Compose (recommended)
- PostgreSQL or MongoDB (for production databases)
- Ubuntu/Debian or similar Linux OS
- Domain name and SSL certificate

## Option 1: Docker Compose (Recommended)

### Setup

1. **Clone the repository and setup environment:**
```bash
git clone <repo-url>
cd QA-Buster
cp .env.example .env
```

2. **Configure .env for production:**
```env
DATABASE_URL=postgresql://user:password@db:5432/qa_buster
CSV_URL=https://docs.google.com/spreadsheets/d/YOUR_ID/export?format=csv
LLM_BASE_URL=http://lm-studio:1234/v1
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
CORS_ORIGINS=https://yourdomain.com
DEBUG=False
```

3. **Start the application:**
```bash
docker-compose up -d
```

4. **View logs:**
```bash
docker-compose logs -f qa-buster
```

### Scaling

For multiple instances:
```bash
docker-compose up -d --scale qa-buster=3
```

Add a load balancer (nginx) in front:
```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

---

## Option 2: Manual Deployment on Linux

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3-pip python3-venv postgresql postgresql-contrib -y

# Create app user
sudo useradd -m -s /bin/bash qa-buster
sudo su - qa-buster
```

### 2. Deploy Application

```bash
# Clone repository
git clone <repo-url> /home/qa-buster/app
cd /home/qa-buster/app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Setup environment
cp .env.example .env
# Edit .env with production settings
```

### 3. Configure PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE qa_buster;
CREATE USER qa_user WITH PASSWORD 'secure_password';
ALTER ROLE qa_user SET client_encoding TO 'utf8';
ALTER ROLE qa_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE qa_user SET default_transaction_deferrable TO on;
ALTER ROLE qa_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE qa_buster TO qa_user;
\q
```

Update `.env`:
```env
DATABASE_URL=postgresql://qa_user:secure_password@localhost/qa_buster
```

### 4. Create Systemd Services

**Main Application Service** (`/etc/systemd/system/qa-buster.service`):
```ini
[Unit]
Description=QA-Buster FastAPI Application
After=network.target postgresql.service

[Service]
Type=notify
User=qa-buster
WorkingDirectory=/home/qa-buster/app
Environment="PATH=/home/qa-buster/app/venv/bin"
ExecStart=/home/qa-buster/app/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable qa-buster.service
sudo systemctl start qa-buster.service
sudo systemctl status qa-buster.service
```

### 5. Setup Nginx Reverse Proxy

**`/etc/nginx/sites-available/qa-buster`:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /home/qa-buster/app/static/;
        expires 30d;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/qa-buster /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

### 7. Monitoring and Logs

Check application logs:
```bash
sudo journalctl -u qa-buster -f
```

Monitor system:
```bash
sudo apt install htop -y
htop
```

---

## Security Best Practices

1. **Environment Variables**: Store sensitive data in `.env` (gitignored)
   ```bash
   chmod 600 .env
   ```

2. **Database Security**:
   - Use strong passwords
   - Restrict database access to localhost or VPN only
   - Enable SSL connections

3. **API Security**:
   - Set `DEBUG=False` in production
   - Configure `CORS_ORIGINS` to specific domains
   - Add rate limiting:
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

4. **Firewall**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

5. **Regular Updates**:
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

---

## Monitoring with Prometheus & Grafana

Add to FastAPI (`main.py`):
```python
from prometheus_client import Counter, Histogram, make_wsgi_app
import time

request_count = Counter('qa_buster_requests_total', 'Total requests')
request_duration = Histogram('qa_buster_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def add_metrics(request, call_next):
    request_count.inc()
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    request_duration.observe(duration)
    return response

app.add_route("/metrics", make_wsgi_app())
```

---

## CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t qa-buster:latest .
      - name: Push to registry
        run: docker push qa-buster:latest
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_IP }}
          username: qa-buster
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd ~/app
            docker-compose pull
            docker-compose up -d
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | `sudo lsof -i :8000` and kill process |
| Database connection error | Check `DATABASE_URL` and PostgreSQL status |
| LLM worker failing | Ensure LM Studio running and accessible |
| High memory usage | Reduce `gunicorn -w` workers or database connections |
| SSL certificate expired | Run `sudo certbot renew` |

---

## Performance Tuning

1. **Database Indexing**:
```sql
CREATE INDEX idx_is_processed ON student_questions(is_processed);
CREATE INDEX idx_is_approved ON student_questions(is_approved);
```

2. **Connection Pooling**:
```python
from sqlalchemy.pool import QueuePool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

3. **Caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_questions():
    # cached for 5 minutes
    pass
```

---

## Backup Strategy

Automated daily backups:
```bash
#!/bin/bash
BACKUP_DIR="/backups/qa-buster"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -U qa_user qa_buster > "$BACKUP_DIR/db_$DATE.sql"

# Sync to S3 (optional)
aws s3 sync $BACKUP_DIR s3://my-backups/qa-buster/
```

Add to crontab:
```bash
0 2 * * * /home/qa-buster/backup.sh
```

---

For questions or issues, refer to the main README.md or open a GitHub issue.
