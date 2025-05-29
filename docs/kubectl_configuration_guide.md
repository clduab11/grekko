# Kubectl Configuration Guide - Grekko Trading Production Cluster

## Overview

This guide provides step-by-step instructions for configuring kubectl access to the `grekko-trading-prod` Kubernetes cluster. The configuration follows security best practices with proper credential management and RBAC controls.

## Prerequisites

- kubectl v1.28+ installed (✅ Confirmed: v1.32.2)
- Access to cluster credentials (certificates, tokens, API server endpoint)
- Proper network connectivity to the cluster
- Valid user account with appropriate RBAC permissions

## Cluster Information

- **Cluster Name**: `grekko-trading-prod`
- **Kubernetes Version**: v1.28
- **Architecture**: 9 nodes (3 masters, 6 workers)
- **Namespaces**: `trading-prod`, `monitoring`, `istio-system`, `backup-system`

## Configuration Methods

### Method 1: Using Cloud Provider CLI (Recommended)

If your cluster is hosted on a cloud provider, use their CLI tools:

#### AWS EKS
```bash
# Configure AWS credentials first
aws configure

# Update kubeconfig for EKS cluster
aws eks update-kubeconfig --region <region> --name grekko-trading-prod

# Verify connection
kubectl get nodes
```

#### Google GKE
```bash
# Authenticate with Google Cloud
gcloud auth login

# Get cluster credentials
gcloud container clusters get-credentials grekko-trading-prod --zone <zone> --project <project-id>

# Verify connection
kubectl get nodes
```

#### Azure AKS
```bash
# Login to Azure
az login

# Get cluster credentials
az aks get-credentials --resource-group <resource-group> --name grekko-trading-prod

# Verify connection
kubectl get nodes
```

### Method 2: Manual Kubeconfig Configuration

If you have the cluster certificates and API server details, follow these steps:

#### Step 1: Obtain Required Information

You need the following information from your cluster administrator:

1. **API Server Endpoint**: `https://api.grekko-trading-prod.example.com:6443`
2. **Cluster CA Certificate**: Base64-encoded cluster certificate
3. **Client Certificate**: Base64-encoded user certificate
4. **Client Key**: Base64-encoded user private key
5. **Service Account Token** (alternative to certificates)

#### Step 2: Create Kubeconfig File

Create the kubeconfig file at `~/.kube/config`:

```yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: <BASE64_CLUSTER_CA_CERT>
    server: https://api.grekko-trading-prod.example.com:6443
  name: grekko-trading-prod
contexts:
- context:
    cluster: grekko-trading-prod
    namespace: trading-prod
    user: grekko-admin
  name: grekko-trading-prod
current-context: grekko-trading-prod
users:
- name: grekko-admin
  user:
    client-certificate-data: <BASE64_CLIENT_CERT>
    client-key-data: <BASE64_CLIENT_KEY>
```

#### Step 3: Alternative Token-Based Authentication

If using service account tokens instead of certificates:

```yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: <BASE64_CLUSTER_CA_CERT>
    server: https://api.grekko-trading-prod.example.com:6443
  name: grekko-trading-prod
contexts:
- context:
    cluster: grekko-trading-prod
    namespace: trading-prod
    user: grekko-admin
  name: grekko-trading-prod
current-context: grekko-trading-prod
users:
- name: grekko-admin
  user:
    token: <SERVICE_ACCOUNT_TOKEN>
```

## Security Best Practices

### 1. Secure Credential Storage

```bash
# Set restrictive permissions on kubeconfig
chmod 600 ~/.kube/config

# Ensure .kube directory has proper permissions
chmod 700 ~/.kube
```

### 2. Use Service Accounts with RBAC

Create a dedicated service account with minimal required permissions:

```yaml
# service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: deployment-monitor
  namespace: trading-prod
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: deployment-monitor
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: deployment-monitor
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: deployment-monitor
subjects:
- kind: ServiceAccount
  name: deployment-monitor
  namespace: trading-prod
```

### 3. Extract Service Account Token

