#!/usr/bin/env bash

# Quick deployment script for Moonshot LLM Evaluation Platform
# Supports: docker, aws-ec2, gcp, local

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
error() { echo -e "${RED}[error]${NC} $*" >&2; }

usage() {
    cat <<EOF
Moonshot Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    docker          Deploy using Docker Compose (recommended)
    aws-ec2         Deploy to AWS EC2 instance
    gcp             Deploy to GCP Cloud Run
    local           Deploy locally (development)
    stop            Stop running deployment
    status          Check deployment status
    logs            View deployment logs

Options:
    -h, --help      Show this help message
    -e, --env FILE  Specify environment file (default: .env)
    -p, --port PORT Specify UI port (default: 3000)

Examples:
    $0 docker                    # Deploy with Docker Compose
    $0 docker --env .env.prod    # Deploy with specific env file
    $0 aws-ec2                   # Deploy to AWS EC2
    $0 stop                      # Stop deployment
    $0 logs                      # View logs

EOF
}

check_requirements() {
    log "Checking requirements..."
    
    local missing=()
    
    if ! command -v docker &>/dev/null; then
        missing+=("docker")
    fi
    
    if [ "$1" = "docker" ] && ! command -v docker-compose &>/dev/null; then
        missing+=("docker-compose")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing required tools: ${missing[*]}"
        error "Please install missing tools and try again"
        exit 1
    fi
    
    log "✓ All requirements satisfied"
}

check_env_file() {
    local env_file="${ENV_FILE:-.env}"
    
    if [ ! -f "$env_file" ]; then
        warn "Environment file not found: $env_file"
        
        if [ -f ".env.example" ]; then
            log "Creating $env_file from .env.example"
            cp .env.example "$env_file"
            
            warn "⚠️  Please edit $env_file and add your API keys before deploying"
            warn "Required: OPENAI_API_KEY"
            
            read -p "Press Enter to open $env_file in editor, or Ctrl+C to exit..."
            ${EDITOR:-nano} "$env_file"
        else
            error "No .env.example found. Cannot create environment file."
            exit 1
        fi
    fi
    
    # Check if API key is set
    if ! grep -q "OPENAI_API_KEY=sk-" "$env_file" 2>/dev/null; then
        warn "⚠️  OPENAI_API_KEY not configured in $env_file"
        warn "The application will not work without API keys"
    fi
    
    log "✓ Environment file ready: $env_file"
}

deploy_docker() {
    log "Deploying with Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    check_requirements docker
    check_env_file
    
    # Build and start services
    log "Building Docker images..."
    docker-compose build
    
    log "Starting services..."
    docker-compose up -d
    
    log "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    if docker-compose ps | grep -q "healthy\|Up"; then
        log "✅ Deployment successful!"
        log ""
        log "Access Moonshot at:"
        log "  Web UI:  http://localhost:3000"
        log "  API:     http://localhost:5000"
        log ""
        log "View logs: docker-compose logs -f"
        log "Stop:      docker-compose down"
    else
        error "Deployment failed. Check logs with: docker-compose logs"
        exit 1
    fi
}

deploy_aws_ec2() {
    log "Deploying to AWS EC2..."
    
    # Check AWS CLI
    if ! command -v aws &>/dev/null; then
        error "AWS CLI not installed. Install from: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    warn "This will guide you through EC2 deployment"
    warn "Make sure you have:"
    warn "  1. AWS credentials configured"
    warn "  2. SSH key pair created"
    warn "  3. VPC and security group ready"
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    # Get user inputs
    read -p "EC2 instance type (default: t3.medium): " INSTANCE_TYPE
    INSTANCE_TYPE=${INSTANCE_TYPE:-t3.medium}
    
    read -p "SSH key name: " KEY_NAME
    read -p "Security group ID: " SG_ID
    read -p "Subnet ID: " SUBNET_ID
    
    # Launch instance
    log "Launching EC2 instance..."
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id ami-0c55b159cbfafe1f0 \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SG_ID" \
        --subnet-id "$SUBNET_ID" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=moonshot-eval}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    log "Instance created: $INSTANCE_ID"
    log "Waiting for instance to be running..."
    
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
    
    # Get public IP
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    log "Instance ready at: $PUBLIC_IP"
    log ""
    log "Next steps:"
    log "  1. SSH to instance: ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
    log "  2. Clone repository: git clone <your-repo> && cd gaia-lab"
    log "  3. Run setup: ./scripts/deploy.sh docker"
}

