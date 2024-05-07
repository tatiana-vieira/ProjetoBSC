from flask import Flask, render_template,jsonify
from .models import PDI, Objetivo, Meta, Indicador
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint

#pdi_route = Flask(__name__)
pdi_route = Blueprint('pdi', __name__)

@pdi_route.route('/relpdi')
def exibir_pdi():
    pdi_data = PDI.query.all()
    objetivos = Objetivo.query.filter(Objetivo.pdi_id.in_([pdi.id for pdi in pdi_data])).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()
    
    return render_template('pdi.html', objetivos=objetivos, metas=metas, indicadores=indicadores)
