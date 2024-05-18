from flask import render_template, request, redirect, url_for, jsonify,flash,session
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, db,Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from flask_login import  login_required
import matplotlib.pyplot as plt
import matplotlib.cm as cm


relatoriometas_route = Blueprint('relatoriometas', __name__)

def get_planejamento_metas():
    # Implement the logic to obtain strategic planning goals here
    metas = MetaPE.query.all()  # Assuming MetaPE is the model for goals
    return metas

@relatoriometas_route.route('/relatmetas', methods=['GET'])
@login_required
def exibir_relatoriometas():
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
                return redirect(url_for('relatoriometas.exibir_relatoriometas'))

            print(f"Planejamento selecionado: {planejamento_selecionado.nome}")
            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
            print(f"Objetivos: {len(objetivospe)}, Metas: {len(metaspe)}")

        return render_template('relatoriometas.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, objetivos=objetivospe, metas=metaspe)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))
##############################################################################################################################
@relatoriometas_route.route('/salvar_alteracao_meta/<int:meta_id>', methods=['POST'])
def salvar_alteracao_meta(meta_id):
    if request.method == 'POST':
        meta = MetaPE.query.get_or_404(meta_id)
        nome = request.form.get('nome')
        porcentagem_execucao = request.form.get('porcentagem_execucao')
        if nome:
            meta.nome = nome
        if porcentagem_execucao:
            meta.porcentagem_execucao = porcentagem_execucao
        db.session.commit()
        return redirect(url_for('relatoriometas.sucesso')), 302
    else:
        return jsonify({'error': 'Método não permitido'}), 405

@relatoriometas_route.route('/sucesso')
def sucesso():
    return render_template('sucesso.html')
###############################################################################
##############################################################################################################################33
@relatoriometas_route.route('/graficometas', methods=['GET'])
@login_required
def exibir_graficometas():
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

        # Gerar o gráfico
        plt.figure(figsize=(14, 7))  # Aumentar o tamanho da figura
        nomes_metas = [meta.nome for meta in metaspe]
        porcentagens_execucao = [meta.porcentagem_execucao for meta in metaspe]

        # Usar um colormap para diferentes cores
        colors = cm.get_cmap('tab20', len(metaspe))

        bars = plt.bar(range(len(metaspe)), porcentagens_execucao, color=[colors(i / len(metaspe)) for i in range(len(metaspe))])
        plt.title('Porcentagem de Execução das Metas')
        plt.xlabel('Meta')
        plt.ylabel('Porcentagem de Execução (%)')
        plt.xticks(range(len(metaspe)), [f'Meta {i+1}' for i in range(len(metaspe))], rotation=45, ha='right', fontsize=9)  # Rotacionar, alinhar e diminuir o tamanho da fonte dos nomes das metas

        # Adicionar a legenda
        plt.legend(bars, nomes_metas, bbox_to_anchor=(1.03, 1), loc='upper left', fontsize=8)

        # Adicionar margem para os rótulos
        plt.subplots_adjust(right=0.6, bottom=0.3)

        # Salvar o gráfico em memória
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        # Codificar o gráfico em base64 para incorporação no HTML
        graph_base64 = base64.b64encode(img.getvalue()).decode()
        plt.close()

        return render_template('graficometas.html', objetivos=objetivospe, metas=metaspe, graph_base64=graph_base64, planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))