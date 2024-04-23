from flask import Flask, render_template, url_for, redirect, flash, request
from flask_mail import Message, send_mail
from routes.models import User, Token
import routes.utils as utils  # Importe as funções send_email e generate_token
from .routes import db
from flask_mail import Mail, Message

app = Flask(__name__)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']

        # Verifique se o email existe no banco de dados
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email não encontrado.', 'danger')
            return render_template('reset_password.html')

        # Gere um token de redefinição de senha
        token = utils.generate_token()

        # Crie um link de redefinição de senha
        reset_password_link = url_for('reset_password_token', token=token, _external=True)

        # Envie um email para o usuário com o link de redefinição de senha
        send_email(user.email, 'Redefinição de senha',
                   render_template('reset_password_email.html',
                                   reset_password_link=reset_password_link))

        flash('Um email de recuperação de senha foi enviado para o seu endereço de email registrado.', 'info')
        return redirect(url_for('login.login_page'))

    return render_template('reset_password.html')

@app.route('/reset-password-token/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    if request.method == 'POST':
        new_password = request.form['new_password']

        # Verifique se o token é válido e não expirou
        token_object = Token.query.filter_by(token=token).first()
        if not token_object or token_object.expired:
            flash('Token inválido ou expirado.', 'danger')
            return redirect(url_for('login.login_page'))

        # Permita que o usuário redefina sua senha
        user = User.query.filter_by(email=token_object.email).first()
        user.password = new_password
        db.session.commit()

        # Atualize o token no banco de dados como inválido
        token_object.expired = True
        db.session.commit()

        flash('Senha redefinida com sucesso.', 'success')
        return redirect(url_for('login.login_page'))

    return render_template('reset_password_token.html')