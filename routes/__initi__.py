# Importe os módulos necessários
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail

# Importe os blueprints específicos que você criou
from .discente import discente_route
from .home import home_route
from .multidimensional import multidimensional_route
from .pdiprppg import pdi_route
from .producao import producao_route
from .indicador import indicador_route
from routes import login_route
from .models import Users  # Certifique-se de que o arquivo models.py está no mesmo diretório
from flask_mail import Mail
from .utils import init_extensions


mail = Mail()

# Crie uma função para inicializar o aplicativo Flask e configurá-lo
def create_app():
    app = Flask(__name__)  

    init_extensions(app)
    # Configuração do banco de dados
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/DB_PRPPG'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicialize o objeto Bcrypt
    bcrypt = Bcrypt(app)

    # Carrega as configurações do arquivo config.py
    app.config.from_pyfile('config.py')

    # Inicialize os módulos do Flask necessários
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    db.init_app(app)

    # Inicialize o CSRFProtect
    csrf = CSRFProtect(app)

    # Inicialize o Flask-Mail
    mail.init_app(app)

    # Passe o objeto Bcrypt para os módulos que precisam dele
   # Users.init_bcrypt(bcrypt)

    # Registre os blueprints
    app.register_blueprint(home_route)
    app.register_blueprint(discente_route)
    app.register_blueprint(multidimensional_route)
    app.register_blueprint(pdi_route)
    app.register_blueprint(producao_route)
    app.register_blueprint(indicador_route)
    app.register_blueprint(login_route)   
  
    return app




