# Production Deployment Guide: PlanBridge AI
**Oil India Limited — Intelligent Schedule-Linking Layer (SIH PS 26122)**

This guide provides end-to-end instructions for deploying the **PlanBridge AI** platform into production environments, ranging from containerized Docker clusters to enterprise Cloud VMs (AWS, GCP, Azure) and serverless platforms.

---

## 1. System Architecture & Ports

The production platform operates as a decoupled, multi-service architecture:

```
                          [ Client Browsers / Mobile Time Agent / PMIS Webhooks ]
                                                    │
                                                    ▼
                                  [ Nginx Reverse Proxy (Port 80 / 443) ]
                                      ├── /api/  ──► [ FastAPI Backend (Port 8000) ]
                                      └── /      ──► [ Streamlit Dashboard (Port 8501) ]
                                                              │
                                            ┌─────────────────┴─────────────────┐
                                            ▼                                   ▼
                             [ Sentence-Transformers ]             [ SQLite / Postgres Store ]
                             (Local all-MiniLM-L6-v2)             (sih_bridge.db with WAL)
```

| Service | Port | Description | Health Endpoint |
| :--- | :---: | :--- | :--- |
| **Streamlit Operations UI** | `8501` | Interactive dashboard for Planners, Supervisors, Contractors, Auditors | `/_stcore/health` |
| **FastAPI REST Backend** | `8000` | High-throughput headless API for mobile apps, spreadsheets, PMIS | `/health` |
| **Swagger / OpenAPI** | `8000` | Interactive REST documentation & testing sandbox | `/docs` |

---

## 2. Option A: Docker Compose Deployment (Recommended)

The platform is fully containerized with **pre-baked sentence-transformer model weights** in the Docker image, ensuring zero cold-start delay and zero cloud dependency.

### Prerequisites
* Docker Engine 24.0+ and Docker Compose v2.0+

### Steps
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sih-ps26122-bridge
   ```

2. **Configure Environment Variables** (Optional for cloud LLM extraction):
   ```bash
   cp .env.example .env
   # Edit .env to add your GEMINI_API_KEY (if using cloud LLM; otherwise deterministic offline fallback is used)
   ```

3. **Build and Launch the Stack**:
   ```bash
   docker compose up --build -d
   ```

4. **Verify Deployment Health**:
   ```bash
   docker compose ps
   curl -f http://localhost:8000/health
   curl -f http://localhost:8501/_stcore/health
   ```

5. **Access the Platform**:
   * Operations Dashboard: `http://<your-server-ip>:8501`
   * REST API & Swagger UI: `http://<your-server-ip>:8000/docs`

---

## 3. Option B: Native Host / Enterprise VM Deployment (Linux / Windows)

For dedicated on-premise servers or cloud virtual machines (Ubuntu 22.04 LTS, Debian 12, Windows Server):

### 1. System Requirements
* **OS**: Ubuntu 22.04 LTS, RHEL 9, or Windows Server 2022
* **CPU**: 2 vCPUs minimum (4 vCPUs recommended for concurrent vector matching)
* **RAM**: 4 GB RAM minimum (8 GB recommended)
* **Storage**: 10 GB SSD for vector cache and immutable audit logs

### 2. Linux Setup Commands
```bash
# Update and install Python 3.11 & tools
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip curl nginx sqlite3

# Clone and enter repo
cd /opt
sudo git clone <repo-url> planbridge
sudo chown -R $USER:$USER /opt/planbridge
cd /opt/planbridge

# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run automated tests to verify deployment integrity
pytest
```

### 3. One-Click Dual Launcher
To launch both FastAPI (Port 8000) and Streamlit (Port 8501) with auto-restart:
```bash
python start_production.py
```

### 4. Setup Systemd Service (Auto-Start on Boot)
Create `/etc/systemd/system/planbridge.service`:
```ini
[Unit]
Description=PlanBridge AI Platform (Oil India Limited)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/planbridge
ExecStart=/opt/planbridge/.venv/bin/python /opt/planbridge/start_production.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable planbridge
sudo systemctl start planbridge
sudo systemctl status planbridge
```

---

## 4. Production Nginx Reverse Proxy with SSL (HTTPS)

Deploy Nginx to serve both services under a single domain with secure WebSockets.

1. **Copy Nginx Configuration**:
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/planbridge.conf
   sudo ln -s /etc/nginx/sites-available/planbridge.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

2. **Enable Free SSL/TLS with Let's Encrypt**:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d planbridge.oilindia.in
   ```

---

## 5. Option C: Cloud Serverless & PaaS Deployment

### Google Cloud Run
1. Build and push container to Google Artifact Registry:
   ```bash
   gcloud builds submit --tag gcr.io/[PROJECT-ID]/planbridge-ai
   ```
2. Deploy service:
   ```bash
   gcloud run deploy planbridge-ai \
     --image gcr.io/[PROJECT-ID]/planbridge-ai \
     --platform managed \
     --memory 2Gi \
     --cpu 2 \
     --port 8501 \
     --allow-unauthenticated
   ```

### Streamlit Community Cloud / Hugging Face Spaces
1. Push this repository to GitHub.
2. Link the repository on [Streamlit Cloud](https://share.streamlit.io).
3. Set the Main file path to: `app/dashboard.py`.
4. Deploy! All dependencies in `requirements.txt` will automatically install and run.

---

## 6. Database Hardening & Maintenance

### High-Concurrency WAL Mode
The production SQLite database uses Write-Ahead Logging (WAL) for concurrent reads/writes:
```sql
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
```

### Automated Backup Script
Set up a daily cron job to back up the database:
```bash
# Add to crontab (crontab -e)
0 2 * * * sqlite3 /opt/planbridge/data/sih_bridge.db ".backup '/opt/planbridge/data/backups/sih_bridge_$(date +\%Y\%m\%d).db'"
```

---

## 7. Production Verification Checklist

Before opening the platform to end users, verify the following:
* [x] **Health check**: `curl http://localhost:8000/health` returns `"status": "healthy"`.
* [x] **Test suite**: Run `pytest` — 17 of 17 tests must pass (100% test pass rate).
* [x] **Supervisor Voice Agent**: Test submitting Hinglish audio dictations on `/api/ingest/voice` and Tab 2.
* [x] **Contradiction & Ghost Progress Shield**: Verify precedence clashes trigger warnings and stop-work alerts on DAG/curing checks.
* [x] **Institutional Memory Copilot**: Verify Kahneman Optimism Bias Factors (OBF) computed against historical projects on Tab 7.
* [x] **Cryptographic Audit Ledger**: Confirm all updates write immutable SHA-256 hash-chained records with timestamps.
* [x] **Primavera P6 & MS Project Round-Trip**: Download XML exports from `/api/export/p6-xml` and `/api/export/ms-project-xml` and verify standard schema validity.
