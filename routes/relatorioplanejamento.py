from flask import render_template,request,redirect,flash,session,url_for
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan,Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint,session


relatorioplanejamento_route = Blueprint('relatorioplanejamento', __name__)


from flask import session, redirect, url_for, flash

@relatorioplanejamento_route.route('/relplano')
def exibir_relplanejamento():
    # Verificar se o usuário está logado como coordenador
    if 'role' in session and session['role'] == 'Coordenador':
        # Obter o ID do coordenador logado
        coordenador_id = session['user_id']

        # Filtrar os planejamentos estratégicos associados ao coordenador logado
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=coordenador_id).all()

        # Se nenhum planejamento estratégico foi encontrado, retornar uma mensagem adequada
        if not planejamentos:
            flash('Não há planejamentos estratégicos associados ao coordenador logado.', 'warning')
            return redirect(url_for('login.get_coordenador'))  # Redirecionar para a página de cadastro de PDI ou outra página adequada
       
        # Inicializar listas vazias para armazenar objetivos, metas e indicadores
        todos_objetivos = []
        todas_metas = []
        todos_indicadores = []

        # Para cada planejamento estratégico, obter os objetivos, metas e indicadores associados
        for planejamento in planejamentos:
            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
            
            # Para cada objetivo, obter as metas e indicadores associados
            for objetivo in objetivos:
                metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
                indicadores = []
                
                # Para cada meta, obter os indicadores associados
                for meta in metas:
                    indicadores.extend(IndicadorPlan.query.filter_by(meta_pe_id=meta.id).all())
                
                # Adicionar os objetivos, metas e indicadores às listas
                todos_objetivos.extend(objetivos)
                todas_metas.extend(metas)
                todos_indicadores.extend(indicadores)

        return render_template('relplanejamento.html', planejamentos=planejamentos, objetivos=todos_objetivos, metas=todas_metas, indicadores=todos_indicadores)
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login_page'))
    

   