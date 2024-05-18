from flask import render_template, request, redirect, url_for, jsonify,flash,session
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, db,Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from flask_login import  login_required


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
@relatoriometas_route.route('/graficometas')
def exibir_graficometas():
    planejamentope = PlanejamentoEstrategico.query.all()
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.objetivo_pdi_id.in_([pdi.id for pdi in planejamentope])).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    planejamento_metas = get_planejamento_metas()

    # Gerar o gráfico
    plt.figure(figsize=(10, 6))
    for meta in metaspe:
        plt.bar(meta.nome, meta.porcentagem_execucao)
    plt.title('Porcentagem de Execução das Metas')
    plt.xlabel('Meta')
    plt.ylabel('Porcentagem de Execução (%)')
    plt.xticks(rotation=90)  # Rotacionar os nomes das metas para melhor visualização

    # Salvar o gráfico em memória
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Codificar o gráfico em base64 para incorporação no HTML
    graph_base64 = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template('graficometas.html', objetivos=objetivospe, metas=metaspe, planejamento_metas=planejamento_metas, graph_base64=graph_base64)