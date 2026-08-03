import multiprocessing
import os

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))


worker_class = os.getenv("GUNICORN_WORKER_CLASS", "sync")
threads = int(os.getenv("GUNICORN_THREADS", "4"))

timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
