import multiprocessing
import os

bind = "0.0.0.0:8000"
workers = 2  # Você pode ajustar isso conforme necessário
reload = os.getenv("FLASK_DEBUG", "false").lower() == "true"

loglevel = 'debug'
accesslog = '-'
errorlog = '-'