from flask import render_template
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, AcaoPE
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint

relatorioacao_route = Blueprint('relatorioacao', __name__)

@relatorioacao_route.route('/relatacao')
def exibir_relatorioacao():
    planejamentope = PlanejamentoEstrategico.query.all()
    
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.objetivo_pdi_id.in_([pdi.id for pdi in planejamentope])).all()
    
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    
    acaope = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    
    return render_template('relatacao.html', objetivos=objetivospe, metas=metaspe, acaope=acaope)