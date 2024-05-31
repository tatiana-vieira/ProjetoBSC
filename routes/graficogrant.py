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
        plot_url = None

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('graficogrant.exibir_gantt'))

            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
            acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

            if acoespe:
                # Gerar gráfico de Gantt
                try:
                    df = pd.DataFrame([(acao.nome, acao.data_inicio, acao.data_termino) for acao in acoespe], columns=['Ação', 'Início', 'Término'])
                    fig, ax = plt.subplots(figsize=(10, 6))

                    for i, (acao, inicio, termino) in enumerate(zip(df['Ação'], df['Início'], df['Término'])):
                        ax.barh(acao, (termino - inicio).days, left=inicio, height=0.4)

                    ax.set_xlabel('Data')
                    ax.set_ylabel('Ação')
                    ax.set_title('Gráfico de Gantt das Ações')

                    img = io.BytesIO()
                    plt.savefig(img, format='png', bbox_inches='tight')
                    img.seek(0)
                    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
                    plt.close(fig)
                except Exception as e:
                    flash(f'Erro ao gerar o gráfico: {str(e)}', 'danger')

        return render_template('gantt.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, acoes=acoespe, plot_url=plot_url)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))