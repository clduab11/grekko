#!/bin/bash

# Kubectl Configuration Script for Grekko Trading Production Cluster
# This script helps configure kubectl access to the grekko-trading-prod cluster
# 
# Usage: ./scripts/configure-kubectl.sh
# 
# Prerequisites:
# - kubectl installed (v1.28+)
# - Cluster credentials available
# - Proper network connectivity

set -euo pipefail

# Configuration variables
CLUSTER_NAME="grekko-trading-prod"
CONTEXT_NAME="grekko-trading-prod"
DEFAULT_NAMESPACE="trading-prod"
KUBECONFIG_PATH="$HOME/.kube/config"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl v1.28+ first."
        exit 1
    fi
    
    # Check kubectl version
    KUBECTL_VERSION=$(kubectl version --client 2>/dev/null | grep -o 'v[0-9]\+\.[0-9]\+' | head -1)
    log_info "kubectl version: $KUBECTL_VERSION"
    
    # Create .kube directory if it doesn't exist
    mkdir -p "$HOME/.kube"
    
    log_success "Prerequisites check completed"
}

# Display current kubectl configuration
show_current_config() {
    log_info "Current kubectl configuration:"
    echo "----------------------------------------"
    
    if kubectl config current-context &> /dev/null; then
        echo "Current context: $(kubectl config current-context)"
    else
        echo "No current context set"
    fi
    
    echo "Available contexts:"
    kubectl config get-contexts 2>/dev/null || echo "No contexts configured"
    echo "----------------------------------------"
}

# Configure kubectl using cloud provider CLI
configure_cloud_provider() {
    log_info "Configuring kubectl using cloud provider CLI..."
    
    echo "Select your cloud provider:"
    echo "1) AWS EKS"
    echo "2) Google GKE"
    echo "3) Azure AKS"
    echo "4) Manual configuration"
    echo "5) Skip cloud provider configuration"
    
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            configure_aws_eks
            ;;
        2)
            configure_gke
            ;;
        3)
            configure_aks
            ;;
        4)
            configure_manual
            ;;
        5)
            log_info "Skipping cloud provider configuration"
            ;;
        *)
            log_error "Invalid choice. Please run the script again."
            exit 1
            ;;
    esac
}

# Configure AWS EKS
configure_aws_eks() {
    log_info "Configuring AWS EKS..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI first."
        return 1
    fi
    
    read -p "Enter AWS region (e.g., us-west-2): " aws_region
    
    if [[ -z "$aws_region" ]]; then
        log_error "AWS region is required"
        return 1
    fi
    
    log_info "Updating kubeconfig for EKS cluster..."
    if aws eks update-kubeconfig --region "$aws_region" --name "$CLUSTER_NAME"; then
        log_success "EKS configuration completed"
    else
        log_error "Failed to configure EKS. Please check your AWS credentials and cluster name."
        return 1
    fi
}

# Configure Google GKE
configure_gke() {
    log_info "Configuring Google GKE..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI is not installed. Please install gcloud first."
        return 1
    fi
    
    read -p "Enter GCP project ID: " project_id
    read -p "Enter GCP zone (e.g., us-central1-a): " zone
    
    if [[ -z "$project_id" || -z "$zone" ]]; then
        log_error "Project ID and zone are required"
        return 1
    fi
    
    log_info "Getting cluster credentials..."
    if gcloud container clusters get-credentials "$CLUSTER_NAME" --zone "$zone" --project "$project_id"; then
        log_success "GKE configuration completed"
    else
        log_error "Failed to configure GKE. Please check your credentials and cluster details."
        return 1
    fi
}

# Configure Azure AKS
configure_aks() {
    log_info "Configuring Azure AKS..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install Azure CLI first."
        return 1
    fi
    
    read -p "Enter resource group name: " resource_group
    
    if [[ -z "$resource_group" ]]; then
        log_error "Resource group name is required"
        return 1
    fi
    
    log_info "Getting cluster credentials..."
    if az aks get-credentials --resource-group "$resource_group" --name "$CLUSTER_NAME"; then
        log_success "AKS configuration completed"
    else
        log_error "Failed to configure AKS. Please check your credentials and cluster details."
        return 1
    fi
}

