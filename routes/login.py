from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from .models import Users,Programas
from routes.db import db
from werkzeug.security import generate_password_hash
from flask_bcrypt import Bcrypt  # Importe o Bcrypt


login_route = Blueprint('login', __name__)
bcrypt = Bcrypt()  # Inicialize o Bcrypt

###################################################3
@login_route.route('/login/register', methods=['POST'])
def register_page():
    if request.method == 'POST':
        # Extrair dados do formulário
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        programa_id = request.form['programa_id']

        # Criar um novo objeto de usuário
        new_user = Users(username=username, email=email, role=role, programa_id=programa_id)

        # Gerar o hash da senha usando Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Definir password_hash
        new_user.password_hash = hashed_password

        if role != 'Coordenador':
            new_user.programa_id = 0  # Definir programa_id como 0 para não coordenadores

        try:
            # Adicionar o novo usuário ao banco de dados
            db.session.add(new_user)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect('/login')  # Redirecionar para a página de login após o cadastro
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Erro ao cadastrar usuário. Por favor, tente novamente.', 'danger')

    # Buscar programas do banco de dados
    programas = Programas.query.all()

    # Renderizar o modelo HTML com programas para o formulário de cadastro
    return render_template('register.html', programas=programas)
###########################################################################################################################################
@login_route.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        # Extrair dados do formulário
        email = request.form['email']
        password = request.form['password']

        # Buscar o usuário pelo e-mail fornecido
        user = Users.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            # Autenticar o usuário
            session['email'] = email

            if user.role == 'Coordenador':
                # Redirecionar para a página do coordenador
                flash('Login bem-sucedido como coordenador!', 'success')
                return redirect(url_for('get_coordenador'))
            elif user.role == 'Pro-reitor':
                # Redirecionar para a página do pró-reitor
                flash('Login bem-sucedido como pró-reitor!', 'success')
                return redirect(url_for('get_proreitor'))
            else:
                # Redirecionar para a página inicial padrão
                flash('Login bem-sucedido!', 'success')
                return redirect(url_for('get_index'))
        else:
            flash('Credenciais inválidas. Por favor, tente novamente.', 'danger')

    return render_template('login.html')

   