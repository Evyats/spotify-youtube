import time

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total",
    "HTTP requests",
    ["service", "method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency",
    ["service", "method", "path"],
)


def register_observability(app: FastAPI, service_name: str) -> None:
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        path = request.url.path
        REQUEST_COUNT.labels(service_name, request.method, path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(service_name, request.method, path).observe(elapsed)
        return response

    @app.get("/metrics")
    def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
