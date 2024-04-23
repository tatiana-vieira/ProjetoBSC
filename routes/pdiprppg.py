from flask import Flask, render_template
from .models import PDI, Objetivo, Meta, Indicador
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint

pdi_route = Flask(__name__)
pdi_route = Blueprint('pdi', __name__)

@pdi_route.route('/pdi')
def exibir_pdi():
    pdi_data = PDI.query.all()
    
    # Filtrando os objetivos relacionados ao PDI
    objetivos = Objetivo.query.filter(Objetivo.pdi_id.in_([pdi.id for pdi in pdi_data])).all()

    # Filtrando as metas relacionadas aos objetivos
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()

    # Filtrando os indicadores relacionados às metas
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()
    
    return render_template('pdi.html', objetivos=objetivos, metas=metas, indicadores=indicadores)

if __name__ == '__main__':
    pdi_route.run(debug=True)