# Manual configuration
configure_manual() {
    log_info "Manual kubectl configuration..."
    log_warning "You will need the following information from your cluster administrator:"
    echo "1. API server endpoint (e.g., https://api.grekko-trading-prod.example.com:6443)"
    echo "2. Cluster CA certificate (base64 encoded)"
    echo "3. Client certificate and key OR service account token"
    echo ""
    
    read -p "Do you have all the required information? (y/n): " has_info
    
    if [[ "$has_info" != "y" && "$has_info" != "Y" ]]; then
        log_warning "Please obtain the required information from your cluster administrator first."
        log_info "Refer to the kubectl configuration guide: docs/kubectl_configuration_guide.md"
        return 1
    fi
    
    read -p "Enter API server endpoint: " api_server
    read -p "Enter path to cluster CA certificate file: " ca_cert_path
    
    if [[ -z "$api_server" || -z "$ca_cert_path" ]]; then
        log_error "API server endpoint and CA certificate are required"
        return 1
    fi
    
    if [[ ! -f "$ca_cert_path" ]]; then
        log_error "CA certificate file not found: $ca_cert_path"
        return 1
    fi
    
    # Configure cluster
    log_info "Configuring cluster..."
    kubectl config set-cluster "$CLUSTER_NAME" \
        --server="$api_server" \
        --certificate-authority="$ca_cert_path" \
        --embed-certs=true
    
    # Configure authentication
    echo "Choose authentication method:"
    echo "1) Client certificate"
    echo "2) Service account token"
    
    read -p "Enter your choice (1-2): " auth_choice
    
    case $auth_choice in
        1)
            configure_cert_auth
            ;;
        2)
            configure_token_auth
            ;;
        *)
            log_error "Invalid choice"
            return 1
            ;;
    esac
    
    # Configure context
    kubectl config set-context "$CONTEXT_NAME" \
        --cluster="$CLUSTER_NAME" \
        --user="grekko-admin" \
        --namespace="$DEFAULT_NAMESPACE"
    
    log_success "Manual configuration completed"
}

# Configure certificate-based authentication
configure_cert_auth() {
    read -p "Enter path to client certificate file: " client_cert_path
    read -p "Enter path to client key file: " client_key_path
    
    if [[ ! -f "$client_cert_path" || ! -f "$client_key_path" ]]; then
        log_error "Certificate or key file not found"
        return 1
    fi
    
    kubectl config set-credentials grekko-admin \
        --client-certificate="$client_cert_path" \
        --client-key="$client_key_path" \
        --embed-certs=true
}

# Configure token-based authentication
configure_token_auth() {
    read -s -p "Enter service account token: " token
    echo ""
    
    if [[ -z "$token" ]]; then
        log_error "Token is required"
        return 1
    fi
    
    kubectl config set-credentials grekko-admin --token="$token"
}

# Set secure permissions
set_secure_permissions() {
    log_info "Setting secure permissions on kubeconfig..."
    
    if [[ -f "$KUBECONFIG_PATH" ]]; then
        chmod 600 "$KUBECONFIG_PATH"
        chmod 700 "$HOME/.kube"
        log_success "Secure permissions set"
    else
        log_warning "Kubeconfig file not found at $KUBECONFIG_PATH"
    fi
}

# Test connection
test_connection() {
    log_info "Testing connection to cluster..."
    
    # Set context
    if kubectl config use-context "$CONTEXT_NAME" &> /dev/null; then
        log_success "Context set to $CONTEXT_NAME"
    else
        log_warning "Failed to set context. Using current context."
    fi
    
    # Test basic connectivity
    if kubectl cluster-info &> /dev/null; then
        log_success "Successfully connected to cluster"
        
        # Show cluster info
        echo "Cluster information:"
        kubectl cluster-info
        
        # Test namespace access
        log_info "Testing namespace access..."
        if kubectl get namespaces &> /dev/null; then
            log_success "Namespace access confirmed"
            echo "Available namespaces:"
            kubectl get namespaces --no-headers | awk '{print "  - " $1}'
        else
            log_warning "Limited namespace access or permissions"
        fi
        
        # Test pod access in trading-prod namespace
        if kubectl get pods -n trading-prod &> /dev/null; then
            log_success "Access to trading-prod namespace confirmed"
        else
            log_warning "No access to trading-prod namespace or no pods running"
        fi
        
    else
        log_error "Failed to connect to cluster. Please check your configuration."
        return 1
    fi
}

