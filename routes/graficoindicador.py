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

            for meta in metas:
                indicadores = IndicadorPlan.query.filter_by(meta_pe_id=meta.id).all()
                for indicador in indicadores:
                    valores_indicadores = Valorindicador.query.filter_by(indicadorpe_id=indicador.id).all()
                    if valores_indicadores:
                        # Verificar se indicador.valor_meta é None
                        if indicador.valor_meta is not None:
                            try:
                                valor_meta = float(indicador.valor_meta)
                            except ValueError:
                                valor_meta = 0.0  # Definir um valor padrão se a conversão falhar
                        else:
                            valor_meta = 0.0  # Valor padrão se o valor_meta estiver ausente

                        graph_base64 = gerar_grafico_comparativo(indicador.nome, valor_meta, valores_indicadores)
                        graphs.append((graph_base64, indicador.nome))

        return render_template('graficoindicador.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, graphs=graphs)

    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))






def gerar_grafico_comparativo(nome_indicador, valor_meta, valores_indicadores):
    fig, ax = plt.subplots()

    periodos = [f"{valor.ano}/{valor.semestre}" for valor in valores_indicadores]
    valores = [float(valor.valor) for valor in valores_indicadores]

    ax.bar(periodos, valores, label='Valor Atual', color='b')
    ax.axhline(y=valor_meta, color='r', linestyle='--', label=f'Meta ({valor_meta}%)')

    ax.set_xlabel('Período')
    ax.set_ylabel('Valor')
    ax.set_title(f'Comparação do Indicador {nome_indicador}', fontsize=10)
    ax.legend()

    for i, v in enumerate(valores):
        ax.text(i, float(v) + 0.1, f"{float(v)}%", ha='center', va='bottom', fontsize=8)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return graph_base64