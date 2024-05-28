from flask import render_template, flash, request, redirect, session, url_for
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, AcaoPE, Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from flask_login import login_required
import matplotlib.pyplot as plt
import io
import base64

graficoacaope_route = Blueprint('graficoacaope', __name__)

@graficoacaope_route.route('/grafacaope', methods=['GET'])
@login_required
def exibir_graficoacaope():
    if session.get('role') == 'Coordenador':
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)

        if not programa:
            flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
            return redirect(url_for('login.get_coordenador'))

        planejamentos = programa.planejamentos
        planejamento_selecionado_id = request.args.get('planejamento_selecionado')
        meta_selecionada_id = request.args.get('meta_selecionada')
        planejamento_selecionado = None
        metaspe = []
        acoespe = []
        graficos = []

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('graficoacaope.exibir_graficoacaope'))

            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()

            if meta_selecionada_id:
                acoespe = AcaoPE.query.filter_by(meta_pe_id=meta_selecionada_id).all()
                if acoespe:
                    nomes_acoes = [acao.nome for acao in acoespe]
                    porcentagens_execucao = [acao.porcentagem_execucao for acao in acoespe]

                    fig, ax = plt.subplots()
                    ax.barh(nomes_acoes, porcentagens_execucao, color='skyblue')
                    ax.set_xlabel('Porcentagem de Execução')
                    ax.set_title('Execução das Ações')

                    img = io.BytesIO()
                    plt.savefig(img, format='png', bbox_inches='tight')
                    img.seek(0)
                    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
                    plt.close(fig)

                    graficos.append({
                        'meta': MetaPE.query.get(meta_selecionada_id).nome,
                        'grafico': plot_url,
                        'acoes': [{
                            'nome': acao.nome,
                            'data_inicio': acao.data_inicio,
                            'data_termino': acao.data_termino,
                            'porcentagem_execucao': acao.porcentagem_execucao
                        } for acao in acoespe]
                    })

        return render_template('graficoacaope.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, metas=metaspe, meta_selecionada_id=meta_selecionada_id, graficos=graficos)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))