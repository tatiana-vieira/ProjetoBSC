from flask import render_template
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan,Valorindicador
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
import matplotlib.pyplot as plt
import base64
from io import BytesIO

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
##################################################################################################################################33333
@relatorioindicador_route.route('/graficoindicadores')
def exibir_graficoindicador():
    planejamentope = PlanejamentoEstrategico.query.all()
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.objetivo_pdi_id.in_([pdi.id for pdi in planejamentope])).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()

    indicadores_por_meta = {}
    valores_indicadores = {}
    for meta in metaspe:
        indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
        indicadores_por_meta[meta.id] = indicadores

        for indicador in indicadores:
            # Filtrar os valores para incluir apenas os a partir de 2018
            valores = [valor.valor for valor in Valorindicador.query.filter_by(indicadorpe_id=indicador.id) if valor.ano >= 2018]
            anos = [valor.ano for valor in Valorindicador.query.filter_by(indicadorpe_id=indicador.id) if valor.ano >= 2018]
            semestres = [valor.semestre for valor in Valorindicador.query.filter_by(indicadorpe_id=indicador.id) if valor.ano >= 2018]
            
            valores_indicadores[indicador.id] = {'valores': valores, 'anos': anos, 'semestres': semestres}

    graphs = []
    for indicador_id, data in valores_indicadores.items():
        anos = [ano for ano in data['anos'] if ano >= 2018]
        semestres = [data['semestres'][i] for i in range(len(data['anos'])) if data['anos'][i] >= 2018]
        valores = [data['valores'][i] for i in range(len(data['anos'])) if data['anos'][i] >= 2018]
        
        plt.figure(figsize=(8, 6))
        for i in range(len(anos)):
            if semestres[i] == 1:
                plt.scatter(anos[i], 1, c='blue', s=100)  # tamanho fixo para os marcadores
            else:
                plt.scatter(anos[i], 2, c='red', s=100)  # tamanho fixo para os marcadores
        plt.title('Valores do Indicador {}'.format(indicador_id))
        plt.xlabel('Ano')
        plt.ylabel('Semestre')
        plt.grid(True)
        
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        
        graph_base64 = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        graphs.append(graph_base64)

    return render_template('graficosindicadores.html', graphs=graphs, indicadores_por_meta=indicadores_por_meta)