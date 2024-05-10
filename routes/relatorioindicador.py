from flask import render_template
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan,Valorindicador
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint

relatorioindicador_route = Blueprint('relatorioindicador', __name__)

@relatorioindicador_route.route('/relatindicadores')
def exibir_relatorioindicador():
    planejamentope = PlanejamentoEstrategico.query.all()
    
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.objetivo_pdi_id.in_([pdi.id for pdi in planejamentope])).all()
    
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    
    indicadores_por_meta = {}
    for meta in metaspe:
        indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
        indicadores_por_meta[meta.id] = indicadores

    valores_indicadores = {}
    for indicador in IndicadorPlan.query.all():
        valores_indicadores[indicador.id] = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()

    return render_template('relatindicadores.html', objetivos=objetivospe, metas=metaspe, indicadores_por_meta=indicadores_por_meta, valores_indicadores=valores_indicadores)