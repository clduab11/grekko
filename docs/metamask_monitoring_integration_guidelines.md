# Metamask Integration Service: Monitoring Integration Guidelines

This document outlines the requirements for the Metamask Integration Service to fully integrate with the existing monitoring infrastructure (Prometheus, Grafana, Loki, Jaeger).

## 1. Metrics Exposure for Prometheus

The Metamask Integration Service application should expose an HTTP endpoint (e.g., `/metrics`) serving metrics in Prometheus format.

- **Requirement**: Implement a Prometheus client library (e.g., `prometheus_client` for Python) within the service.
- **Key Metrics to Expose**:
    - **Security:**
        - `metamask_auth_failures_total`: Counter for authentication failures.
        - `metamask_suspicious_transactions_detected_total`: Counter for detected suspicious transactions.
        - `metamask_rpc_connection_errors_total`: Counter for RPC connection errors.
        - `metamask_browser_automation_security_events_total`: Counter for security events from browser automation (labeled by event type).
    - **Performance:**
        - `metamask_api_request_duration_seconds`: Histogram/Summary for API endpoint latency (labeled by `endpoint`, `method`, `status_code`).
        - `metamask_api_requests_total`: Counter for total API requests (labeled by `endpoint`, `method`, `status_code`).
        - `metamask_api_requests_failed_total`: Counter for failed API requests (labeled by `endpoint`, `method`, `status_code`).
        - `metamask_browser_automation_duration_seconds`: Histogram/Summary for browser automation task duration (labeled by `task_type`).
        - `metamask_db_query_duration_seconds`: Histogram/Summary for database query duration (labeled by `query_type`, `table`).
        - `metamask_kafka_message_processing_duration_seconds`: Histogram/Summary for Kafka message processing time (labeled by `topic`, `consumer_group`).
        - `metamask_kafka_messages_processed_total`: Counter for Kafka messages processed (labeled by `topic`, `consumer_group`, `status`).
    - **Business Metrics:**
        - `metamask_wallet_connection_attempts_total`: Counter for wallet connection attempts.
        - `metamask_wallet_connection_successful_total`: Counter for successful wallet connections.
        - `metamask_wallet_connection_failed_total`: Counter for failed wallet connections (labeled by `reason`).
        - `metamask_transaction_attempts_total`: Counter for transaction attempts.
        - `metamask_transaction_completed_total`: Counter for completed transactions.
        - `metamask_transaction_failed_total`: Counter for failed transactions (labeled by `reason`).
        - `metamask_network_switches_total`: Counter for network switch events (labeled by `from_network`, `to_network`, `status`).
        - `metamask_user_sessions_active`: Gauge for currently active user sessions.
        - `metamask_user_session_duration_seconds`: Histogram/Summary for user session durations.
    - **Operational:**
        - Standard process metrics (CPU, memory) if not covered by cAdvisor/kubelet.
        - `metamask_dependency_health`: Gauge for health of dependencies (e.g., Redis, PostgreSQL, Kafka) (labeled by `dependency_name`, `status`).

- **Kubernetes Annotations**: Ensure the Metamask Integration Service pods have the following annotations for Prometheus scraping:
  ```yaml
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/path: "/metrics"  # Or your custom metrics path
    prometheus.io/port: "8080"      # The port your service exposes metrics on
  ```
- **Labels**: Ensure pods are labeled appropriately, e.g., `app: metamask-integration`, `app.kubernetes.io/part-of: trading-system`.

## 2. Structured Logging for Loki

The service should output logs in a structured format (preferably JSON) to `stdout`/`stderr`. This allows for easier parsing, indexing, and querying in Loki.

- **Requirement**: Configure the application's logger to output JSON.
- **Key Log Fields**:
    - `timestamp`: ISO 8601 timestamp.
    - `level`: Log level (e.g., INFO, WARN, ERROR, DEBUG).
    - `message`: The log message.
    - `service_name`: "metamask-integration-service".
    - `correlation_id`: A unique ID to trace requests across services/components.
    - `user_id`: If applicable and anonymized/pseudonymized.
    - `transaction_id`: If applicable.
    - `error_code`: If an error occurred.
    - `stack_trace`: For errors.
    - Any other relevant contextual information (e.g., `api_endpoint`, `method`, `duration_ms`).

- **Example Log Line (JSON)**:
  ```json
  {"timestamp": "2025-05-29T12:30:00.123Z", "level": "ERROR", "service_name": "metamask-integration-service", "message": "Failed to process transaction", "transaction_id": "xyz789", "error_code": "TXN_FAIL_005", "correlation_id": "abc123def456", "stack_trace": "..."}
  ```
- **Log Forwarding**: A log forwarder (e.g., Promtail, Fluent Bit) should be configured in the Kubernetes cluster to collect these logs and send them to the Loki instance at `http://loki.monitoring.svc.cluster.local:3100`.

## 3. Distributed Tracing with Jaeger

The service should be instrumented to generate and propagate distributed traces.

- **Requirement**: Integrate an OpenTelemetry (recommended) or OpenTracing-compatible client library.
- **Configuration**:
    - Configure the tracer to export spans to the Jaeger agent or collector.
        - Jaeger Agent (UDP): `jaeger-agent.monitoring.svc.cluster.local:6831`
        - Jaeger Collector (HTTP/gRPC): `jaeger-collector.monitoring.svc.cluster.local:14268` (HTTP) or `:14250` (gRPC). OTLP endpoint is also available on the collector.
    - Ensure context propagation is enabled for inter-service communication (e.g., via HTTP headers like W3C Trace Context or B3).
- **Key Spans**:
    - Incoming API requests.
    - Outgoing calls to external services (e.g., blockchain RPC nodes, other internal services).
    - Database queries.
    - Kafka message production and consumption.
    - Significant internal operations or business logic flows.
- **Tags/Attributes**: Spans should include relevant tags/attributes like `http.method`, `http.url`, `db.statement`, `messaging.kafka.topic`, `error` (boolean), and any custom business-relevant tags.

By adhering to these guidelines, the Metamask Integration Service will be effectively monitored, providing deep insights into its security posture, performance characteristics, and operational health.