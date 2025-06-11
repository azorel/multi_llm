#!/bin/bash
# Deployment script for Autonomous Multi-LLM Agent System

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_IMAGE="autonomous-agent"
DOCKER_TAG="${DOCKER_TAG:-latest}"
ENVIRONMENT="${ENVIRONMENT:-development}"
NAMESPACE="${NAMESPACE:-autonomous-agent}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check requirements
check_requirements() {
    log_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check kubectl for Kubernetes deployment
    if [[ "$ENVIRONMENT" == "production" ]] && ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed (required for production deployment)"
        exit 1
    fi
    
    # Check docker-compose for local deployment
    if [[ "$ENVIRONMENT" == "development" ]] && ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed (required for development deployment)"
        exit 1
    fi
    
    log_success "Requirements check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Build with appropriate target
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker build --target production -t "${DOCKER_IMAGE}:${DOCKER_TAG}" .
    else
        docker build --target development -t "${DOCKER_IMAGE}:${DOCKER_TAG}" .
    fi
    
    log_success "Docker image built: ${DOCKER_IMAGE}:${DOCKER_TAG}"
}

# Deploy to development (Docker Compose)
deploy_development() {
    log_info "Deploying to development environment..."
    
    cd "$PROJECT_ROOT"
    
    # Check for .env file
    if [[ ! -f .env ]]; then
        log_warning ".env file not found. Creating template..."
        cat > .env << EOF
# API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
NOTION_API_KEY=your_notion_key_here
GITHUB_TOKEN=your_github_token_here

# Notion Database IDs
NOTION_TASKS_DB_ID=your_tasks_db_id
NOTION_KNOWLEDGE_DB_ID=your_knowledge_db_id
NOTION_LOGS_DB_ID=your_logs_db_id

# GitHub Configuration
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repo_name

# Alert Configuration
ALERT_WEBHOOK_URL=your_webhook_url
EOF
        log_warning "Please edit .env file with your actual API keys and configuration"
        return 1
    fi
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Development deployment successful!"
        log_info "API available at: http://localhost:8000"
        log_info "API docs available at: http://localhost:8000/docs"
        log_info "Grafana available at: http://localhost:3000 (admin/admin)"
        log_info "Prometheus available at: http://localhost:9091"
    else
        log_error "Health check failed"
        return 1
    fi
}

# Deploy to production (Docker Swarm/Compose)
deploy_production() {
    log_info "Deploying to production environment..."
    
    cd "$PROJECT_ROOT"
    
    # Check if required environment variables are set
    if [[ -z "$OPENAI_API_KEY" || -z "$ANTHROPIC_API_KEY" || -z "$GOOGLE_API_KEY" ]]; then
        log_error "Required API keys not found in environment variables"
        log_error "Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, and GOOGLE_API_KEY"
        return 1
    fi
    
    # Create production docker-compose override
    log_info "Creating production configuration..."
    cat > docker-compose.prod.yml << EOF
version: '3.8'
services:
  autonomous-agent:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - WORKER_COUNT=4
      - MAX_CONCURRENT_TASKS=20
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  redis:
    deploy:
      resources:
        limits:
          memory: 512M
    restart: unless-stopped
    
  postgresql:
    deploy:
      resources:
        limits:
          memory: 1G
    restart: unless-stopped
EOF

    # Deploy using docker-compose
    log_info "Starting production deployment..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    # Wait for deployment
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    log_info "Checking service health..."
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Production deployment successful!"
        log_info "Service available at: http://localhost:8000"
        log_info "API documentation: http://localhost:8000/docs"
        log_info "Health check: http://localhost:8000/health"
        
        # Show running containers
        log_info "Running containers:"
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
    else
        log_error "Health check failed - checking container logs..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=20
        return 1
    fi
}

# Deploy to staging
deploy_staging() {
    log_info "Deploying to staging environment..."
    NAMESPACE="autonomous-agent-staging"
    deploy_production
}

# Rollback deployment
rollback() {
    log_info "Rolling back deployment..."
    
    if [[ "$ENVIRONMENT" == "production" ]] || [[ "$ENVIRONMENT" == "staging" ]]; then
        kubectl rollout undo deployment/autonomous-agent -n "$NAMESPACE"
        kubectl rollout status deployment/autonomous-agent -n "$NAMESPACE"
        log_success "Rollback completed"
    else
        log_info "Restarting development environment..."
        cd "$PROJECT_ROOT"
        docker-compose restart
        log_success "Development environment restarted"
    fi
}

# Show deployment status
status() {
    log_info "Checking deployment status..."
    
    if [[ "$ENVIRONMENT" == "production" ]] || [[ "$ENVIRONMENT" == "staging" ]]; then
        echo "Kubernetes Status:"
        kubectl get all -n "$NAMESPACE"
        echo ""
        echo "Pod Status:"
        kubectl get pods -n "$NAMESPACE" -o wide
        echo ""
        echo "Service Status:"
        kubectl get services -n "$NAMESPACE"
    else
        echo "Docker Compose Status:"
        cd "$PROJECT_ROOT"
        docker-compose ps
    fi
}

# Cleanup deployment
cleanup() {
    log_info "Cleaning up deployment..."
    
    if [[ "$ENVIRONMENT" == "production" ]] || [[ "$ENVIRONMENT" == "staging" ]]; then
        kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
        log_success "Kubernetes resources cleaned up"
    else
        cd "$PROJECT_ROOT"
        docker-compose down -v
        docker system prune -f
        log_success "Development environment cleaned up"
    fi
}

# Show logs
logs() {
    if [[ "$ENVIRONMENT" == "production" ]] || [[ "$ENVIRONMENT" == "staging" ]]; then
        kubectl logs -l app=autonomous-agent -n "$NAMESPACE" --tail=100 -f
    else
        cd "$PROJECT_ROOT"
        docker-compose logs -f autonomous-agent
    fi
}

# Main deployment function
deploy() {
    check_requirements
    build_image
    
    case "$ENVIRONMENT" in
        development)
            deploy_development
            ;;
        staging)
            deploy_staging
            ;;
        production)
            deploy_production
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    deploy      Deploy the application
    rollback    Rollback to previous version
    status      Show deployment status
    cleanup     Clean up deployment
    logs        Show application logs
    build       Build Docker image only
    help        Show this help message

Environment Variables:
    ENVIRONMENT     Target environment (development|staging|production)
    DOCKER_TAG      Docker image tag (default: latest)
    NAMESPACE       Kubernetes namespace (default: autonomous-agent)

Examples:
    $0 deploy                           # Deploy to development
    ENVIRONMENT=production $0 deploy    # Deploy to production
    $0 status                          # Show deployment status
    $0 logs                            # Show logs
    $0 cleanup                         # Clean up deployment

EOF
}

# Main script logic
case "${1:-help}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup
        ;;
    logs)
        logs
        ;;
    build)
        check_requirements
        build_image
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac