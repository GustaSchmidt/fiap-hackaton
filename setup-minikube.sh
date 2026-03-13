#!/bin/bash
set -e

# ============================================================
# FIAP X - Video Processing Platform
# Minikube Local Setup Script
# ============================================================

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Pre-requisites check ---
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v minikube &> /dev/null; then
        log_error "minikube not found. Install: https://minikube.sigs.k8s.io/docs/start/"
        exit 1
    fi

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Install: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        log_error "docker not found. Install: https://docs.docker.com/get-docker/"
        exit 1
    fi

    log_ok "All prerequisites found."
}

# --- Start Minikube ---
start_minikube() {
    log_info "Starting Minikube cluster..."

    if minikube status | grep -q "Running" 2>/dev/null; then
        log_warn "Minikube is already running."
    else
        minikube start \
            --driver=docker \
            --cpus=4 \
            --memory=8192 \
            --disk-size=20g \
            --addons=ingress,metrics-server
    fi

    log_ok "Minikube is running."
}

# --- Build Docker images inside Minikube ---
build_images() {
    log_info "Configuring Docker to use Minikube's Docker daemon..."
    eval $(minikube docker-env)

    log_info "Building Docker images..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    docker build -t fiapx/auth-service:latest "$SCRIPT_DIR/services/auth-service"
    log_ok "auth-service image built."

    docker build -t fiapx/video-upload-service:latest "$SCRIPT_DIR/services/video-upload-service"
    log_ok "video-upload-service image built."

    docker build -t fiapx/video-processing-service:latest "$SCRIPT_DIR/services/video-processing-service"
    log_ok "video-processing-service image built."

    docker build -t fiapx/notification-service:latest "$SCRIPT_DIR/services/notification-service"
    log_ok "notification-service image built."

    docker build -t fiapx/api-gateway:latest "$SCRIPT_DIR/services/api-gateway"
    log_ok "api-gateway image built."

    log_ok "All images built successfully."
}

# --- Deploy to Kubernetes ---
deploy_k8s() {
    log_info "Deploying to Kubernetes..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    K8S_DIR="$SCRIPT_DIR/k8s"

    # Apply in order: namespace -> config -> infrastructure -> services
    kubectl apply -f "$K8S_DIR/namespace.yaml"
    log_ok "Namespace created."

    kubectl apply -f "$K8S_DIR/configmap.yaml"
    log_ok "ConfigMap applied."

    # Secrets (requires envsubst - values come from .env file)
    if [ -f "$SCRIPT_DIR/.env" ]; then
        source "$SCRIPT_DIR/.env"
    fi
    envsubst < "$K8S_DIR/secrets.yaml" | kubectl apply -f -
    log_ok "Secrets applied."

    # Infrastructure
    kubectl apply -f "$K8S_DIR/postgres.yaml"
    kubectl apply -f "$K8S_DIR/redis.yaml"
    kubectl apply -f "$K8S_DIR/rabbitmq.yaml"
    kubectl apply -f "$K8S_DIR/minio.yaml"
    kubectl apply -f "$K8S_DIR/mailhog.yaml"
    log_ok "Infrastructure deployed."

    # Wait for infrastructure to be ready
    log_info "Waiting for infrastructure pods to be ready..."
    kubectl -n fiapx wait --for=condition=ready pod -l app=postgres --timeout=120s 2>/dev/null || log_warn "Postgres still starting..."
    kubectl -n fiapx wait --for=condition=ready pod -l app=redis --timeout=60s 2>/dev/null || log_warn "Redis still starting..."
    kubectl -n fiapx wait --for=condition=ready pod -l app=rabbitmq --timeout=120s 2>/dev/null || log_warn "RabbitMQ still starting..."
    log_ok "Infrastructure is ready."

    # Application services
    kubectl apply -f "$K8S_DIR/auth-service.yaml"
    kubectl apply -f "$K8S_DIR/video-upload-service.yaml"
    kubectl apply -f "$K8S_DIR/video-processing-service.yaml"
    kubectl apply -f "$K8S_DIR/notification-service.yaml"
    kubectl apply -f "$K8S_DIR/api-gateway.yaml"
    log_ok "Application services deployed."

    # Monitoring
    kubectl apply -f "$K8S_DIR/monitoring.yaml"
    log_ok "Monitoring deployed."

    log_info "Waiting for all pods to be ready..."
    sleep 10
    kubectl -n fiapx get pods
}

# --- Print access URLs ---
print_urls() {
    echo ""
    echo "============================================================"
    echo "  FIAP X - Video Processing Platform"
    echo "============================================================"
    echo ""

    MINIKUBE_IP=$(minikube ip)

    echo "  Application:    http://$MINIKUBE_IP:30080"
    echo "  Prometheus:     http://$MINIKUBE_IP:30090"
    echo "  Grafana:        http://$MINIKUBE_IP:30030  (admin/admin)"
    echo "  RabbitMQ Mgmt:  Access via port-forward:"
    echo "    kubectl -n fiapx port-forward svc/rabbitmq 15672:15672"
    echo "  MinIO Console:  Access via port-forward:"
    echo "    kubectl -n fiapx port-forward svc/minio 9001:9001"
    echo "  MailHog:        Access via port-forward:"
    echo "    kubectl -n fiapx port-forward svc/mailhog 8025:8025"
    echo ""
    echo "  To view all pods:"
    echo "    kubectl -n fiapx get pods"
    echo ""
    echo "  To view logs of a service:"
    echo "    kubectl -n fiapx logs -f deployment/<service-name>"
    echo ""
    echo "  To stop:"
    echo "    minikube stop"
    echo ""
    echo "  To delete everything:"
    echo "    kubectl delete namespace fiapx && minikube stop"
    echo ""
    echo "============================================================"
}

# --- Main ---
main() {
    echo ""
    echo "============================================================"
    echo "  FIAP X - Minikube Setup"
    echo "============================================================"
    echo ""

    check_prerequisites
    start_minikube
    build_images
    deploy_k8s
    print_urls
}

main "$@"
