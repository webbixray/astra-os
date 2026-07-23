from prometheus_client import Counter, Gauge, Histogram

http_requests_total = Counter(
    "astra_http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "astra_http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_flight = Gauge(
    "astra_http_requests_in_flight",
    "Current HTTP requests being handled",
    labelnames=["method"],
)

users_signed_up = Counter(
    "astra_users_signed_up_total",
    "Total user signups",
)

campaigns_created = Counter(
    "astra_campaigns_created_total",
    "Total campaigns created",
)

workflows_completed = Counter(
    "astra_workflows_completed_total",
    "Total workflows completed",
)

workflows_failed = Counter(
    "astra_workflows_failed_total",
    "Total workflows failed",
)
