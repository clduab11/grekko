"""Metrics Module for Metamask Integration Service

This module handles the collection and exposure of metrics for monitoring
the Metamask Integration Service using Prometheus.
"""

import time
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from .config import METRICS_ENABLED, METRICS_PORT, METRICS_ENDPOINT
import logging

logger = logging.getLogger(__name__)

# Metrics definitions

# Security Metrics
metamask_auth_failures_total = Counter(
    'metamask_auth_failures_total',
    'Counter for authentication failures.'
)
metamask_suspicious_transactions_detected_total = Counter(
    'metamask_suspicious_transactions_detected_total',
    'Counter for detected suspicious transactions.'
)
metamask_rpc_connection_errors_total = Counter(
    'metamask_rpc_connection_errors_total',
    'Counter for RPC connection errors.'
)
metamask_browser_automation_security_events_total = Counter(
    'metamask_browser_automation_security_events_total',
    'Counter for security events from browser automation.',
    ['event_type']
)

# Performance Metrics
metamask_api_request_duration_seconds = Histogram(
    'metamask_api_request_duration_seconds',
    'Histogram for API endpoint latency.',
    ['endpoint', 'method', 'status_code']
)
metamask_api_requests_total = Counter( # Renamed from api_requests_total for consistency
    'metamask_api_requests_total',
    'Counter for total API requests.',
    ['endpoint', 'method', 'status_code']
)
metamask_api_requests_failed_total = Counter(
    'metamask_api_requests_failed_total',
    'Counter for failed API requests.',
    ['endpoint', 'method', 'status_code']
)
metamask_browser_automation_duration_seconds = Histogram(
    'metamask_browser_automation_duration_seconds',
    'Histogram for browser automation task duration.',
    ['task_type']
)
metamask_db_query_duration_seconds = Histogram(
    'metamask_db_query_duration_seconds',
    'Histogram for database query duration.',
    ['query_type', 'table']
)
metamask_kafka_message_processing_duration_seconds = Histogram(
    'metamask_kafka_message_processing_duration_seconds',
    'Histogram for Kafka message processing time.',
    ['topic', 'consumer_group']
)
metamask_kafka_messages_processed_total = Counter(
    'metamask_kafka_messages_processed_total',
    'Counter for Kafka messages processed.',
    ['topic', 'consumer_group', 'status']
)

# Business Metrics
metamask_wallet_connection_attempts_total = Counter( # Renamed from wallet_connections_total
    'metamask_wallet_connection_attempts_total',
    'Counter for wallet connection attempts.'
)
metamask_wallet_connection_successful_total = Counter(
    'metamask_wallet_connection_successful_total',
    'Counter for successful wallet connections.'
)
metamask_wallet_connection_failed_total = Counter(
    'metamask_wallet_connection_failed_total',
    'Counter for failed wallet connections.',
    ['reason']
)
metamask_transaction_attempts_total = Counter( # Renamed from transaction_requests_total
    'metamask_transaction_attempts_total',
    'Counter for transaction attempts.',
    ['status'] # Existing label, kept for now, may need review based on usage
)
metamask_transaction_completed_total = Counter(
    'metamask_transaction_completed_total',
    'Counter for completed transactions.'
)
metamask_transaction_failed_total = Counter(
    'metamask_transaction_failed_total',
    'Counter for failed transactions.',
    ['reason']
)
metamask_network_switches_total = Counter( # Renamed from network_switches_total
    'metamask_network_switches_total',
    'Counter for network switch events.',
    ['from_network', 'to_network', 'status']
)
metamask_user_sessions_active = Gauge(
    'metamask_user_sessions_active',
    'Gauge for currently active user sessions.'
)
metamask_user_session_duration_seconds = Histogram(
    'metamask_user_session_duration_seconds',
    'Histogram for user session durations.'
)

# Operational Metrics
metamask_dependency_health = Gauge(
    'metamask_dependency_health',
    'Gauge for health of dependencies.',
    ['dependency_name', 'status']
)

# Existing metrics (to be reviewed if they are redundant or need renaming)
# transaction_latency_seconds = Histogram('transaction_latency_seconds', 'Transaction processing latency in seconds', ['status']) # Covered by specific transaction metrics
# browser_operations_total = Counter('browser_operations_total', 'Total number of browser operations', ['operation', 'status']) # Covered by specific browser automation metrics
# validation_checks_total = Counter('validation_checks_total', 'Total number of validation checks', ['type', 'result']) # Potentially useful, keep for now


# --- Potentially redundant or to be refactored metrics ---
# These were present in the original file but might be covered by the new, more specific metrics.
# Review and remove/refactor if necessary.
transaction_latency_seconds = Histogram('metamask_transaction_latency_seconds', 'Transaction processing latency in seconds', ['status']) # Renamed for consistency
browser_operations_total = Counter('metamask_browser_operations_total', 'Total number of browser operations', ['operation', 'status']) # Renamed for consistency
validation_checks_total = Counter('metamask_validation_checks_total', 'Total number of validation checks', ['type', 'result']) # Renamed for consistency


