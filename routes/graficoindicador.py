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

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('graficoindicador.exibir_graficoindicador'))

            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()

            # Processar e renderizar gráficos
            return processar_e_renderizar_graficos(metas, planejamentos, planejamento_selecionado)

        return render_template('graficoindicador.html', planejamentos=planejamentos)
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

def gerar_grafico_consolidado(indicadores):
    fig, ax = plt.subplots(figsize=(14, 8))
    
    nomes_indicadores = [ind['nome'] for ind in indicadores]
    valores_atuais = [sum([val['valor'] for val in ind['valores_indicadores']]) for ind in indicadores]
    metas = [ind['valor_meta'] for ind in indicadores]
    
    bar_width = 0.4
    x = range(len(nomes_indicadores))
    
    ax.bar([p - bar_width / 2 for p in x], valores_atuais, width=bar_width, color='skyblue', label='Valor Atual')
    ax.bar([p + bar_width / 2 for p in x], metas, width=bar_width, color='lightcoral', alpha=0.7, label='Meta')

    ax.set_xticks(x)
    ax.set_xticklabels(nomes_indicadores, rotation=30, ha='right', fontsize=10)
    ax.set_xlabel('Indicadores', fontsize=12)
    ax.set_ylabel('Valores', fontsize=12)
    ax.set_title('Desempenho Total dos Indicadores em Relação às Metas', fontsize=14, weight='bold')

    for i, (v_atual, meta) in enumerate(zip(valores_atuais, metas)):
        ax.text(i - bar_width / 2, v_atual + 2, f"{v_atual:.1f}", ha='center', fontsize=9)
        ax.text(i + bar_width / 2, meta + 2, f"{meta:.1f}", ha='center', fontsize=9)

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=10)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return graph_base64

def gerar_grafico_linhas(indicadores):
    """
    Gera um gráfico de linhas para mostrar a evolução dos indicadores ao longo do tempo.
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    for indicador in indicadores:
        periodos = [f"{valor['ano']}/{valor['semestre']}" for valor in indicador['valores_indicadores']]
        valores = [valor['valor'] for valor in indicador['valores_indicadores']]
        valor_meta = indicador['valor_meta']

        if len(valores) > 1:  # Mostre apenas indicadores com dados em mais de um período
            ax.plot(periodos, valores, marker='o', linestyle='-', label=indicador['nome'], linewidth=2)
            if valor_meta > 0:
                ax.axhline(y=valor_meta, color='red', linestyle='--', linewidth=1, label=f"Meta {indicador['nome']}")

    ax.set_xlabel('Período', fontsize=12)
    ax.set_ylabel('Valor do Indicador', fontsize=12)
    ax.set_title('Evolução dos Indicadores ao Longo do Tempo', fontsize=14, weight='bold')
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=10)
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return graph_base64



def processar_e_renderizar_graficos(metas, planejamentos, planejamento_selecionado):
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

    graph_consolidado = gerar_grafico_consolidado(indicadores)
    graph_linhas = gerar_grafico_linhas(indicadores)

    graphs = [
        (graph_consolidado, "Desempenho Total dos Indicadores"),
        (graph_linhas, "Evolução ao Longo do Tempo"),
    ]

    return render_template(
        'graficoindicador.html',
        planejamentos=planejamentos,
        planejamento_selecionado=planejamento_selecionado,
        graphs=graphs
    )


def gerar_grafico_radar(indicadores):
    """
    Gera um gráfico de radar para comparar indicadores em relação às metas.
    """
    import numpy as np
    from math import pi

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    labels = [ind['nome'] for ind in indicadores]
    valores_atuais = [sum([val['valor'] for val in ind['valores_indicadores']]) for ind in indicadores]
    metas = [ind['valor_meta'] for ind in indicadores]

    # Ângulos para o gráfico de radar
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    valores_atuais += valores_atuais[:1]  # Fechar o gráfico
    metas += metas[:1]
    angles += angles[:1]

    # Plotar
    ax.fill(angles, valores_atuais, color='skyblue', alpha=0.4, label="Valores Atuais")
    ax.plot(angles, valores_atuais, color='blue', linewidth=2)
    ax.fill(angles, metas, color='lightcoral', alpha=0.4, label="Metas")
    ax.plot(angles, metas, color='red', linestyle='--', linewidth=2)

    ax.set_yticks([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10, color="black")
    ax.set_title("Comparação dos Indicadores em Relação às Metas", fontsize=14, weight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1), fontsize=10)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return graph_base64
