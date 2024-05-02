import secrets
from flask_mail import Mail

def generate_token(length):
    return secrets.token_hex(length)

mail = Mail()

def init_extensions(app):
    # Initialize other extensions (SQLAlchemy, Migrate, etc.)
    # ...
    mail.init_app(app)