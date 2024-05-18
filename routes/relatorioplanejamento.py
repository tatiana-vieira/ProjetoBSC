from flask import render_template,redirect,flash,session,url_for,request,jsonify
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan,Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint,session
from flask_login import  login_required


relatorioplanejamento_route = Blueprint('relatorioplanejamento', __name__)

@relatorioplanejamento_route.route('/relplano', methods=['GET'])
@login_required
def exibir_detalhes_planejamento():
    if session.get('role') == 'Coordenador':
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)
        
        if not programa:
            flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
            return redirect(url_for('login.get_coordenador'))

        planejamentos = programa.planejamentos

        planejamento_selecionado_id = request.args.get('planejamento_selecionado')
        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                return jsonify({'error': 'Planejamento não encontrado'}), 404

            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
            indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas])).all()
            
            dados = []
            for objetivo in objetivos:
                metas_dados = []
                for meta in [m for m in metas if m.objetivo_pe_id == objetivo.id]:
                    indicadores_dados = [{'nome': indicador.nome} for indicador in indicadores if indicador.meta_pe_id == meta.id]
                    metas_dados.append({'nome': meta.nome, 'indicadores': indicadores_dados})
                dados.append({'nome': objetivo.nome, 'metas': metas_dados})

            return jsonify({'objetivos': dados})

        return render_template('relplanejamento.html', programa=programa, planejamentos=planejamentos)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))