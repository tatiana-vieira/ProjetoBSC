from flask import render_template,request,flash,redirect,url_for,session
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan,Valorindicador,Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from flask_login import login_required
import random

relatorioindicador_route = Blueprint('relatorioindicador', __name__)

@relatorioindicador_route.route('/relatindicadores')
@login_required
def exibir_relatorioindicador():
    if session.get('role') == 'Coordenador':
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)

        if not programa:
            flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
            return redirect(url_for('login.get_coordenador'))

        planejamentos = programa.planejamentos
        planejamento_selecionado_id = request.args.get('planejamento_selecionado')
        planejamento_selecionado = None
        objetivospe = []
        metaspe = []
        indicadores_por_meta = {}
        valores_indicadores = {}

        if planejamento_selecionado_id:
            print(f"Planejamento selecionado ID: {planejamento_selecionado_id}")
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))

            print(f"Planejamento selecionado: {planejamento_selecionado.nome}")
            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()

            for meta in metaspe:
                indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
                indicadores_por_meta[meta.id] = indicadores

            for indicador in IndicadorPlan.query.all():
                valores_indicadores[indicador.id] = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()

        return render_template('relatindicadores.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, objetivos=objetivospe, metas=metaspe, indicadores_por_meta=indicadores_por_meta, valores_indicadores=valores_indicadores)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))
##################################################################################################################################33333
@relatorioindicador_route.route('/graficoindicadores', methods=['GET'])
@login_required
def exibir_graficoindicador():
    if session.get('role') == 'Coordenador':
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)

        if not programa:
            flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
            return redirect(url_for('login.get_coordenador'))

        planejamentos = programa.planejamentos
        planejamento_selecionado_id = request.args.get('planejamento_selecionado')
        planejamento_selecionado = None
        objetivospe = []
        metaspe = []

        if planejamento_selecionado_id:
            print(f"Planejamento selecionado ID: {planejamento_selecionado_id}")
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatoriometas.exibir_graficometas'))

            print(f"Planejamento selecionado: {planejamento_selecionado.nome}")
            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()

        indicadores_por_meta = {}
        valores_indicadores = {}
        for meta in metaspe:
            indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
            indicadores_por_meta[meta.id] = indicadores

            for indicador in indicadores:
                # Filtrar os valores para incluir apenas os a partir de 2018
                valores = [valor for valor in Valorindicador.query.filter_by(indicadorpe_id=indicador.id).all() if valor.ano >= 2018]
                valores_indicadores[indicador.id] = valores

        graphs = []
        for indicador_id, valores in valores_indicadores.items():
            plt.figure(figsize=(10, 6))
            anos = [valor.ano for valor in valores]
            valores_y = [valor.valor for valor in valores]
            plt.plot(anos, valores_y, marker='o', linestyle='-', color='b')
            plt.title(f'Indicador {indicador_id}')
            plt.xlabel('Ano')
            plt.ylabel('Valor')
            plt.grid(True)
            
            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            
            graph_base64 = base64.b64encode(img.getvalue()).decode()
            plt.close()
            
            graphs.append((graph_base64, f'Indicador {indicador_id}'))

        return render_template('graficosindicadores.html', graphs=graphs, planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))