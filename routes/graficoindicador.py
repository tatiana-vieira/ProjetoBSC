from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan, Valorindicador, db
from flask_login import login_required
import matplotlib.pyplot as plt
import io
import base64

graficoindicador_route = Blueprint('graficoindicador', __name__)

@graficoindicador_route.route('/relgraficosindicadores', methods=['GET'])
@login_required
def exibir_graficoindicador():
    if session.get('role') == 'Coordenador':
        coordenador_programa_id = session.get('programa_id')
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=coordenador_programa_id).all()
        planejamento_selecionado_id = request.args.get('planejamento_selecionado')
        planejamento_selecionado = None
        graphs = []

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('graficoindicador.exibir_graficoindicador'))

            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
            indicadores = []

            for meta in metas:
                indicadores_meta = IndicadorPlan.query.filter_by(meta_pe_id=meta.id).all()
                for indicador in indicadores_meta:
                    valores_indicadores = Valorindicador.query.filter_by(indicadorpe_id=indicador.id).all()
                    indicadores.append({
                        'nome': indicador.nome,
                        'valor_meta': float(indicador.valor_meta) if indicador.valor_meta else 0.0,
                        'valores_indicadores': [{'ano': valor.ano, 'semestre': valor.semestre, 'valor': float(valor.valor)} for valor in valores_indicadores]
                    })

            # Gerar gráficos consolidado e de desempenho para todos os indicadores
            graph_base64, graphs_base64 = gerar_grafico_consolidado(indicadores)
            graphs.append((graph_base64, "Indicadores Consolidado"))
            graphs.append((graphs_base64, "Desempenho Total dos Indicadores em Relação às Metas"))

        return render_template('graficoindicador.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, graphs=graphs)

    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

def gerar_grafico_consolidado(indicadores):
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for indicador in indicadores:
        periodos = [f"{valor['ano']}/{valor['semestre']}" for valor in indicador['valores_indicadores']]
        valores = [valor['valor'] for valor in indicador['valores_indicadores']]
        valor_meta = indicador['valor_meta']

        # Gráfico de Linha do Indicador com Meta
        ax.plot(periodos, valores, marker='o', linestyle='-', label=indicador['nome'], linewidth=2)
        if valor_meta > 0:
            ax.axhline(y=valor_meta, color='red', linestyle='--', linewidth=1, label=f"Meta {indicador['nome']} ({valor_meta}%)")
        for i, v in enumerate(valores):
            cumprimento = (v / valor_meta) * 100 if valor_meta > 0 else 0
            cor = 'green' if cumprimento >= 100 else 'orange' if cumprimento >= 80 else 'red'
            ax.text(i, v + 0.5, f"{v:.1f}% ({cumprimento:.1f}%)", ha='center', va='bottom', fontsize=8, color=cor)

    ax.set_xlabel('Período')
    ax.set_ylabel('Valor do Indicador')
    ax.set_title('Comparação de Indicadores com Metas')
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1), title="Indicadores", fontsize=10)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Salva o gráfico
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    # Gráfico de Barras para Desempenho Total em Relação à Meta
    fig, ax = plt.subplots(figsize=(12, 6))
    nomes_indicadores = [ind['nome'] for ind in indicadores]
    valores_atuais = [sum([val['valor'] for val in ind['valores_indicadores']]) for ind in indicadores]
    metas = [ind['valor_meta'] for ind in indicadores]
    
    ax.bar(nomes_indicadores, valores_atuais, color='skyblue', label='Valor Atual')
    ax.bar(nomes_indicadores, metas, color='lightcoral', alpha=0.6, label='Meta')
    ax.set_xlabel('Indicadores')
    ax.set_ylabel('Valores')
    ax.set_title('Desempenho Total dos Indicadores em Relação às Metas')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Salva o gráfico
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graphs_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return graph_base64, graphs_base64  # Retorna ambos gráficos como base64
