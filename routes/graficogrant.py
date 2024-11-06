from flask import render_template, flash, request, redirect, session, url_for
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, AcaoPE, Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from flask_login import login_required
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64

graficogrant_route = Blueprint('graficogrant', __name__)

@graficogrant_route.route('/gantt', methods=['GET'])
@login_required
def exibir_gantt():
    if session.get('role') == 'Coordenador':
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)

        if not programa:
            flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
            return redirect(url_for('login.get_coordenador'))

        planejamentos = programa.planejamentos
        planejamento_selecionado_id = request.args.get('planejamento_selecionado')
        planejamento_selecionado = None
        acoespe = []
        plot_urls = {}

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('graficogrant.exibir_gantt'))

            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
            acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

            if acoespe:
                try:
                    # Gráfico de Gantt
                    df = pd.DataFrame([(acao.nome, acao.data_inicio, acao.data_termino) for acao in acoespe], columns=['Ação', 'Início', 'Término'])
                    fig, ax = plt.subplots(figsize=(10, 6))
                    for i, (acao, inicio, termino) in enumerate(zip(df['Ação'], df['Início'], df['Término'])):
                        ax.barh(acao, (termino - inicio).days, left=inicio, height=0.4)
                    ax.set_xlabel('Data')
                    ax.set_ylabel('Ação')
                    ax.set_title('Período de execução das Ações')
                    img = io.BytesIO()
                    plt.savefig(img, format='png', bbox_inches='tight')
                    img.seek(0)
                    plot_urls['gantt'] = base64.b64encode(img.getvalue()).decode('utf8')
                    plt.close(fig)

                # Gráfico de Progresso por Ação
                    df['Porcentagem'] = [acao.porcentagem_execucao for acao in acoespe]
                    fig, ax = plt.subplots(figsize=(10, 6))

                    # Criar gráfico de barras com tamanho de fonte ajustado
                    ax.bar(df['Ação'], df['Porcentagem'], color='skyblue')
                    ax.set_xlabel('Ação', fontsize=12)
                    ax.set_ylabel('Progresso (%)', fontsize=12)
                    ax.set_title('Progresso de Execução por Ação', fontsize=14)

                    # Rotacionar as labels do eixo x para uma melhor visualização
                    ax.tick_params(axis='x', labelrotation=45, labelsize=10)  # Ajuste de rotação e tamanho da fonte

                    # Salvar o gráfico
                    img = io.BytesIO()
                    plt.savefig(img, format='png', bbox_inches='tight')
                    img.seek(0)
                    plot_urls['progress'] = base64.b64encode(img.getvalue()).decode('utf8')
                    plt.close(fig)

                    # Gráfico de Distribuição do Status das Ações
                    status_counts = pd.Series([acao.status for acao in acoespe]).value_counts()
                    fig, ax = plt.subplots(figsize=(6, 6))
                    ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=90)
                    ax.set_title('Distribuição do Status das Ações')
                    img = io.BytesIO()
                    plt.savefig(img, format='png', bbox_inches='tight')
                    img.seek(0)
                    plot_urls['status'] = base64.b64encode(img.getvalue()).decode('utf8')
                    plt.close(fig)

                    # Gráfico de Duração Média por Ação
                    df['Duração'] = (df['Término'] - df['Início']).dt.days
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.bar(df['Ação'], df['Duração'], color='lightgreen')
                    ax.set_xlabel('Ação')
                    ax.set_ylabel('Duração em Dias')
                    ax.set_title('Duração Média de Execução por Ação')
                    img = io.BytesIO()
                    plt.savefig(img, format='png', bbox_inches='tight')
                    img.seek(0)
                    plot_urls['duration'] = base64.b64encode(img.getvalue()).decode('utf8')
                    plt.close(fig)

                except Exception as e:
                    flash(f'Erro ao gerar os gráficos: {str(e)}', 'danger')

        return render_template('gantt.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, acoes=acoespe, plot_urls=plot_urls)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))
