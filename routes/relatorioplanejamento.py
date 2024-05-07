from flask import render_template
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPE
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint

relplanejamento_route = Blueprint('relplanejamento', __name__)

@relplanejamento_route.route('/relplano')
def exibir_pdi():
    planejamentope = PlanejamentoEstrategico.query.all()
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.objetivo_pdi_id.in_([pdi.id for pdi in planejamentope])).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    indicadores = IndicadorPE.query.filter(IndicadorPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    
    return render_template('relplanejamento.html', objetivos=objetivospe, metas=metaspe, indicadores=indicadores)

