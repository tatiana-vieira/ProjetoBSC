from flask import render_template
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, AcaoPE,IndicadorPE
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint

relatorioindicador_route = Blueprint('relatorioindicador', __name__)

@relatorioindicador_route.route('/relatindicador')
def exibir_relatorioacao():
    planejamentope = PlanejamentoEstrategico.query.all()
    
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.objetivo_pdi_id.in_([pdi.id for pdi in planejamentope])).all()
    
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    
    indicadorpe = IndicadorPE.query.filter(IndicadorPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    
    return render_template('relatindicadores.html', objetivos=objetivospe, metas=metaspe, indicadorpe=indicadorpe)