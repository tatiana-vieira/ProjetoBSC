from flask import Blueprint, render_template, request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from .models import PDI,Objetivo,Meta
import json

db = SQLAlchemy()
indicador_route = Blueprint('indicador', __name__)

class Indicador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    id_meta = db.Column(db.Integer, db.ForeignKey('pdi.id'), nullable=False)

    # Relação com a tabela PDI
    meta = db.relationship('PDI', backref=db.backref('indicadores', lazy=True))

@indicador_route.route('/cadastro_indicador', methods=['GET', 'POST'])
def cadastro_indicador():
    if request.method == 'POST':
        nome = request.form['nome']
        id_meta = request.form['id_meta']
        indicador = Indicador(nome=nome, id_meta=id_meta)
        db.session.add(indicador)
        db.session.commit()
        return redirect(url_for('sucesso_cadastro'))    
    
    else:
        pdis = PDI.query.all()  # Busca todos os PDIs
        objetivos = Objetivo.query.all()  # Busca todos os objetivos
        metas = Meta.query.all()  # Busca todas as metas
        return render_template('cadastro_indicador.html', pdis=pdis, objetivos=objetivos, metas=metas)

@indicador_route.route('/sucesso_cadastro')
def sucesso_cadastro():
    return 'Indicador cadastrado com sucesso!'
