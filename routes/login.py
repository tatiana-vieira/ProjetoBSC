from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from .models import Users, Programa,Token
from routes.db import db
from flask_bcrypt import Bcrypt
from flask_login import login_user, login_required, LoginManager, current_user

login_route = Blueprint('login', __name__)
bcrypt = Bcrypt()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).get(int(user_id))

@login_route.route('/get_coordenador')
@login_required
def get_coordenador():
    permanent_session_lifetime_ms = current_app.config.get('PERMANENT_SESSION_LIFETIME_MS')
    programa_id = current_user.programa_id
    return render_template('indexcord.html', permanent_session_lifetime_ms=permanent_session_lifetime_ms, programa_id=programa_id)

@login_route.route('/get_proreitor')
@login_required
def get_proreitor():
    permanent_session_lifetime_ms = current_app.config.get('PERMANENT_SESSION_LIFETIME_MS')
    return render_template('indexpro.html', permanent_session_lifetime_ms=permanent_session_lifetime_ms)

@login_route.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            session['email'] = email  
            session['user_id'] = user.id  
            session['role'] = user.role if user.role in ['Coordenador', 'Pro-reitor'] else 'Outro'
            session['programa_id'] = user.programa_id

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

@login_route.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login.login_page'))

@login_route.route('/cancelar', methods=['GET', 'POST'])
def cancelar():
    if request.method == 'POST':
        return redirect(request.referrer)
    role = session.get('role')
    if role == 'Coordenador':
        return redirect(url_for('login.get_coordenador'))
    elif role == 'Pro-reitor':
        return redirect(url_for('login.get_proreitor'))
    else:
        return redirect(url_for('index'))

@login_route.route('/get_role')
@login_required
def get_role():
    role = current_user.role  
    if role == 'Coordenador' or role == 'Pro-reitor':
        return render_template(f'index{role.lower()}.html')
    else:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login.login_page'))


##############################################################################################33


# Rota para verificar o e-mail
# Rota para verificar o e-mail
@login_route.route('/verificar_email', methods=['GET', 'POST'])
def verificar_email():
    if request.method == 'POST':
        email = request.form['email']
        user = Users.query.filter_by(email=email).first()

        if not user:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('login.verificar_email'))

        # Redireciona para a rota apropriada com o e-mail como parâmetro
        if user.security_question:
            return redirect(url_for('login.redefinir_senha', email=email))
        else:
            return redirect(url_for('login.redefinir_senha_codigo', email=email))

    return render_template('verificar_email.html')


# Rota para redefinir senha com pergunta de segurança
# Rota para redefinir senha com pergunta de segurança
@login_route.route('/redefinir_senha', methods=['GET', 'POST'])
def redefinir_senha():
    email = request.args.get('email')
    user = Users.query.filter_by(email=email).first()

    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('login.verificar_email'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')

        # Atualiza a senha e opcionalmente a pergunta e a resposta de segurança
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password_hash = hashed_password

        if security_question and security_answer:
            user.security_question = security_question
            user.security_answer = security_answer

        try:
            db.session.commit()
            flash('Senha redefinida com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('login.login_page'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao redefinir a senha. Por favor, tente novamente.', 'danger')

    return render_template('redefinir_senha.html', email=email)




@login_route.route('/trocar_senha', methods=['GET', 'POST'])
@login_required
def trocar_senha():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        # Verifica a senha atual
        if bcrypt.check_password_hash(current_user.password_hash, current_password):
            # Atualiza para a nova senha
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            current_user.password_hash = hashed_password
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('login.get_role'))
        else:
            flash('Senha atual incorreta.', 'danger')

    return render_template('trocar_senha.html')



@login_route.route('/register_security', methods=['GET', 'POST'])
def register_security():
    if request.method == 'POST':
        email = request.form.get('email')
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')  # Texto simples

        user = Users.query.filter_by(email=email).first()
        if user:
            user.security_question = security_question
            user.security_answer = security_answer  # Salvar como texto simples
            db.session.commit()
            flash('Pergunta de segurança cadastrada com sucesso!', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')

    return render_template('register_security.html')



############ usuarios sem pergunta #########################
# Rota para redefinir senha para usuários sem pergunta de segurança
@login_route.route('/redefinir_senha_codigo', methods=['GET', 'POST'])
def redefinir_senha_codigo():
    email = request.args.get('email')
    user = Users.query.filter_by(email=email).first()

    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('login.verificar_email'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')

        # Atualiza a senha e opcionalmente a pergunta e a resposta de segurança
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password_hash = hashed_password

        if security_question and security_answer:
            user.security_question = security_question
            user.security_answer = security_answer

        try:
            db.session.commit()
            flash('Senha redefinida com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('login.login_page'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao redefinir a senha. Por favor, tente novamente.', 'danger')

    return render_template('redefinir_senha_codigo.html', email=email)