```bash
# Apply the service account configuration
kubectl apply -f service-account.yaml

# Get the service account token
kubectl get secret $(kubectl get serviceaccount deployment-monitor -n trading-prod -o jsonpath='{.secrets[0].name}') -n trading-prod -o jsonpath='{.data.token}' | base64 --decode
```

## Verification Steps

### 1. Test Basic Connectivity

```bash
# Check cluster info
kubectl cluster-info

# List nodes
kubectl get nodes

# Check namespaces
kubectl get namespaces
```

### 2. Test Namespace Access

```bash
# List pods in trading-prod namespace
kubectl get pods -n trading-prod

# Check services
kubectl get services -n trading-prod

# Verify monitoring namespace access
kubectl get pods -n monitoring
```

### 3. Test Monitoring Access

```bash
# Port-forward to Prometheus (if accessible)
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Port-forward to Grafana (if accessible)
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Refused
```bash
# Check if API server endpoint is correct
nslookup api.grekko-trading-prod.example.com

# Test connectivity
telnet api.grekko-trading-prod.example.com 6443
```

#### 2. Certificate Verification Failed
```bash
# Check cluster CA certificate
kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 --decode

# Verify certificate validity
openssl x509 -in cluster-ca.crt -text -noout
```

#### 3. Authentication Failed
```bash
# Check current context
kubectl config current-context

# View user configuration
kubectl config view --raw -o jsonpath='{.users[0].user}'

# Test with verbose output
kubectl get nodes -v=8
```

#### 4. Authorization Failed (RBAC)
```bash
# Check current user permissions
kubectl auth can-i get pods --namespace=trading-prod

# List all permissions for current user
kubectl auth can-i --list --namespace=trading-prod
```

## Environment-Specific Configurations

### Development Environment
```bash
# Switch to development context (if available)
kubectl config use-context grekko-trading-dev
```

### Staging Environment
```bash
# Switch to staging context (if available)
kubectl config use-context grekko-trading-staging
```

### Production Environment
```bash
# Switch to production context
kubectl config use-context grekko-trading-prod

# Verify you're in the correct environment
kubectl config current-context
```

## Monitoring and Observability Access

### Prometheus Access
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Access Prometheus UI
open http://localhost:9090
```

### Grafana Access
```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000 &

# Access Grafana UI
open http://localhost:3000
```

### Application Logs
```bash
# View logs for specific services
kubectl logs -f deployment/coinbase-integration-active -n trading-prod
kubectl logs -f deployment/metamask-integration-active -n trading-prod
kubectl logs -f deployment/risk-management-active -n trading-prod
kubectl logs -f deployment/agent-coordination-active -n trading-prod

# View logs for all trading system components
kubectl logs -f -l app.kubernetes.io/part-of=trading-system -n trading-prod
```

## Security Considerations

### 1. Network Security
- Ensure VPN connection if cluster is behind private network
- Verify firewall rules allow kubectl traffic (port 6443)
- Use secure endpoints (HTTPS) for API server

### 2. Credential Management
- Never commit kubeconfig files to version control
- Use environment-specific kubeconfig files
- Rotate certificates and tokens regularly
- Use short-lived tokens when possible

### 3. Access Control
- Follow principle of least privilege
- Use namespace-specific service accounts
- Regularly audit RBAC permissions
- Monitor kubectl access logs

## Next Steps

1. **Obtain Cluster Credentials**: Contact your cluster administrator for:
   - API server endpoint
   - Cluster CA certificate
   - User certificates or service account token

2. **Configure kubectl**: Use one of the methods above to configure kubectl

3. **Verify Access**: Run the verification steps to ensure proper connectivity

4. **Set Up Monitoring**: Configure port-forwarding for Prometheus and Grafana access

5. **Test Deployment Monitoring**: Verify you can view pod status, logs, and metrics

## Support

For assistance with kubectl configuration:
- **DevOps Team**: devops@grekko.trading
- **Security Team**: security@grekko.trading
- **Documentation**: [Production Deployment Guide](./production_deployment_guide.md)

---

**Last Updated**: 2025-05-29  
**Version**: 1.0  
**Maintained By**: DevOps Team