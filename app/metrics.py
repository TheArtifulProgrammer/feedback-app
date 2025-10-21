"""Prometheus metrics instrumentation"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Response
from functools import wraps
import time

# Metric definitions
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

feedback_operations_total = Counter(
    'feedback_operations_total',
    'Total feedback operations',
    ['operation']
)

feedback_count = Gauge(
    'feedback_count',
    'Current feedback count'
)

errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type']
)


def track_request_metrics(endpoint_name):
    """Decorator to track HTTP metrics"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            method = endpoint_name.split('_')[0].upper()

            try:
                response = f(*args, **kwargs)
                duration = time.time() - start_time
                status = response[1] if isinstance(response, tuple) else 200

                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint_name,
                    status=status
                ).inc()

                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint_name
                ).observe(duration)

                return response

            except Exception as e:
                errors_total.labels(error_type=type(e).__name__).inc()
                raise

        return decorated_function
    return decorator


def record_feedback_operation(operation: str):
    """Record feedback operation"""
    feedback_operations_total.labels(operation=operation).inc()


def update_feedback_count(count: int):
    """Update feedback count"""
    feedback_count.set(count)


def record_error(error_type: str):
    """Record error"""
    errors_total.labels(error_type=error_type).inc()


def metrics_endpoint():
    """Expose Prometheus metrics"""
    from app.database import DatabaseManager
    db = DatabaseManager()
    try:
        count = db.count_feedback()
        feedback_count.set(count)
    except Exception:
        pass
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