deploy_gcp() {
    log "Deploying to GCP Cloud Run..."
    
    if ! command -v gcloud &>/dev/null; then
        error "gcloud CLI not installed. Install from: https://cloud.google.com/sdk"
        exit 1
    fi
    
    read -p "GCP Project ID: " PROJECT_ID
    read -p "Region (default: us-central1): " REGION
    REGION=${REGION:-us-central1}
    
    log "Setting project..."
    gcloud config set project "$PROJECT_ID"
    
    log "Building container..."
    gcloud builds submit --tag "gcr.io/$PROJECT_ID/moonshot-eval"
    
    log "Deploying to Cloud Run..."
    gcloud run deploy moonshot-eval \
        --image "gcr.io/$PROJECT_ID/moonshot-eval" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --port 3000 \
        --memory 4Gi \
        --cpu 2 \
        --set-env-vars NODE_ENV=production
    
    SERVICE_URL=$(gcloud run services describe moonshot-eval \
        --region "$REGION" \
        --format 'value(status.url)')
    
    log "✅ Deployed successfully!"
    log "URL: $SERVICE_URL"
}

deploy_local() {
    log "Deploying locally (development mode)..."
    
    cd "$PROJECT_ROOT"
    check_env_file
    
    # Check if virtual env exists
    if [ ! -d ".venv" ]; then
        log "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    log "Installing dependencies..."
    source .venv/bin/activate
    pip install -r requirements.txt
    
    log "Installing Moonshot assets..."
    python -m moonshot -i moonshot-data -i moonshot-ui -u || true
    
    log "Starting Moonshot..."
    log "Press Ctrl+C to stop"
    python -m moonshot web
}

stop_deployment() {
    log "Stopping deployment..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
        log "✓ Docker containers stopped"
    fi
    
    # Kill any running moonshot processes
    pkill -f "moonshot web" || true
    log "✓ Local processes stopped"
}

show_status() {
    log "Deployment Status"
    log "================="
    
    # Check Docker
    if command -v docker &>/dev/null && docker-compose ps 2>/dev/null | grep -q "Up"; then
        log "✓ Docker deployment: RUNNING"
        docker-compose ps
    else
        log "✗ Docker deployment: STOPPED"
    fi
    
    # Check local process
    if pgrep -f "moonshot web" >/dev/null; then
        log "✓ Local deployment: RUNNING"
    else
        log "✗ Local deployment: STOPPED"
    fi
}

show_logs() {
    if [ -f "docker-compose.yml" ] && docker-compose ps | grep -q "Up"; then
        docker-compose logs -f
    elif [ -f "moonshot.log" ]; then
        tail -f moonshot.log moonshot-web.log
    else
        error "No deployment found"
        exit 1
    fi
}

# Parse arguments
COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    docker)
        deploy_docker "$@"
        ;;
    aws-ec2)
        deploy_aws_ec2 "$@"
        ;;
    gcp)
        deploy_gcp "$@"
        ;;
    local)
        deploy_local "$@"
        ;;
    stop)
        stop_deployment "$@"
        ;;
    status)
        show_status "$@"
        ;;
    logs)
        show_logs "$@"
        ;;
    -h|--help|help)
        usage
        exit 0
        ;;
    "")
        usage
        exit 1
        ;;
    *)
        error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
