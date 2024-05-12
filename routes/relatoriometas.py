from flask import render_template, request, redirect, url_for, jsonify
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, db
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint

relatoriometas_route = Blueprint('relatoriometas', __name__)

def get_planejamento_metas():
    # Implement the logic to obtain strategic planning goals here
    metas = MetaPE.query.all()  # Assuming MetaPE is the model for goals
    return metas

@relatoriometas_route.route('/relatmetas')
def exibir_relatoriometas():
    planejamentope = PlanejamentoEstrategico.query.all()
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.objetivo_pdi_id.in_([pdi.id for pdi in planejamentope])).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    planejamento_metas = get_planejamento_metas()
    return render_template('relatoriometas.html', objetivos=objetivospe, metas=metaspe, planejamento_metas=planejamento_metas)

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