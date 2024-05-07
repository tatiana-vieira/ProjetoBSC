from flask import Flask
from flask_login import LoginManager
from .config import SECRET_KEY, MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD

app = Flask(__name__)

# Configurações do Flask
app.config['SECRET_KEY'] = SECRET_KEY

# Configurações de e-mail
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD

# Inicialize o gerenciador de login
login_manager = LoginManager()
login_manager.init_app(app)

# Configurações do LoginManager
login_manager.session_protection = 'strong'  # Pode ser 'basic', 'strong', 'None'
login_manager.login_view = 'auth.login'  # Endpoint da rota de login