from flask import Flask, render_template
from .models import PDI, Objetivo, Meta, Indicador
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from flask import Flask, request,jsonify

planejamento_route = Flask(__name__)
planejamento_route = Blueprint('planejamento', __name__)

@planejamento_route.route('/planejamento')
def exibir_pdi():
    objetivos = Objetivo.query.all()
    return render_template('planejamento.html', objetivos=objetivos)

@planejamento_route.route('/metas_por_objetivo')
def obter_metas_por_objetivo():
    objetivo_id = request.args.get('objetivo_id')
    metas = Meta.query.filter_by(objetivo_id=objetivo_id).all()
    metas_dict = {str(meta.id): meta.nome for meta in metas}  # Convertendo o ID para str
    return jsonify(metas_dict)

if __name__ == '__main__':
    planejamento_route.run(debug=True)