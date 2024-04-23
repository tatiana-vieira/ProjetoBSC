from flask import Blueprint, render_template, request
from flask_sqlalchemy import SQLAlchemy
from .models import PDI
import json

db = SQLAlchemy()
indicador_route = Blueprint('indicador', __name__)

class Indicador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    id_meta = db.Column(db.Integer, db.ForeignKey('pdi_unifei.id'), nullable=False)

    # Relação com a tabela PDI
    meta = db.relationship('PDI', backref=db.backref('indicadores', lazy=True))

@indicador_route.route('/cadastro_indicador', methods=['GET', 'POST'])
def cadastro_indicador():
    if request.method == 'POST':
        nome = request.form['nome']
        if 'id_meta' in request.form:
            id_meta = request.form['id_meta']
        else:
            return "Erro: 'id_meta' não está presente no formulário"
        indicador = Indicador(nome=nome, id_meta=id_meta)
        db.session.add(indicador)
        db.session.commit()
        return 'Indicador cadastrado com sucesso!'    
    
    else:
        metas = PDI.query.all()  # Busca todas as metas
        return render_template('cadastro_indicador.html', metas=metas)
    
    