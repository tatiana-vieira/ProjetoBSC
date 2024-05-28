from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import db, IndicadorPlan, VariavelPE, MetaPE,Formula,SinalPE
from flask_login import login_required, LoginManager, current_user
from functools import wraps

calculoindicador_route = Blueprint('calculoindicador', __name__)
login_manager = LoginManager(calculoindicador_route)

def coordenador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'Coordenador':
            flash('Acesso negado. Apenas coordenadores podem acessar esta página.', 'danger')
            return redirect(url_for('login.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@calculoindicador_route.route('/calcularindicador', methods=['GET', 'POST'])
@login_required
def indicadores():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        meta_id = request.form.get('meta')
        variaveis = request.form.getlist('variavel-nome[]')
        sinais = request.form.getlist('sinal[]')

        indicador = IndicadorPlan(nome=nome, descricao=descricao, meta_pe_id=meta_id)
        db.session.add(indicador)
        db.session.commit()

        for variavel_nome in variaveis:
            variavel = VariavelPE(nome=variavel_nome, indicador_pe_id=indicador.id)
            db.session.add(variavel)

        for sinal_valor in sinais:
            sinal = SinalPE(valor=sinal_valor, indicador_pe_id=indicador.id)
            db.session.add(sinal)

        db.session.commit()

        flash('Indicador cadastrado com sucesso!', 'success')
        return redirect(url_for('calculoindicador.indicadores'))

    metas = MetaPE.query.all()
    return render_template('add_data.html', metas=metas)

@calculoindicador_route.route('/adicionar_variavel/<int:indicador_id>', methods=['GET', 'POST'])
def adicionar_variavel(indicador_id):
    if request.method == 'POST':
        nome = request.form.get('nome')
        variavel = VariavelPE(nome=nome, indicador_pe_id=indicador_id)
        db.session.add(variavel)
        db.session.commit()
        return redirect(url_for('calculoindicador.adicionar_variavel', indicador_id=indicador_id))

    indicador = IndicadorPlan.query.get(indicador_id)
    variaveis = VariavelPE.query.filter_by(indicador_pe_id=indicador_id).all()
    return render_template('adicionar_variavel.html', indicador=indicador, variaveis=variaveis)

@calculoindicador_route.route('/adicionar_formula/<int:indicador_id>', methods=['GET', 'POST'])
def adicionar_formula(indicador_id):
    if request.method == 'POST':
        expressao = request.form.get('expressao')
        formula = Formula(indicador_id=indicador_id, expressao=expressao)
        db.session.add(formula)
        db.session.commit()
        return redirect(url_for('calculoindicador.indicadores'))

    indicador = IndicadorPlan.query.get(indicador_id)
    variaveis = VariavelPE.query.filter_by(indicador_pe_id=indicador_id).all()
    return render_template('adicionar_formula.html', indicador=indicador, variaveis=variaveis)