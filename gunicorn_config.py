import multiprocessing
import os

bind = "0.0.0.0:8000"
workers = 2
if os.getenv("FLASK_DEBUG", "false").lower() == "true":
    reload = True
else:
    reload = False

loglevel = 'debug'
accesslog = '-'
errorlog = '-'