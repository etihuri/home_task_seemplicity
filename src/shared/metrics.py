from prometheus_client import Counter, Gauge, Histogram

# Request metrics
http_requests_total = Counter(
    "tasker_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "tasker_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Task metrics
tasks_submitted_total = Counter(
    "tasker_tasks_submitted_total",
    "Total tasks submitted",
    ["task_name"],
)

tasks_completed_total = Counter(
    "tasker_tasks_completed_total",
    "Total tasks completed",
    ["task_name", "status"],
)

task_duration_seconds = Histogram(
    "tasker_task_duration_seconds",
    "Task execution time in seconds",
    ["task_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# System metrics
tasks_pending = Gauge(
    "tasker_tasks_pending",
    "Number of pending tasks",
)
