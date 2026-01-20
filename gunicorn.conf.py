import os

workers = int(os.environ.get("WORKERS", 2))  # 1-2 workers per CPU core
bind = "0.0.0.0:80"
timeout = 240
keepalive = 50  # Should be less than timeout
app_module = "src.app:create_app()"