def start_metrics_server():
    """
    Start the HTTP server to expose Prometheus metrics if enabled in configuration.
    """
    if METRICS_ENABLED:
        try:
            start_http_server(METRICS_PORT)
            logger.info(f"Metrics server started on port {METRICS_PORT}, endpoint {METRICS_ENDPOINT}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    else:
        logger.info("Metrics collection is disabled in configuration")

def record_wallet_connection():
    """
    Record a wallet connection attempt.
    """
    if METRICS_ENABLED:
        metamask_wallet_connection_attempts_total.inc() # Updated to new metric name

def record_transaction_request(status: str):
    """
    Record a transaction request with its status.
    
    Args:
        status (str): The status of the transaction request (e.g., 'success', 'failure').
    """
    if METRICS_ENABLED:
        metamask_transaction_attempts_total.labels(status=status).inc() # Updated to new metric name

def record_transaction_latency(status: str, start_time: float):
    """
    Record the latency of a transaction processing.
    
    Args:
        status (str): The status of the transaction (e.g., 'success', 'failure').
        start_time (float): The start time of the transaction processing.
    """
    if METRICS_ENABLED:
        latency = time.time() - start_time
        transaction_latency_seconds.labels(status=status).observe(latency) # Kept existing, review if covered by new ones

# Updated to match new label requirements
def record_network_switch(from_network: str, to_network: str, status: str):
    """
    Record a network switch event.
    
    Args:
        from_network (str): The network switched from.
        to_network (str): The network switched to.
        status (str): The status of the switch.
    """
    if METRICS_ENABLED:
        metamask_network_switches_total.labels(from_network=from_network, to_network=to_network, status=status).inc()

def record_api_request(endpoint: str, method: str, status_code: int, duration: float):
    """
    Record an API request with its details.
    
    Args:
        endpoint (str): The API endpoint accessed.
        method (str): The HTTP method used (e.g., 'GET', 'POST').
        status_code (int): The HTTP status code returned.
        duration (float): The duration of the API request in seconds.
    """
    if METRICS_ENABLED:
        metamask_api_requests_total.labels(endpoint=endpoint, method=method, status_code=status_code).inc()
        metamask_api_request_duration_seconds.labels(endpoint=endpoint, method=method, status_code=status_code).observe(duration)
        if status_code >= 400: # Assuming 4xx and 5xx are failures
            metamask_api_requests_failed_total.labels(endpoint=endpoint, method=method, status_code=status_code).inc()

def record_browser_operation(operation: str, status: str, duration: Optional[float] = None):
    """
    Record a browser operation with its status.
    
    Args:
        operation (str): The type of browser operation (e.g., 'launch', 'navigate').
        status (str): The status of the operation (e.g., 'success', 'failure').
        duration (float, optional): The duration of the browser operation in seconds.
    """
    if METRICS_ENABLED:
        browser_operations_total.labels(operation=operation, status=status).inc() # Kept existing, review
        if duration is not None:
            metamask_browser_automation_duration_seconds.labels(task_type=operation).observe(duration)

def record_validation_check(check_type: str, result: str):
    """
    Record a validation check with its result.
    
    Args:
        check_type (str): The type of validation check (e.g., 'transaction', 'address').
        result (str): The result of the check (e.g., 'valid', 'invalid').
    """
    if METRICS_ENABLED:
        validation_checks_total.labels(type=check_type, result=result).inc() # Kept existing, review

# --- New recording functions for added metrics ---

def record_auth_failure():
    if METRICS_ENABLED:
        metamask_auth_failures_total.inc()

def record_suspicious_transaction():
    if METRICS_ENABLED:
        metamask_suspicious_transactions_detected_total.inc()

def record_rpc_connection_error():
    if METRICS_ENABLED:
        metamask_rpc_connection_errors_total.inc()

def record_browser_automation_security_event(event_type: str):
    if METRICS_ENABLED:
        metamask_browser_automation_security_events_total.labels(event_type=event_type).inc()

def record_db_query_duration(query_type: str, table: str, duration: float):
    if METRICS_ENABLED:
        metamask_db_query_duration_seconds.labels(query_type=query_type, table=table).observe(duration)

def record_kafka_message_processing(topic: str, consumer_group: str, status: str, duration: float):
    if METRICS_ENABLED:
        metamask_kafka_messages_processed_total.labels(topic=topic, consumer_group=consumer_group, status=status).inc()
        metamask_kafka_message_processing_duration_seconds.labels(topic=topic, consumer_group=consumer_group).observe(duration)

def record_wallet_connection_success():
    if METRICS_ENABLED:
        metamask_wallet_connection_successful_total.inc()

def record_wallet_connection_failure(reason: str):
    if METRICS_ENABLED:
        metamask_wallet_connection_failed_total.labels(reason=reason).inc()

def record_transaction_completed():
    if METRICS_ENABLED:
        metamask_transaction_completed_total.inc()

def record_transaction_failed(reason: str):
    if METRICS_ENABLED:
        metamask_transaction_failed_total.labels(reason=reason).inc()

def set_active_user_sessions(count: int):
    if METRICS_ENABLED:
        metamask_user_sessions_active.set(count)

def record_user_session_duration(duration: float):
    if METRICS_ENABLED:
        metamask_user_session_duration_seconds.observe(duration)

def set_dependency_health(dependency_name: str, status: str): # status could be 'up', 'down', 'degraded'
    if METRICS_ENABLED:
        # Convert status to a numerical value for Gauge if needed, or use info metrics
        # For simplicity, let's assume status is directly usable or mapped elsewhere
        # Example: 1 for up, 0 for down
        health_value = 1 if status.lower() == 'up' else 0 # Basic example
        metamask_dependency_health.labels(dependency_name=dependency_name, status=status).set(health_value)