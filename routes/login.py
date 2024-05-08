from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from .models import Users, Programa  # Certifique-se de importar seus modelos corretamente
from routes.db import db
from flask_bcrypt import Bcrypt
from flask_login import login_user, login_required, LoginManager, current_user

login_route = Blueprint('login', __name__)
bcrypt = Bcrypt()  # Inicialize o Bcrypt

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
######################################################################################################################3
@login_route.route('/get_coordenador')
def get_coordenador():
    # Acessando o contexto do aplicativo Flask
    permanent_session_lifetime_ms = current_app.config.get('PERMANENT_SESSION_LIFETIME_MS')
    
    # Seu código para recuperar os dados do coordenador
    return render_template('indexcord.html', permanent_session_lifetime_ms=permanent_session_lifetime_ms)
######################################################################################################################
@login_route.route('/get_proreitor')
def get_proreitor():
    # Acessando o contexto do aplicativo Flask
    permanent_session_lifetime_ms = current_app.config.get('PERMANENT_SESSION_LIFETIME_MS')
    
    # Seu código para recuperar os dados do pro-reitor
    return render_template('indexpro.html', permanent_session_lifetime_ms=permanent_session_lifetime_ms)
######################################################################################################################
@login_route.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)  # Registrar o usuário
            session['email'] = email  
            session['user_id'] = user.id  

            if user.role == 'Coordenador':
                session['role'] = 'Coordenador'  # Definindo a função do usuário na sessão
            
            flash('Login bem-sucedido!', 'success')
            if user.role == 'Coordenador':
                return redirect(url_for('login.get_coordenador'))
            elif user.role == 'Pro-reitor':
                return redirect(url_for('login.get_proreitor'))
            else:
                return redirect(url_for('login.dashboard'))
        else:
            flash('Credenciais inválidas. Por favor, tente novamente.', 'danger')

    return render_template('login.html')
######################################################################################################################
@login_route.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login.login_page'))  
######################################################################################################################
@login_route.route('/cancelar', methods=['GET', 'POST'])
def cancelar():
    if request.method == 'POST':
        return redirect(request.referrer)
    
    # Se a requisição não for POST, então redirecionar com base no papel do usuário na sessão
    role = session.get('role')
    if role == 'Coordenador':
        return redirect(url_for('login.get_coordenador'))
    elif role == 'Pro-reitor':
        return redirect(url_for('login.get_proreitor'))
    else:
        return redirect(url_for('index'))  # Redireciona para a página inicial
######################################################################################################################
@login_route.route('/get_role')
@login_required
def get_role():
    role = current_user.role  
    if role == 'Coordenador' or role == 'Pro-reitor':
        return render_template(f'index{role.lower()}.html')
    else:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login.login_page'))
######################################################################################################################