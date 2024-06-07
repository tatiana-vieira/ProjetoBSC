import os

bind = "0.0.0.0:8000"
workers = 2
reload = os.getenv("FLASK_DEBUG", "false").lower() == "true"