#!/bin/bash

# Production Deployment Script for Grekko Trading System
# Implements Blue-Green Deployment with Zero-Downtime Updates
# Includes comprehensive validation, backup, and rollback capabilities

set -euo pipefail

# Configuration
NAMESPACE="trading-prod"
DEPLOYMENT_TIMEOUT="600s"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10
BACKUP_RETENTION_DAYS=30
LOG_FILE="/tmp/grekko-deployment-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
    
    # Check required secrets
    local required_secrets=("trading-secrets")
    for secret in "${required_secrets[@]}"; do
        if ! kubectl get secret "$secret" -n "$NAMESPACE" &> /dev/null; then
            error "Required secret $secret not found in namespace $NAMESPACE"
            exit 1
        fi
    done
    
    success "Prerequisites check passed"
}

# Backup current deployment state
backup_deployment_state() {
    log "Creating backup of current deployment state..."
    
    local backup_dir="/tmp/grekko-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup deployments
    kubectl get deployments -n "$NAMESPACE" -o yaml > "$backup_dir/deployments.yaml"
    
    # Backup services
    kubectl get services -n "$NAMESPACE" -o yaml > "$backup_dir/services.yaml"
    
    # Backup configmaps
    kubectl get configmaps -n "$NAMESPACE" -o yaml > "$backup_dir/configmaps.yaml"
    
    # Backup ingress
    kubectl get ingress -n "$NAMESPACE" -o yaml > "$backup_dir/ingress.yaml"
    
    # Create backup archive
    tar -czf "/tmp/grekko-backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C "/tmp" "$(basename "$backup_dir")"
    
    # Store backup location for rollback
    echo "$backup_dir" > /tmp/grekko-last-backup
    
    success "Backup created at $backup_dir"
}

# Database backup
backup_databases() {
    log "Creating database backups..."
    
    # PostgreSQL backup
    kubectl exec -n "$NAMESPACE" deployment/postgresql-cluster -- pg_dumpall -U postgres > "/tmp/postgresql-backup-$(date +%Y%m%d-%H%M%S).sql"
    
    # Redis backup
    kubectl exec -n "$NAMESPACE" deployment/redis-cluster -- redis-cli BGSAVE
    
    success "Database backups completed"
}

# Validate container images
validate_images() {
    log "Validating container images..."
    
    local images=(
        "grekko/coinbase-integration:latest"
        "grekko/metamask-integration:latest"
        "grekko/risk-management:latest"
        "grekko/agent-coordination:latest"
    )
    
    for image in "${images[@]}"; do
        if ! docker pull "$image" &> /dev/null; then
            error "Failed to pull image: $image"
            exit 1
        fi
        
        # Security scan (if trivy is available)
        if command -v trivy &> /dev/null; then
            log "Scanning image $image for vulnerabilities..."
            if ! trivy image --exit-code 1 --severity HIGH,CRITICAL "$image"; then
                error "Security vulnerabilities found in $image"
                exit 1
            fi
        fi
    done
    
    success "All images validated successfully"
}

# Deploy infrastructure components
deploy_infrastructure() {
    log "Deploying infrastructure components..."
    
    # Deploy databases
    kubectl apply -f k8s/databases/ -n "$NAMESPACE"
    
    # Deploy message bus
    kubectl apply -f k8s/message-bus/ -n "$NAMESPACE"
    
    # Deploy monitoring
    kubectl apply -f k8s/monitoring/ -n monitoring
    
    # Wait for infrastructure to be ready
    log "Waiting for infrastructure components to be ready..."
    kubectl wait --for=condition=available --timeout="$DEPLOYMENT_TIMEOUT" deployment/postgresql-cluster -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout="$DEPLOYMENT_TIMEOUT" deployment/redis-cluster -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout="$DEPLOYMENT_TIMEOUT" deployment/kafka-cluster -n "$NAMESPACE"
    
    success "Infrastructure deployment completed"
}

# Deploy application services (Blue-Green)
deploy_services() {
    local target_version="$1"
    log "Deploying services to $target_version environment..."
    
    # Update deployment manifests with target version
    sed -i.bak "s/version: active/version: $target_version/g" k8s/deployment/production-deployment.yaml
    sed -i.bak "s/version: standby/version: $target_version/g" k8s/deployment/production-deployment.yaml
    
    # Deploy services
    kubectl apply -f k8s/deployment/production-deployment.yaml
    
    # Wait for deployments to be ready
    local deployments=(
        "coinbase-integration-$target_version"
        "metamask-integration-$target_version"
        "risk-management-$target_version"
        "agent-coordination-$target_version"
    )
    
    for deployment in "${deployments[@]}"; do
        log "Waiting for deployment $deployment to be ready..."
        kubectl wait --for=condition=available --timeout="$DEPLOYMENT_TIMEOUT" "deployment/$deployment" -n "$NAMESPACE"
    done
    
    success "Services deployed to $target_version environment"
}

