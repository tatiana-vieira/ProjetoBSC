from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import PlanejamentoEstrategico, MetaPE, IndicadorPE, AcaoPE, PDI, Programa, Users,Objetivo,ObjetivoPE
from flask_login import current_user  # Adicione esta linha
from flask_login import LoginManager
from . import db  # Importe a instância db do main.py
from flask import Flask
from routes.db import db


planejamento_route = Blueprint('planejamento', __name__)
login_manager = LoginManager(planejamento_route)

@planejamento_route.route('/cadastro_planejamentope', methods=['GET', 'POST'])
def cadastro_planejamentope():
    if request.method == 'POST':
        # Processar o formulário de cadastro de planejamento
        nome = request.form['nome']
        pdi_id = request.form['pdi_id']

        # Verifique se o usuário está logado e é um coordenador
        if 'programa_id' not in session:
            flash('Nenhum programa do usuário encontrado. Faça login novamente.', 'danger')
            return redirect(url_for('login.login_page'))

        programa_id = session['programa_id']  # Recupere o programa_id da sessão

        # Lógica para criar um novo planejamento estratégico
        novo_planejamento = PlanejamentoEstrategico(
            nome=nome,
            pdi_id=pdi_id,
            id_programa=programa_id
        )
        db.session.add(novo_planejamento)
        db.session.commit()

        flash('Planejamento cadastrado com sucesso!', 'success')
        return redirect(url_for('get_coordenador'))
    else:
        # Se o método for GET, renderize o formulário de cadastro
        pdis = PDI.query.all()
        programas = Programa.query.all()

        programa_do_usuario = None
        if current_user and current_user.is_authenticated and hasattr(current_user, 'programa_id') and current_user.programa_id:
            programa_do_usuario = Programa.query.get(current_user.programa_id)
            print("Programa do usuário encontrado:", programa_do_usuario)
        else:
            programa_do_usuario = None
            print("Nenhum programa do usuário encontrado.")

        return render_template('planejamento.html', pdis=pdis, programas=programas, programa_do_usuario=programa_do_usuario)

@planejamento_route.route('/sucesso_cadastro')
def sucesso_cadastro():
    return 'Indicador cadastrado com sucesso!'
#################################################################################################################################
@planejamento_route.route('/associar_objetivospe', methods=['GET', 'POST'])
def associar_objetivospe():
    if request.method == 'POST':
        # Aqui vai o código para lidar com o formulário submetido
        nome = request.form['nome']
        planejamento_estrategico_id = request.form['planejamento_id']
        objetivo_pdi_id = request.form['objetivo_id']

        # Cria um novo objetivo PE e o adiciona ao banco de dados
        novo_objetivo = ObjetivoPE(
            nome=nome,
            planejamento_estrategico_id=planejamento_estrategico_id,
            objetivo_pdi_id=objetivo_pdi_id
        )

        db.session.add(novo_objetivo)
        db.session.commit()

        flash('Objetivo cadastrado com sucesso!', 'success')
        return redirect(url_for('get_coordenador'))
    else:
        # Se o método não for POST, obtemos os dados necessários
        planejamento_estrategico = PlanejamentoEstrategico.query.all()
        objetivos_por_planejamento = []

        # Para cada planejamento estratégico, obtemos os objetivos associados
        for pe in planejamento_estrategico:
            objetivos = Objetivo.query.filter_by(pdi_id=pe.pdi_id).all()
            objetivos_por_planejamento.append((pe, objetivos))

        # Renderizamos o formulário HTML com os dados obtidos
        return render_template('objetivope.html', objetivos_por_planejamento=objetivos_por_planejamento)


###################################################################################################################################
@planejamento_route.route('/associar_metaspe', methods=['GET', 'POST'])
def associar_metaspe():
    if request.method == 'POST':
        # Aqui vai o código para lidar com o formulário submetido
        nome = request.form['nome']
        objetivo_pe_id = request.form['objetivo_pe_id']
        porcentagem_execucao = request.form['porcentagem_execucao']
        
        # Verifica se o objetivo existe
        objetivo_pe = ObjetivoPE.query.get(objetivo_pe_id)
        if objetivo_pe is None:
            flash('Objetivo PE não encontrado!', 'error')
            return redirect(url_for('get_coordenador'))
        
        # Cria uma nova meta PE e a associa ao objetivo PE
        nova_meta = MetaPE(
            nome=nome,
            objetivo_pe_id=objetivo_pe_id,
            porcentagem_execucao=porcentagem_execucao
        )

        db.session.add(nova_meta)
        db.session.commit()

        flash('Meta cadastrada com sucesso!', 'success')
        return redirect(url_for('get_coordenador'))
    else:
        # Se o método não for POST, obtenha os dados necessários para o formulário
        # Busca os planejamentos estratégicos
        planejamentos_estrategicos = PlanejamentoEstrategico.query.all()
        
        # Busca os objetivos PE
        objetivos_pe = ObjetivoPE.query.all()
        
        # Renderiza o formulário HTML com os dados obtidos
        return render_template('metaspe.html', planejamentos_estrategicos=planejamentos_estrategicos, objetivos_pe=objetivos_pe)