# Setup monitoring access
setup_monitoring_access() {
    log_info "Setting up monitoring access..."
    
    echo "Would you like to set up port-forwarding for monitoring services?"
    echo "1) Set up Prometheus port-forward (port 9090)"
    echo "2) Set up Grafana port-forward (port 3000)"
    echo "3) Set up both"
    echo "4) Skip monitoring setup"
    
    read -p "Enter your choice (1-4): " monitor_choice
    
    case $monitor_choice in
        1)
            setup_prometheus_forward
            ;;
        2)
            setup_grafana_forward
            ;;
        3)
            setup_prometheus_forward
            setup_grafana_forward
            ;;
        4)
            log_info "Skipping monitoring setup"
            ;;
        *)
            log_warning "Invalid choice. Skipping monitoring setup."
            ;;
    esac
}

# Setup Prometheus port-forward
setup_prometheus_forward() {
    log_info "Setting up Prometheus port-forward..."
    
    if kubectl get svc prometheus -n monitoring &> /dev/null; then
        log_info "Starting Prometheus port-forward on localhost:9090..."
        log_info "Run: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
        log_info "Access Prometheus at: http://localhost:9090"
    else
        log_warning "Prometheus service not found in monitoring namespace"
    fi
}

# Setup Grafana port-forward
setup_grafana_forward() {
    log_info "Setting up Grafana port-forward..."
    
    if kubectl get svc grafana -n monitoring &> /dev/null; then
        log_info "Starting Grafana port-forward on localhost:3000..."
        log_info "Run: kubectl port-forward -n monitoring svc/grafana 3000:3000"
        log_info "Access Grafana at: http://localhost:3000"
    else
        log_warning "Grafana service not found in monitoring namespace"
    fi
}

# Create service account for monitoring
create_monitoring_service_account() {
    log_info "Creating monitoring service account..."
    
    read -p "Would you like to create a monitoring service account with limited permissions? (y/n): " create_sa
    
    if [[ "$create_sa" == "y" || "$create_sa" == "Y" ]]; then
        # Apply the RBAC configuration
        if kubectl apply -f k8s/cluster/kubeconfig-template.yaml &> /dev/null; then
            log_success "Monitoring service account created"
            
            # Get the service account token
            log_info "Extracting service account token..."
            TOKEN_NAME=$(kubectl get serviceaccount deployment-monitor -n trading-prod -o jsonpath='{.secrets[0].name}' 2>/dev/null)
            
            if [[ -n "$TOKEN_NAME" ]]; then
                TOKEN=$(kubectl get secret "$TOKEN_NAME" -n trading-prod -o jsonpath='{.data.token}' | base64 --decode)
                log_success "Service account token extracted"
                log_info "You can use this token for monitoring access:"
                echo "Token: $TOKEN"
            else
                log_warning "Could not extract service account token automatically"
            fi
        else
            log_warning "Could not create monitoring service account. You may need cluster admin permissions."
        fi
    fi
}

# Display helpful commands
show_helpful_commands() {
    log_info "Helpful kubectl commands for monitoring:"
    echo ""
    echo "Basic cluster information:"
    echo "  kubectl cluster-info"
    echo "  kubectl get nodes"
    echo "  kubectl get namespaces"
    echo ""
    echo "Trading system monitoring:"
    echo "  kubectl get pods -n trading-prod"
    echo "  kubectl get services -n trading-prod"
    echo "  kubectl logs -f deployment/coinbase-integration-active -n trading-prod"
    echo "  kubectl logs -f deployment/metamask-integration-active -n trading-prod"
    echo ""
    echo "Monitoring services:"
    echo "  kubectl get pods -n monitoring"
    echo "  kubectl port-forward -n monitoring svc/prometheus 9090:9090"
    echo "  kubectl port-forward -n monitoring svc/grafana 3000:3000"
    echo ""
    echo "Resource monitoring:"
    echo "  kubectl top nodes"
    echo "  kubectl top pods -n trading-prod"
    echo ""
    echo "For more information, see: docs/kubectl_configuration_guide.md"
}

# Main function
main() {
    echo "========================================"
    echo "Kubectl Configuration for Grekko Trading"
    echo "========================================"
    echo ""
    
    check_prerequisites
    show_current_config
    configure_cloud_provider
    set_secure_permissions
    test_connection
    setup_monitoring_access
    create_monitoring_service_account
    show_helpful_commands
    
    echo ""
    log_success "Kubectl configuration completed!"
    log_info "You can now use kubectl to manage the grekko-trading-prod cluster"
}

# Run main function
main "$@"