# Health check function
health_check() {
    local target_version="$1"
    log "Performing health checks on $target_version environment..."
    
    local services=(
        "coinbase-integration-$target_version"
        "metamask-integration-$target_version"
        "risk-management-$target_version"
        "agent-coordination-$target_version"
    )
    
    for service in "${services[@]}"; do
        local retries=0
        while [ $retries -lt $HEALTH_CHECK_RETRIES ]; do
            if kubectl exec -n "$NAMESPACE" "deployment/$service" -- curl -f http://localhost:8080/health &> /dev/null; then
                success "Health check passed for $service"
                break
            else
                warning "Health check failed for $service (attempt $((retries + 1))/$HEALTH_CHECK_RETRIES)"
                sleep $HEALTH_CHECK_INTERVAL
                ((retries++))
            fi
        done
        
        if [ $retries -eq $HEALTH_CHECK_RETRIES ]; then
            error "Health check failed for $service after $HEALTH_CHECK_RETRIES attempts"
            return 1
        fi
    done
    
    success "All health checks passed for $target_version environment"
}

# Performance validation
performance_validation() {
    local target_version="$1"
    log "Running performance validation on $target_version environment..."
    
    # Run load tests (if available)
    if [ -f "tests/load/load_test.py" ]; then
        log "Running load tests..."
        python3 tests/load/load_test.py --target="$target_version" --duration=60
    fi
    
    # Check response times
    local services=(
        "coinbase-integration-$target_version"
        "metamask-integration-$target_version"
        "risk-management-$target_version"
        "agent-coordination-$target_version"
    )
    
    for service in "${services[@]}"; do
        local response_time=$(kubectl exec -n "$NAMESPACE" "deployment/$service" -- curl -w "%{time_total}" -s -o /dev/null http://localhost:8080/health)
        if (( $(echo "$response_time > 1.0" | bc -l) )); then
            warning "High response time for $service: ${response_time}s"
        else
            success "Response time for $service: ${response_time}s"
        fi
    done
    
    success "Performance validation completed"
}

# Switch traffic (Blue-Green cutover)
switch_traffic() {
    local target_version="$1"
    log "Switching traffic to $target_version environment..."
    
    # Update load balancer service selector
    kubectl patch service trading-system-lb -n "$NAMESPACE" -p '{"spec":{"selector":{"version":"'$target_version'"}}}'
    
    # Update ingress
    kubectl patch ingress trading-system-ingress -n "$NAMESPACE" -p '{"spec":{"rules":[{"host":"api.grekko.trading","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"trading-system-'$target_version'","port":{"number":80}}}}]}}]}}'
    
    # Wait for traffic switch to propagate
    sleep 30
    
    success "Traffic switched to $target_version environment"
}

# Post-deployment validation
post_deployment_validation() {
    log "Running post-deployment validation..."
    
    # Check all pods are running
    if ! kubectl get pods -n "$NAMESPACE" | grep -v "Running\|Completed"; then
        success "All pods are running"
    else
        error "Some pods are not in running state"
        kubectl get pods -n "$NAMESPACE"
        return 1
    fi
    
    # Check service endpoints
    local endpoints=$(kubectl get endpoints -n "$NAMESPACE" -o json | jq -r '.items[] | select(.subsets | length > 0) | .metadata.name')
    if [ -z "$endpoints" ]; then
        error "No service endpoints available"
        return 1
    fi
    
    # Run integration tests
    if [ -f "tests/integration/test_production.py" ]; then
        log "Running integration tests..."
        python3 -m pytest tests/integration/test_production.py -v
    fi
    
    success "Post-deployment validation completed"
}

# Rollback function
rollback() {
    error "Deployment failed. Initiating rollback..."
    
    if [ -f "/tmp/grekko-last-backup" ]; then
        local backup_dir=$(cat /tmp/grekko-last-backup)
        log "Rolling back to previous state from $backup_dir"
        
        # Restore previous deployment state
        kubectl apply -f "$backup_dir/deployments.yaml"
        kubectl apply -f "$backup_dir/services.yaml"
        kubectl apply -f "$backup_dir/configmaps.yaml"
        kubectl apply -f "$backup_dir/ingress.yaml"
        
        # Wait for rollback to complete
        sleep 60
        
        success "Rollback completed"
    else
        error "No backup found for rollback"
    fi
}

# Cleanup old deployments
cleanup() {
    log "Cleaning up old deployments..."
    
    # Remove old backup files
    find /tmp -name "grekko-backup-*.tar.gz" -mtime +$BACKUP_RETENTION_DAYS -delete
    
    # Clean up unused images
    if command -v docker &> /dev/null; then
        docker image prune -f
    fi
    
    success "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting Grekko Trading System production deployment..."
    
    # Determine target version (blue/green)
    local current_version=$(kubectl get service trading-system-lb -n "$NAMESPACE" -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "blue")
    local target_version
    if [ "$current_version" = "blue" ]; then
        target_version="green"
    else
        target_version="blue"
    fi
    
    log "Current version: $current_version, Target version: $target_version"
    
    # Set trap for cleanup on failure
    trap rollback ERR
    
    # Deployment steps
    check_prerequisites
    backup_deployment_state
    backup_databases
    validate_images
    deploy_infrastructure
    deploy_services "$target_version"
    
    if health_check "$target_version"; then
        performance_validation "$target_version"
        switch_traffic "$target_version"
        post_deployment_validation
        cleanup
        
        success "Deployment completed successfully!"
        log "New active version: $target_version"
        log "Deployment log: $LOG_FILE"
    else
        error "Health checks failed"
        exit 1
    fi
}

# Script execution
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi