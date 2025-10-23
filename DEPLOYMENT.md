# Deployment Guide: Hosting Moonshot for Team/Enterprise Use

> **Goal**: Deploy the Moonshot LLM evaluation system to a cloud or enterprise server for team collaboration

---

## 📋 Table of Contents

1. [Quick Start with Docker](#quick-start-with-docker)
2. [Cloud Platform Deployment](#cloud-platform-deployment)
3. [Enterprise Server Deployment](#enterprise-server-deployment)
4. [Security & Access Control](#security--access-control)
5. [Environment Configuration](#environment-configuration)
6. [Team Collaboration Setup](#team-collaboration-setup)

---

## 🐳 Quick Start with Docker

### Option 1: Docker Compose (Recommended)

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  moonshot:
    build: .
    ports:
      - "3000:3000"  # Web UI
      - "5000:5000"  # API
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TOGETHER_API_KEY=${TOGETHER_API_KEY}
      - NODE_ENV=production
    volumes:
      - ./reports:/app/reports
      - ./moonshot-data:/app/moonshot-data
    restart: unless-stopped
    networks:
      - moonshot-network

networks:
  moonshot-network:
    driver: bridge
```

**Create `Dockerfile`:**

```dockerfile
FROM python:3.11-slim

# Install Node.js (required for Moonshot UI)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Install Moonshot data and UI assets
RUN python -m moonshot -i moonshot-data -i moonshot-ui -u

# Expose ports
EXPOSE 3000 5000

# Start Moonshot
CMD ["python", "-m", "moonshot", "web"]
```

**Deploy:**

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Access:**
- Web UI: `http://your-server:3000`
- API: `http://your-server:5000`

---

## ☁️ Cloud Platform Deployment

### AWS Deployment

#### Option A: AWS ECS (Elastic Container Service)

**1. Push Docker image to ECR:**

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t moonshot-llm-eval .
docker tag moonshot-llm-eval:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/moonshot-llm-eval:latest

# Push
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/moonshot-llm-eval:latest
```

**2. Create ECS Task Definition:**

```json
{
  "family": "moonshot-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "moonshot-container",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/moonshot-llm-eval:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        },
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/moonshot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**3. Deploy with Application Load Balancer:**

```bash
# Create ECS service
aws ecs create-service \
  --cluster moonshot-cluster \
  --service-name moonshot-service \
  --task-definition moonshot-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=moonshot-container,containerPort=3000"
```

**Estimated Cost:** ~$50-100/month (Fargate + ALB)

---

#### Option B: AWS EC2

**1. Launch EC2 instance:**
- AMI: Ubuntu 22.04 LTS
- Instance type: t3.medium (2 vCPU, 4 GB RAM) minimum
- Security group: Allow ports 22, 3000, 5000, 80, 443

**2. Setup script:**

```bash
#!/bin/bash
# Save as setup.sh and run on EC2

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/YOUR_ORG/gaia-lab.git
cd gaia-lab

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Run with Docker Compose
docker-compose up -d

# Setup Nginx reverse proxy (optional)
sudo apt-get install -y nginx
sudo tee /etc/nginx/sites-available/moonshot <<EOF
server {
    listen 80;
    server_name moonshot.yourcompany.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/moonshot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

**3. SSL with Let's Encrypt:**

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d moonshot.yourcompany.com
```

**Estimated Cost:** ~$30-50/month (t3.medium EC2)

---

### GCP Deployment (Cloud Run)

**1. Build and push to GCP:**

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build with Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/moonshot-llm-eval

# Deploy to Cloud Run
gcloud run deploy moonshot-eval \
  --image gcr.io/YOUR_PROJECT_ID/moonshot-llm-eval \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 \
  --memory 4Gi \
  --cpu 2 \
  --set-env-vars NODE_ENV=production \
  --set-secrets OPENAI_API_KEY=openai-key:latest
```

**Estimated Cost:** ~$20-40/month (pay per use)

---

### Azure Deployment (Container Instances)

```bash
# Create resource group
az group create --name moonshot-rg --location eastus

# Create container registry
az acr create --resource-group moonshot-rg --name moonshotregistry --sku Basic

# Build and push
az acr build --registry moonshotregistry --image moonshot-llm-eval:latest .

# Deploy container
az container create \
  --resource-group moonshot-rg \
  --name moonshot-eval \
  --image moonshotregistry.azurecr.io/moonshot-llm-eval:latest \
  --cpu 2 \
  --memory 4 \
  --registry-login-server moonshotregistry.azurecr.io \
  --registry-username $(az acr credential show --name moonshotregistry --query username -o tsv) \
  --registry-password $(az acr credential show --name moonshotregistry --query passwords[0].value -o tsv) \
  --dns-name-label moonshot-eval \
  --ports 3000 5000 \
  --environment-variables NODE_ENV=production \
  --secure-environment-variables OPENAI_API_KEY=$OPENAI_API_KEY
```

**Estimated Cost:** ~$35-60/month

---

## 🏢 Enterprise Server Deployment

### On-Premises Server Setup

**Requirements:**
- Ubuntu 20.04+ or RHEL 8+
- 4 GB RAM minimum, 8 GB recommended
- 2 CPU cores minimum, 4 cores recommended
- 50 GB disk space
- Docker or Python 3.11 + Node.js 20

**Installation:**

```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip nodejs npm git

# 2. Clone repository to /opt
sudo mkdir -p /opt/moonshot
sudo chown $(whoami):$(whoami) /opt/moonshot
cd /opt/moonshot
git clone <your-repo-url> .

# 3. Setup Python environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Install Moonshot assets
python -m moonshot -i moonshot-data -i moonshot-ui -u

# 6. Create systemd service
sudo tee /etc/systemd/system/moonshot.service <<EOF
[Unit]
Description=Moonshot LLM Evaluation Platform
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=/opt/moonshot
Environment="PATH=/opt/moonshot/.venv/bin"
ExecStart=/opt/moonshot/.venv/bin/python -m moonshot web
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable moonshot
sudo systemctl start moonshot

# 8. Check status
sudo systemctl status moonshot
```

**Access:**
- Web UI: `http://your-server-ip:3000`
- API: `http://your-server-ip:5000`

---

## 🔐 Security & Access Control

### 1. API Key Management

**Use Environment Variables (Never commit keys!):**

```bash
# .env file (gitignored)
OPENAI_API_KEY=sk-proj-xxxxx
TOGETHER_API_KEY=xxxxx
ADMIN_PASSWORD=strong_password_here
```

**For cloud deployments, use secret managers:**

- **AWS**: AWS Secrets Manager or Systems Manager Parameter Store
- **GCP**: Secret Manager
- **Azure**: Key Vault

**Example AWS Secrets Manager:**

```bash
# Store secret
aws secretsmanager create-secret \
  --name moonshot/openai-api-key \
  --secret-string "sk-proj-xxxxx"

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id moonshot/openai-api-key \
  --query SecretString \
  --output text
```

---

### 2. Authentication & Authorization

**Option A: Nginx Basic Auth (Simple)**

```nginx
# Add to Nginx config
location / {
    auth_basic "Moonshot Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:3000;
}
```

```bash
# Create users
sudo apt-get install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd user1
sudo htpasswd /etc/nginx/.htpasswd user2
```

**Option B: OAuth2 Proxy (Enterprise)**

```yaml
# docker-compose.yml with OAuth2 Proxy
services:
  oauth2-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:latest
    command:
      - --provider=google
      - --email-domain=yourcompany.com
      - --upstream=http://moonshot:3000
      - --http-address=0.0.0.0:4180
    environment:
      OAUTH2_PROXY_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      OAUTH2_PROXY_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      OAUTH2_PROXY_COOKIE_SECRET: ${COOKIE_SECRET}
    ports:
      - "4180:4180"
    depends_on:
      - moonshot
```

---

### 3. Network Security

**Firewall Rules:**

```bash
# Ubuntu/Debian with ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 3000/tcp   # Block direct access to Moonshot
sudo ufw deny 5000/tcp   # Block direct API access
sudo ufw enable
```

**Security Groups (AWS):**

```bash
# Allow only your company IP range
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 443 \
  --cidr YOUR_COMPANY_IP_RANGE/32
```

---

### 4. SSL/TLS Configuration

**Let's Encrypt (Free):**

```bash
sudo certbot --nginx -d moonshot.yourcompany.com
```

**Corporate Certificate:**

```nginx
server {
    listen 443 ssl;
    server_name moonshot.yourcompany.com;

    ssl_certificate /etc/ssl/certs/moonshot.crt;
    ssl_certificate_key /etc/ssl/private/moonshot.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3000;
    }
}
```

---

## 🌐 Environment Configuration

### Production `.env` Template

```bash
# API Keys (use secret manager in production)
OPENAI_API_KEY=
TOGETHER_API_KEY=

# Application Settings
NODE_ENV=production
PORT=3000
API_PORT=5000

# Database (if using external storage)
DATABASE_URL=

# Logging
LOG_LEVEL=info
LOG_FILE=/var/log/moonshot/app.log

# CORS Settings (restrict to your domain)
ALLOWED_ORIGINS=https://moonshot.yourcompany.com

# Session/Auth
SESSION_SECRET=
COOKIE_SECURE=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_MS=900000

# Storage
REPORTS_DIR=/data/moonshot/reports
DATASETS_DIR=/data/moonshot/datasets
```

---

## 👥 Team Collaboration Setup

### 1. Shared Reports Storage

**AWS S3 Backend:**

```python
# Add to your configuration
import boto3

s3 = boto3.client('s3')

def save_report(report_data, report_id):
    s3.put_object(
        Bucket='moonshot-reports',
        Key=f'reports/{report_id}.json',
        Body=json.dumps(report_data)
    )
```

**Shared Network Drive (Enterprise):**

```bash
# Mount shared drive
sudo mount -t nfs nfs-server.company.com:/moonshot/reports /mnt/moonshot-reports

# Add to /etc/fstab for persistence
echo "nfs-server.company.com:/moonshot/reports /mnt/moonshot-reports nfs defaults 0 0" | sudo tee -a /etc/fstab
```

---

### 2. Multi-User Access Patterns

**Pattern 1: Shared Instance**
- Single Moonshot instance
- All users access same UI
- Shared API key (tracked usage)
- Good for: Small teams (< 10 people)

**Pattern 2: User-specific API Keys**
- Configure per-user API keys
- Track usage per user
- Good for: Medium teams with budget allocation

**Pattern 3: Multi-tenant Deployment**
- Separate instances per team/project
- Isolated resources and costs
- Good for: Large organizations

---

### 3. Usage Tracking & Cost Management

**Track API Usage:**

```python
# middleware/usage_tracker.py
import time
from functools import wraps

def track_usage(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('user_id', 'unknown')
        start_time = time.time()
        
        result = await func(*args, **kwargs)
        
        duration = time.time() - start_time
        log_usage(user, duration, result.get('tokens_used'))
        
        return result
    return wrapper
```

---

## 📊 Monitoring & Logging

### Application Monitoring

**Prometheus + Grafana:**

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**CloudWatch (AWS):**

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure metrics
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/config.json
```

---

## 🚀 Deployment Checklist

- [ ] Choose deployment platform (Docker/Cloud/On-prem)
- [ ] Setup secret management for API keys
- [ ] Configure SSL/TLS certificates
- [ ] Implement authentication/authorization
- [ ] Configure firewall/security groups
- [ ] Setup backup strategy for reports
- [ ] Configure monitoring and logging
- [ ] Test API key rotation procedure
- [ ] Document access procedures for team
- [ ] Setup cost alerts (cloud deployments)
- [ ] Create disaster recovery plan
- [ ] Schedule regular security updates

---

## 💰 Cost Comparison

| Platform | Monthly Cost | Setup Time | Scalability | Best For |
|----------|-------------|------------|-------------|----------|
| **Docker on EC2** | $30-50 | 2-4 hours | Manual | Small teams |
| **AWS ECS/Fargate** | $50-100 | 4-6 hours | Auto | Medium teams |
| **GCP Cloud Run** | $20-40 | 1-2 hours | Auto | Variable usage |
| **Azure Container** | $35-60 | 2-3 hours | Manual | Azure shops |
| **On-premises** | Hardware only | 4-8 hours | Manual | Enterprise |

*Note: Costs exclude API usage (OpenAI/etc.) which scales with evaluation volume*

---

## 📞 Support & Troubleshooting

### Common Issues

**Port already in use:**
```bash
sudo lsof -ti:3000 | xargs kill -9
```

**Permissions issues:**
```bash
sudo chown -R $(whoami):$(whoami) /opt/moonshot
```

**Memory issues:**
```bash
# Increase Docker memory limit
docker update --memory="4g" moonshot-container
```

---

## 📚 Additional Resources

- [Moonshot Documentation](https://github.com/aiverify-foundation/moonshot)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [AWS ECS Guide](https://docs.aws.amazon.com/ecs/)
- [Nginx Configuration](https://nginx.org/en/docs/)

---

**Last Updated**: 2025-10-24  
**Maintained by**: Gaia Lab Team  
**Contact**: devops@yourcompany.com
