from flask import Flask
from flask_login import LoginManager
from .config import login_manager

app = Flask(__name__)

# Inicialize o gerenciador de login
login_manager.init_app(app)

login_manager = LoginManager()
login_manager.session_protection = 'strong'  # Pode ser 'basic', 'strong', 'None'
login_manager.login_view = 'auth.login'  # Endpoint da rota de login


SECRET_KEY = 'my_secret_key_123'

# config.py
MAIL_SERVER = 'smtp.your_mail_server.com'
MAIL_PORT = 587  # Adjust port if needed
MAIL_USE_TLS = True  # Enable encryption
MAIL_USERNAME = 'your_email@example.com'
MAIL_PASSWORD = 'your_email_password'