import os
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1

if os.getenv("FLASK_DEBUG", "false").lower() == "true":
    reload = True
else:
    reload = False

loglevel = 'debug'
accesslog = '-'
errorlog = '-'