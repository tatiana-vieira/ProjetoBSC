from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session,flash
from routes.db import db  # Certifique-se de importar a instância correta
from routes.models import PDI, Objetivo, Meta, Indicador, Users

indicador_route = Blueprint('indicador', __name__)

@indicador_route.route('/cadastro_indicador', methods=['GET', 'POST'])
def cadastro_indicador():
    if request.method == 'POST':
        return processar_formulario_indicador()
    else:
        pdis = PDI.query.all()
        return render_template('cadastro_indicador.html', pdis=pdis)

@indicador_route.route('/sucesso_cadastro')
def sucesso_cadastro():
    return 'Indicador cadastrado com sucesso!'

@indicador_route.route('/get_objetivos/<int:pdi_id>', methods=['GET'])
def get_objetivos(pdi_id):
    objetivos = Objetivo.query.filter_by(pdi_id=pdi_id).all()
    objetivos_data = [{'id': obj.id, 'nome': obj.nome} for obj in objetivos]
    return jsonify({'objetivos': objetivos_data})

@indicador_route.route('/get_metas/<int:objetivo_id>', methods=['GET'])
def get_metas(objetivo_id):
    metas = Meta.query.filter_by(objetivo_id=objetivo_id).all()
    metas_data = [{'id': meta.id, 'nome': meta.nome} for meta in metas]
    return jsonify({'metas': metas_data})

def processar_formulario_indicador():
    if 'email' not in session:
        return 'Acesso não autorizado'

    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    nome = request.form.get('nome')
    meta_id = request.form.get('meta_id')

    if not nome or not meta_id:
        flash('Dados incompletos', 'error')
        return redirect(url_for('indicador.cadastro_indicador'))

    novo_indicador = Indicador(nome=nome, meta_pdi_id=meta_id)
    db.session.add(novo_indicador)
    db.session.commit()

    flash('Indicador cadastrado com sucesso!', 'success')
    return redirect(url_for('indicador.cadastro_indicador'))