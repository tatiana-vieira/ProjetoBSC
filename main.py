import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash, current_app,make_response
from sqlalchemy import select, text
from routes.models import (Ensino, Engajamento, Transfconhecimento, Pesquisar, Orientacao, PDI, Meta, Objetivo, Indicador, Producaointelectual, Users, Programa, BSC,
                           MetaPE, IndicadorPlan, AcaoPE, ObjetivoPE, PlanejamentoEstrategico,Risco)
from routes.multidimensional import multidimensional_route
from routes.pdiprppg import pdiprppg_route
from routes.producao import producao_route
from routes.indicador import indicador_route
from routes.login import login_route
from routes.relatorioindicador import relatorioindicador_route
from routes.planejamento import planejamento_route
from routes.relatorioplanejamento import relatorioplanejamento_route
from routes.relatorioacao import relatorioacao_route
from routes.relatoriometas import relatoriometas_route
from routes.altpdi import altpdi_route
from routes.avaliacaodiscente import avaliacaodiscente_route
from routes.graficogrant import graficogrant_route
from routes.graficoacaope import graficoacaope_route
from routes.calculoindicadores import calculoindicadores_route
from routes.graficoindicador import graficoindicador_route
from routes.relatoriocompletos import relatoriocompleto_route
from routes.autoavaliacaodiscente  import autoavaliacaodiscente_route
from routes.autoavaliacaoegresso import autoavaliacaoegresso_route
from routes.autoavaliacaodocente import autoavaliacaodocente_route
from routes.autoavaliacaocoordenador import autoavaliacaocoordenador_route
from routes.analisediscenteclustersia import analisediscenteclustersia_route
from routes.avaliacaodiscente import avaliacaodiscente_route
from routes.avaliacaodocente import avaliacaodocente_route
from routes.avaliacaoegresso import avaliacaoegresso_route
from routes.avaliacaosecretaria import avaliacaosecretaria_route
from routes.avaliacaocoordenador import avaliacaocoordenador_route
from routes.discente import discente_route
from routes.altpdipro import altpdipro_route
from routes.coordenador import coordenador_route
from routes.db import db, init_db
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired
from flask_login import login_required, current_user, UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import pandas as pd
from flask import Flask, render_template
import matplotlib.pyplot as plt
import io
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter, landscape

app = Flask(__name__)


# Configuração de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info('Starting application...')
logger.info('Flask app created')

# Use variáveis de ambiente para configurar a aplicação
app.secret_key = os.getenv("SECRET_KEY", "super secret key")  # Use variável de ambiente para secret key
bcrypt = Bcrypt(app)

# Configuração do banco de dados
os.environ["DATABASE_URL"] = "postgresql://bancodbpprg_user:1KDFiPuohIDURbgqpthOAyw73OwZdArn@dpg-cphr11a1hbls73b85ut0-a.oregon-postgres.render.com/bancodbpprg"
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not set. Please configure the environment variable.")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logger.info('Configurações do banco de dados definidas')

# Inicialize o objeto db com o aplicativo
db.init_app(app)
logger.info('db.init_app(app) executado')

try:
    with app.app_context():
        db.create_all()  # Isso garantirá que todas as tabelas sejam criadas
    logger.info('Database initialized successfully')
except Exception as e:
    logger.error('Database initialization failed: %s', str(e))

# Inicialize o objeto LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
logger.info('LoginManager inicializado')

@login_manager.user_loader
def load_user(user_id):
    logger.info(f'Carregando usuário com ID: {user_id}')
    return Users.query.get(int(user_id))

# Defina o tempo de vida da sessão permanente em segundos
app.permanent_session_lifetime = 3600  # Por exemplo, 1 hora

@app.context_processor
def add_session_config():
    permanent_session_lifetime = current_app.permanent_session_lifetime
    if isinstance(permanent_session_lifetime, int):
        permanent_session_lifetime_ms = permanent_session_lifetime * 1000
    else:
        permanent_session_lifetime_ms = permanent_session_lifetime.seconds * 1000

    return {
        'PERMANENT_SESSION_LIFETIME_MS': permanent_session_lifetime_ms,
    }

logger.info('Configurações de sessão definidas')

app.register_blueprint(login_route)
app.register_blueprint(multidimensional_route)
app.register_blueprint(pdiprppg_route)
app.register_blueprint(producao_route)
app.register_blueprint(indicador_route)
app.register_blueprint(planejamento_route)
app.register_blueprint(relatorioplanejamento_route)
app.register_blueprint(relatorioacao_route)
app.register_blueprint(relatorioindicador_route)
app.register_blueprint(relatoriometas_route)
app.register_blueprint(altpdi_route)
app.register_blueprint(graficogrant_route)
app.register_blueprint(graficoacaope_route)
app.register_blueprint(calculoindicadores_route)
app.register_blueprint(graficoindicador_route)
app.register_blueprint(relatoriocompleto_route)
app.register_blueprint(autoavaliacaoegresso_route)
app.register_blueprint(autoavaliacaodocente_route)
app.register_blueprint(autoavaliacaocoordenador_route)
app.register_blueprint(autoavaliacaodiscente_route)
app.register_blueprint(analisediscenteclustersia_route)
app.register_blueprint(avaliacaodiscente_route)
app.register_blueprint(avaliacaodocente_route)
app.register_blueprint(avaliacaoegresso_route)
app.register_blueprint(avaliacaosecretaria_route)
app.register_blueprint(avaliacaocoordenador_route)
app.register_blueprint(discente_route)
app.register_blueprint(altpdipro_route)
app.register_blueprint(coordenador_route)



@app.route('/')
def index():
    return redirect('/login')

######################################################################################################################################
@app.route('/multidimensional')
def get_multidimensional_data():
    try:
        consulta_ensinoaprendiz1 = db.session.execute(select([Ensino]).where(Ensino.areatematica == 'Ciência da Computação'))
        resultados_ensinoaprendiz1 = [{'nome': row.nome, 'mestradotempocerto': row.mestradotempocerto, 
                                       'equilibriogenero': row.equilibriogenero, 'pessoalacaddoutorado': row.pessoalacaddoutorado,
                                       'contatoambientetrabalho': row.contatoambientetrabalho,'proporcao': row.proporcao,'mestratempocertoletra': row.mestratempocertoletra,
                                       'equilibriogeneroletra': row.equilibriogeneroletra, 'pessoalacademicoletra': row.pessoalacademicoletra,
                                       'contaambienteletra': row.contaambienteletra,'proporcaoletra': row.proporcaoletra,'codigo': row.codigo,'sigla': row.sigla,
                                       'pais': row.pais,'programa': row.programa,'areatematica': row.areatematica,'regiao': row.regiao} for row in consulta_ensinoaprendiz1]

        consulta_engajreg = db.session.execute(select([Engajamento]).where(Engajamento.areatematica == 'Ciência da Computação'))  
        resultados_engajreg = [{'nome': row.nome,'estagio': row.estagio,'publiconjuntareg': row.publiconjuntareg,
                                'rendasfontesreg': row.rendasfontesreg,'codigo':row.codigo,'nome':row.nome,'sigla':row.sigla,'pais':row.pais,
                                'programa': row.programa,'areatematica':row.areatematica,'estagioletra':row.estagioletra,
                                'publiconjuntaregletra':row.publiconjuntaregletra,'rendasfontesregletra':row.rendasfontesregletra,'regiao':row.regiao} for row in consulta_engajreg]

        consulta_transfconhecimento = db.session.execute(select([Transfconhecimento]).where(Transfconhecimento.areatematica == 'Ciência da Computação'))
        resultados_transfconhecimento = [{'nome':row.nome,'rendafonteprivada':row.rendafonteprivada,'copublicparcind': row.copublicparcind,
                                          'publcitadaspatentes':row.publcitadaspatentes,'codigo':row.codigo,'sigla':row.sigla,'pais':row.pais,'programa':row.programa,
                                          'areatematica':row.areatematica,'rendaletra':row.rendaletra,'copubletra':row.copubletra,'publicitadasletra':row.publicitadasletra,
                                          'regiao':row.regiao} for row in consulta_transfconhecimento]

        consulta_pesquisar = db.session.execute(select([Pesquisar]).where(Pesquisar.areatematica== 'Ciência da Computação'))
        resultados_pesquisar = [{'nome':row.nome,'receitapesquisaexterna':row.receitapesquisaexterna,'produtividadedoutorado': row.produtividadedoutorado,
                                 'publpesqabsoluto':row.publpesqabsoluto,'taxacitacao':row.taxacitacao,'publicacaomaicitada':row.publicacaomaicitada,
                                 'publicacaointerdisciplinar': row.publicacaointerdisciplinar,'publicacaoacessoaberto': row.publicacaoacessoaberto,'orientacaoopesqensino':row.orientacaoopesqensino,
                                 'autoras': row.autoras,'codigo': row.codigo,'sigla':row.sigla,'pais': row.pais,'programa':row.programa,'areatematica':row.areatematica,
                                 'receitapesquisaexternaletra': row.receitapesquisaexternaletra,'produtividadedoutoradoletra': row.produtividadedoutoradoletra,'publpesqabsolutoletra':row.publpesqabsolutoletra,'taxacitacaoletra': row.taxacitacaoletra,
                                 'publicacaomaicitadaletra':row.publicacaomaicitadaletra,'publicacaointerdisciplinarletra':row.publicacaointerdisciplinarletra,
                                 'publicacaoacessoabertoletra':row.publicacaoacessoabertoletra,'orientacaoopesqensinoletra':row.orientacaoopesqensinoletra,
                                 'autorasletra':row.autorasletra,'regiao':row.regiao} for row in consulta_pesquisar]

        consulta_orientacaointern = db.session.execute(select([Orientacao]).where(Orientacao.areatematica == 'Ciência da Computação'))
        resultados_orientacaointern = [{'nome': row.nome,'professortitular':row.professortitular,'alunosenvolvidosorient':row.alunosenvolvidosorient,
                                         'prodoutcomorient':row.prodoutcomorient,'publicacoescoautoriaorient':row.publicacoescoautoriaorient,
                                         'publicpubcteorient':row.publicpubcteorient,'prodoutcomorientletra':row.prodoutcomorientletra,
                                         'publicacoescoautoriaorientletra':row.publicacoescoautoriaorientletra,
                                         'publicpubcteorientletra':row.publicpubcteorientletra,'codigo':row.codigo,'sigla':row.sigla,'pais':row.pais,'programa':row.programa,
                                         'areatematica':row.areatematica,'professortitularletra':row.professortitularletra,
                                         'regiao':row.regiao} for row in consulta_orientacaointern]

        return render_template('multidimensional.html', ensino=resultados_ensinoaprendiz1, engajamento=resultados_engajreg,
                                transfconhecimento=resultados_transfconhecimento, pesquisar=resultados_pesquisar,
                                orientacao=resultados_orientacaointern)
    
    except Exception as e:
        logger.error(f"Erro ao buscar dados multidimensionais: {e}")
        db.session.rollback()
        return "Erro ao buscar dados multidimensionais"

#####################################################################################################################################
@app.route('/producao')
def get_producao():
    try:
       producao = db.session.execute(select([Producaointelectual]).where(Producaointelectual.codigoprograma =='32003013008P4'))
       resutado = [{'titulo':row.titulo,'autor': row.autor,'categoria': row.categoria,
        'tipoproducao': row.tipoproducao,'subtipo': row.subtipo,'areaconcentracao': row.areaconcentracao, 
        'linhapesquisa': row.linhapesquisa,'projetopesquisa': row.projetopesquisa,'anaopublicacao':row.anaopublicacao } for row in producao]
    except Exception as e:
        logger.error(f"Erro ao buscar dados de Produção Intelectual: {e}")
        db.session.rollback()
        return "Erro ao buscar dados de Produção Intelectual"    
    
    return render_template('producao.html',producao=resutado)
##########################################################################################################################################

@app.route('/programas')
def get_programas():
    try:
       programas = db.session.query(Programa).all()
       resultados = [{'id':row.id,'codigo': row.codigo,'nome': row.nome} for row in programas]
       return jsonify(resultados)

    except Exception as e:
        logger.error(f"Erro ao buscar dados de Programas: {e}")
        db.session.rollback()
        return "Erro ao buscar dados de Programas"    
   
############################################################## PDI ##############################################
@app.route('/pdi')
def get_pdi():
   try:
       pdi = db.session.query(PDI).all()
       resultados_pdi = [{'id':row.id,'nome': row.nome,'datainicio': row.datainicio,'datafim': row.datafim} for row in pdi]
       return jsonify(resultados_pdi)
   except Exception as e:
        logger.error(f"Erro ao buscar dados do PDI: {e}")
        db.session.rollback()
        return "Erro ao buscar dados do PDI"  
##############################
@app.route('/objetivo')
def get_objetivo():
   try:
       objetivo = db.session.query(Objetivo).all()
       resultados_objetivo = [{'id':row.id,'pdi_id': row.pdi_id,'nome': row.nome,'bsc':row.bsc} for row in objetivo]
       return jsonify(resultados_objetivo) 
   except Exception as e:
        logger.error(f"Erro ao buscar dados de Objetivo: {e}")
        db.session.rollback()
        return "Erro ao buscar dados de Objetivo"
####################################
@app.route('/meta')
def get_meta():
   try:
       meta = db.session.query(Meta).all()
       resultados_meta = [{'id':row.id,'objetivo_id': row.objetivo_id,'nome': row.nome,'porcentagem_execucao':row.porcentagem_execucao} for row in meta]
       return jsonify(resultados_meta)
   except Exception as e:
        logger.error(f"Erro ao buscar dados de Meta: {e}")
        db.session.rollback()
        return "Erro ao buscar dados de Meta"    
#############################################################################################################
@app.route('/indicador')
def get_indicador():
   try:
       indicador = db.session.query(Indicador).all()
       resultados_indicador = [{'id':row.id,'nome': row.nome,'meta_id': row.meta_pe_id} for row in indicador]
       return jsonify(resultados_indicador)
   except Exception as e:
        logger.error(f"Erro ao buscar dados do Indicador: {e}")
        db.session.rollback()
        return "Erro ao buscar dados do Indicador"
#############################################################################################################
@app.route('/metape')
def get_metape():
   try:
       metape = db.session.query(MetaPE).all()
       resultados_meta = [{'id':row.id,'objetivo_pe_id': row.objetivo_pe_id,'nome': row.nome,'porcentagem_execucao':row.porcentagem_execucao} for row in metape]
       return jsonify(resultados_meta)
   except Exception as e:
        logger.error(f"Erro ao buscar dados de Meta: {e}")
        db.session.rollback()
        return "Erro ao buscar dados de Meta" 
##################################################################################################
@app.route('/objetivope')
def get_objetivope():
   try:
       objetivope = db.session.query(ObjetivoPE).all()
       resultados_objetivo = [{'id':row.id,'planejamento_estrategico_id': row.planejamento_estrategico_id,'nome': row.nome,'objetivo_pdi_id':row.objetivo_pdi_id} for row in objetivope]
       return jsonify(resultados_objetivo) 
   except Exception as e:
        logger.error(f"Erro ao buscar dados de Objetivo: {e}")
        db.session.rollback()
        return "Erro ao buscar dados de Objetivo"
##################################################################################################
@app.route('/indicadorpe')
def get_indicadorpe():
   try:
       indicador_pe = db.session.query(IndicadorPlan).all()
       resultados_indicador_pe = [{'id':row.id,'nome': row.nome,'meta_pe_id': row.meta_pe_id} for row in indicador_pe]
       return jsonify(resultados_indicador_pe)
   except Exception as e:
        logger.error(f"Erro ao buscar dados do Indicador: {e}")
        db.session.rollback()
        return "Erro ao buscar dados do Indicador"
##########################################################################################
@app.route('/planejamentorel')
def get_planejamentorelpe():
   try:
       planejamento_estrategico = db.session.query(PlanejamentoEstrategico).all()
       resultados_planejamento = [{'id':row.id,'nome': row.nome,'pdi_id': row.pdi_id,'id_programa':row.id_programa} for row in planejamento_estrategico]
       return jsonify(resultados_planejamento)
   except Exception as e:
        logger.error(f"Erro ao buscar dados do Planejamento: {e}")
        db.session.rollback()
        return "Erro ao buscar dados do Planejamento"
##################################################################################################
@app.route('/acaope')
def get_acaope():
   try:
       acao_pe = db.session.query(AcaoPE).all()
       resultados_acao_pe = [{'id':row.id,'nome': row.nome,'meta_pe_id': row.meta_pe_id,'porcentagem_execucao':row.porcentagem_execucao,'data_inicio':row.data_inicio} for row in acao_pe]
       return jsonify(resultados_acao_pe)
   except Exception as e:
        logger.error(f"Erro ao buscar dados de Ação: {e}")
        db.session.rollback()
        return "Erro ao buscar dados de Ação"
######################################################################################################################
@app.route('/login/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        programa_id = request.form.get('programa_id')

        # Verificar se programa_id está vazio e atribuir None se necessário
        programa_id = int(programa_id) if programa_id else None

        # Hash da senha
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Criação do novo usuário
        new_user = Users(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=role,
            programa_id=programa_id
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect('/login')
        except Exception as e:
            logger.error(f"Erro ao cadastrar usuário: {e}")
            db.session.rollback()
            flash('Erro ao cadastrar usuário. Por favor, tente novamente.', 'danger')

    programas = Programa.query.all()
    return render_template('register.html', programas=programas)


#############Cadastro de PDI ##################################
def processar_formulario_pdi(pdi_id=None):
    nome = request.form.get('nome')
    datainicio = request.form.get('datainicio')
    datafim = request.form.get('datafim')

    if not nome or not datainicio or not datafim:
        return 'Dados incompletos'

    if pdi_id:
        pdi = PDI.query.get(pdi_id)
        if pdi:
            pdi.nome = nome
            pdi.datainicio = datainicio
            pdi.datafim = datafim
            db.session.commit()
            return redirect(url_for('lista_pdis'))  # Redireciona após edição
        else:
            return 'PDI não encontrado'
    else:
        novo_pdi = PDI(nome=nome, datainicio=datainicio, datafim=datafim)
        db.session.add(novo_pdi)
        db.session.commit()
        return redirect(url_for('lista_pdis'))  # Redireciona após cadastro


@app.route('/cadastro_pdi', methods=['GET', 'POST'])
def cadastro_pdi():
    if request.method == 'POST':
        return processar_formulario_pdi()
    return render_template('cadastropdi.html')

from datetime import datetime

from datetime import datetime

@app.route('/editar_pdi/<int:pdi_id>', methods=['GET', 'POST'])
def editar_pdi(pdi_id):
    pdi = PDI.query.get(pdi_id)
    if not pdi:
        return 'PDI não encontrado', 404

    if request.method == 'POST':
        processar_formulario_pdi(pdi_id)
        flash('PDI atualizado com sucesso!', 'success')
        return redirect(url_for('lista_pdis'))
    
    return render_template('cadastropdi.html', pdi=pdi)



@app.route('/lista_pdis')
def lista_pdis():
    pdis = PDI.query.all()
    return render_template('editarpdi.html', pdis=pdis)

@app.route('/sucesso_cadastro')
def sucesso_cadastro():
    return 'Cadastro realizado com sucesso!'

######################Cadastro Objetivo ######################################
@app.route('/lista_objetivos', methods=['GET', 'POST'])
def lista_objetivos():
    filtros = {}
    if request.method == 'POST':
        bsc_filtro = request.form.get('bsc')
        pdi_filtro = request.form.get('pdi_id')
        nome_filtro = request.form.get('nome')

        if bsc_filtro:
            filtros['bsc'] = bsc_filtro
        if pdi_filtro:
            filtros['pdi_id'] = pdi_filtro
        if nome_filtro:
            filtros['nome'] = nome_filtro

    objetivos = Objetivo.query.filter_by(**filtros).options(joinedload(Objetivo.pdi)).distinct().all()
    lista_pdis = PDI.query.all()
    return render_template('lista_objetivos.html', objetivos=objetivos, lista_pdis=lista_pdis)




def atualizar_progresso_objetivo(objetivo_id):
    objetivo = Objetivo.query.get(objetivo_id)
    if objetivo.indicadores:
        progresso_total = sum(
            indicador.valor_atual / indicador.valor_esperado
            for indicador in objetivo.indicadores
            if indicador.valor_esperado > 0
        )
        objetivo.progresso = round((progresso_total / len(objetivo.indicadores)) * 100, 2)
    else:
        objetivo.progresso = 0
    db.session.commit()


@app.route('/vincular_indicador/<int:objetivo_id>', methods=['GET', 'POST'])
def vincular_indicador(objetivo_id):
    objetivo = Objetivo.query.get_or_404(objetivo_id)
    error_message = None

    if request.method == 'POST':
        indicador_id = request.form['indicador_id']
        indicador = Indicador.query.get_or_404(indicador_id)
        if indicador.objetivo_id:
            error_message = f"Indicador '{indicador.nome}' já está vinculado a outro objetivo."
        else:
            indicador.objetivo_id = objetivo.id
            db.session.commit()
            return redirect(url_for('editar_objetivo', objetivo_id=objetivo.id))

    indicadores_disponiveis = Indicador.query.filter_by(objetivo_id=None).all()  # Apenas indicadores não vinculados
    return render_template('vincular_indicador.html', objetivo=objetivo, indicadores=indicadores_disponiveis, error_message=error_message)


 
@app.route('/cadastro_objetivo', methods=['GET', 'POST'])
def cadastro_objetivo():
    objetivo_id = request.args.get('id')  # Tenta recuperar o ID do objetivo
    objetivo = None
    error_message = None

    if objetivo_id:
        try:
            objetivo = Objetivo.query.get(int(objetivo_id))  # Busca o objetivo pelo ID
            if not objetivo:
                error_message = f"Objetivo com ID {objetivo_id} não encontrado."
        except ValueError:
            error_message = f"ID inválido fornecido: {objetivo_id}"

    lista_pdis = PDI.query.all()
    return render_template(
        'cadastro_objetivo.html',
        lista_pdis=lista_pdis,
        objetivo=objetivo,
        success_message=None,
        error_message=error_message  # Envia mensagens de erro ao template
    )




@app.route('/editar_objetivo/<int:objetivo_id>', methods=['GET', 'POST'])
def editar_objetivo(objetivo_id):
    success_message = None
    objetivo = Objetivo.query.get_or_404(objetivo_id)
    
    if request.method == 'POST':
        success_message = processar_formulario_objetivo(objetivo_id)
    
    lista_pdis = PDI.query.all()
    return render_template('cadastro_objetivo.html', objetivo=objetivo, lista_pdis=lista_pdis, success_message=success_message)


def processar_formulario_objetivo(objetivo_id=None):
    if 'email' not in session:
        return 'Acesso não autorizado'

    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    pdi_id = request.form.get('pdi_id')
    nome = request.form.get('nome')
    bsc = request.form.get('bsc')
    descricao = request.form.get('descricao')

    if not all([pdi_id, nome, bsc, descricao]):
        return "Todos os campos são obrigatórios."

    if objetivo_id:
        # Editar objetivo existente
        objetivo = Objetivo.query.get(objetivo_id)
        objetivo.pdi_id = pdi_id
        objetivo.nome = nome
        objetivo.bsc = bsc
        objetivo.descricao = descricao
        db.session.commit()
        return "Objetivo alterado com sucesso"
    else:
        # Verificar duplicidade de objetivo
        objetivo_existente = Objetivo.query.filter_by(nome=nome, pdi_id=pdi_id).first()
        if objetivo_existente:
            return "Um objetivo com este nome já existe neste PDI."

        # Criar novo objetivo
        novo_objetivo = Objetivo(pdi_id=pdi_id, nome=nome, bsc=bsc, descricao=descricao)
        db.session.add(novo_objetivo)
        db.session.commit()
        return "Objetivo cadastrado com sucesso"


@app.route('/excluir_objetivo/<int:objetivo_id>', methods=['POST'])
def excluir_objetivo(objetivo_id):
    objetivo = Objetivo.query.get_or_404(objetivo_id)
    db.session.delete(objetivo)
    db.session.commit()
    return redirect(url_for('lista_objetivos'))

##############################################################################################################################
###########################################################################################################################

@app.route('/cadastro_meta', methods=['GET', 'POST'])
def cadastro_meta():
    if request.method == 'POST':
        return processar_formulario_meta()

    lista_pdis = PDI.query.all()  # Lista todos os PDIs cadastrados
    pdi_id = request.args.get('pdi_id')
    if pdi_id:
        objetivos = buscar_objetivos_relacionados_pdi(int(pdi_id))  # Obtém objetivos relacionados ao PDI selecionado
    else:
        objetivos = []

    # Renderiza o template com os dados disponíveis
    return render_template('cadastro_meta.html', lista_pdis=lista_pdis, objetivos=objetivos, datetime=datetime)



def processar_formulario_meta():
    if 'email' not in session:
        flash('Acesso não autorizado', 'error')
        return redirect(url_for('login_page'))

    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        flash('Acesso não autorizado', 'error')
        return redirect(url_for('login_page'))

    objetivo_id = request.form['objetivo_id']
    nome = request.form['nome']
    descricao = request.form.get('descricao', '')  # Campo opcional
    prazo_final = request.form['prazo_final']
    responsavel = request.form.get('responsavel', '')  # Campo opcional
    porcentagem_execucao = request.form.get('porcentagem_execucao', 0)  # Padrão: 0%

    novo_meta = Meta(
        objetivo_id=objetivo_id,
        nome=nome,
        descricao=descricao,
        prazo_final=datetime.strptime(prazo_final, '%Y-%m-%d'),
        responsavel=responsavel,
        porcentagem_execucao=porcentagem_execucao
    )
    db.session.add(novo_meta)
    db.session.commit()

    flash('Meta cadastrada com sucesso!', 'success')
    return redirect(url_for('cadastro_meta'))



def buscar_objetivos_relacionados_pdi(pdi_id):
    # Retorna os objetivos relacionados ao PDI específico
    return Objetivo.query.filter_by(pdi_id=pdi_id).all()


@app.route('/metas_relacionadas_pdi/<int:pdi_id>')
def metas_relacionadas_pdi(pdi_id):
    objetivos = buscar_objetivos_relacionados_pdi(pdi_id)
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()

    # Serializa os dados para JSON
    data = [
        {
            'id': meta.id,
            'nome': meta.nome,
            'objetivo_nome': meta.objetivo.nome,
            'porcentagem_execucao': meta.porcentagem_execucao,
            'data_ultima_atualizacao': meta.data_ultima_atualizacao.strftime('%d/%m/%Y') if meta.data_ultima_atualizacao else None
        }
        for meta in metas
    ]
    return jsonify(data)


@app.route('/filtrar_metas', methods=['GET'])
def filtrar_metas():
    status = request.args.get('status')
    now = datetime.utcnow()

    if status == 'atrasada':
        metas = Meta.query.filter(Meta.prazo_final < now, Meta.porcentagem_execucao < 100).all()
    elif status == 'concluida':
        metas = Meta.query.filter(Meta.porcentagem_execucao == 100).all()
    else:  # Em andamento
        metas = Meta.query.filter(Meta.prazo_final >= now, Meta.porcentagem_execucao < 100).all()

    # Serializa os dados para JSON
    data = [
        {
            'id': meta.id,
            'nome': meta.nome,
            'descricao': meta.descricao,
            'responsavel': meta.responsavel or 'Não atribuído',
            'prazo_final': meta.prazo_final.strftime('%d/%m/%Y') if meta.prazo_final else None,
            'porcentagem_execucao': meta.porcentagem_execucao
        }
        for meta in metas
    ]
    return jsonify(data)


def verificar_alertas_metas():
    now = datetime.utcnow()

    metas_atrasadas = Meta.query.filter(Meta.prazo_final < now, Meta.porcentagem_execucao < 100).all()
    metas_concluidas = Meta.query.filter(Meta.porcentagem_execucao == 100).all()

    return {
        "atrasadas": len(metas_atrasadas),
        "concluidas": len(metas_concluidas),
        "total": Meta.query.count()
    }

#####################################################################3
@app.route('/selecionar_pdi_para_alteracao', methods=['GET'])
def selecionar_pdi_para_alteracao():
    # Obter a lista de PDIs do banco de dados
    lista_pdis = PDI.query.all()
    return render_template('selecionar_pdi_meta.html', lista_pdis=lista_pdis)


@app.route('/escolher_objetivo_para_alteracao', methods=['GET'])
def escolher_objetivo_para_alteracao():
    pdi_id = request.args.get('pdi_id')
    if not pdi_id:
        return redirect(url_for('selecionar_pdi_para_alteracao'))

    # Buscar objetivos relacionados ao PDI selecionado
    objetivos = buscar_objetivos_relacionados_pdi(int(pdi_id))
    return render_template('escolher_objetivo_meta.html', pdi_id=pdi_id, objetivos=objetivos)


##########################################################3
@app.route('/editar_meta/<float:meta_id>', methods=['GET', 'POST'])
def editar_meta(meta_id):
    meta = Meta.query.get_or_404(meta_id)
    if request.method == 'POST':
        meta.nome = request.form['nome']
        meta.porcentagem_execucao = request.form['porcentagem_execucao']
        db.session.commit()
        flash('Meta alterada com sucesso!', 'success')
        return redirect(url_for('cadastro_meta'))
    return render_template('alterarmetapdi.html', meta=meta)


@app.route('/alterar_meta', methods=['POST'])
def alterar_meta():
    meta_id = request.form['meta_id']
    meta = Meta.query.get_or_404(meta_id)
    
    meta.nome = request.form['nome']
    meta.porcentagem_execucao = request.form['porcentagem_execucao']
    db.session.commit()
    
    flash('Meta alterada com sucesso!', 'success')
    return redirect(url_for('cadastro_meta'))

@app.route('/objetivos_relacionados_pdi/<int:pdi_id>')
def objetivos_relacionados_pdi(pdi_id):
    # Verifica se o usuário está logado e é um Pró-reitor
    
    user = Users.query.filter_by(email=session['email']).first()

    # Busca os objetivos relacionados ao PDI
    objetivos = buscar_objetivos_relacionados_pdi(pdi_id)

    # Imprime os objetivos relacionados para verificação
    print("Objetivos relacionados:", objetivos)

    # Retorna os objetivos relacionados como dados JSON
    objetivos_data = [{'id': objetivo.id, 'nome': objetivo.nome} for objetivo in objetivos]
    return jsonify(objetivos_data)

# Rota para obter metas relacionadas a um objetivo
@app.route('/metas_relacionadas_objetivo/<int:objetivo_id>')
def metas_relacionadas_objetivo(objetivo_id):
    metas = Meta.query.filter_by(objetivo_id=objetivo_id).all()
    return jsonify([{'id': meta.id, 'nome': meta.nome} for meta in metas])

# Rota para obter detalhes de uma meta específica
@app.route('/detalhes_meta/<int:meta_id>')
def detalhes_meta(meta_id):
    meta = Meta.query.get(meta_id)
    if meta:
        return jsonify({
            'nome': meta.nome,
            'porcentagem_execucao': meta.porcentagem_execucao
        })
    return jsonify({'error': 'Meta não encontrada'}), 404



###################################################3
@app.route('/sucesso_alteracao')
def sucesso_alteracao():
    return render_template('sucesso_alteracao.html')  # Crie um template para essa página

# Função auxiliar para buscar objetivos relacionados ao PDI
def buscar_objetivos_relacionados_pdi(pdi_id):
    # Buscar objetivos baseados em um ID de PDI
    return Objetivo.query.filter_by(pdi_id=pdi_id).all()

    
################################################################################################################################
######################################################################
###############################################################
@app.route('/visualizacao')
def visualizacao():
     return render_template('bsc.html')

@app.route('/register')
def register():
  return render_template('register.html')

@app.route('/logout')
def logout():
    logger.info('Rota de logout acessada')  # Registra quando a rota é acessada
    session.pop('email', None)  # Remove a chave de e-mail da sessão
    logger.info('Chave de sessão removida')  # Registra quando a chave de sessão é removida
    return render_template('logout.html')

##########################################################################################################################
class CadastroForm(FlaskForm):
    objetivo = SelectField('Objetivo do PDI', coerce=int)
    objetivo_novo = StringField('Novo Objetivo')
    meta_descricao = StringField('Descrição da Meta', validators=[DataRequired()])
    indicador_descricao = StringField('Descrição do Indicador', validators=[DataRequired()])
    acao_descricao = StringField('Descrição da Ação', validators=[DataRequired()])
    valor_realizado = StringField('Valor Realizado')
    submit = SubmitField('Enviar')
################################################Planejamento estrategico######################################################################
@app.route('/cadastro_planejamentope', methods=['GET', 'POST'])
def cadastro_planejamentope():
    if 'email' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login_page'))

    nome = request.form['nome']
    pdi_id = request.form['pdi_id']

    # Verifique se o usuário está autenticado e se é um coordenador
    if 'programa_id' not in session:
        flash('Nenhum programa do usuário encontrado. Faça login novamente.', 'danger')
        return redirect(url_for('login.login_page'))

    programa_id = session['programa_id']  # Recupere o programa_id da sessão

    novo_planejamento = PlanejamentoEstrategico(pdi_id=pdi_id, nome=nome, programa_id=programa_id)
    print(novo_planejamento)

    try:
        # Adicione o novo planejamento ao banco de dados
        db.session.add(novo_planejamento)
        db.session.commit()
        flash('Planejamento cadastrado com sucesso!', 'success')
        return redirect(url_for('get_coordenador')) 
    except Exception as e:
        logger.error(f"Erro ao cadastrar planejamento: {e}")
        db.session.rollback()
        flash('Erro ao cadastrar planejamento. Por favor, tente novamente.', 'danger')
        return redirect(url_for('get_coordenador'))

def processar_formulario_planejamentope(programa_do_usuario):
    # Verifica se o usuário está logado e é um Coordenador
    if not current_user.is_authenticated or current_user.role != 'Coordenador':
        return 'Acesso não autorizado'
    
    # Extrai os dados do formulário
    pdi_id = request.form['pdi_id']
    nome = request.form['nome']
    programa_id = request.form['programa_id']
    
    # Verifica se o programa_id do usuário corresponde ao programa_id fornecido no formulário
    if programa_id != programa_do_usuario.id:
        return 'Acesso não autorizado'
    
    # Insere os dados no banco de dados, incluindo o programa do usuário
    novo_planejamento = PlanejamentoEstrategico(pdi_id=pdi_id, nome=nome, programa=programa_do_usuario, programa_id=programa_id)
    db.session.add(novo_planejamento)
    db.session.commit()
    
    # Renderiza o template 'planejamento.html' com os dados da lista_pdispe
    return redirect(url_for('sucesso_cadastro'))
######################################################################################
@app.route('/rota_protegida')
@login_required
def rota_protegida():
    # Armazena a URL atual na sessão
    session['previous_url'] = request.url
    # Esta rota só será acessível para usuários autenticados
    return 'Esta rota é protegida!'
##################################################################################################################################

##################################################################################################################################
########################################################################################################
@app.route('/associar_indicadorespe', methods=['GET', 'POST'])
def associar_indicadorespe():
    if request.method == 'POST':
        meta_pe_id = request.form['meta_pe_id']
        nome_indicador = request.form['nome']
        descricao = request.form['descricao ']

        meta_pe =MetaPE.query.get(meta_pe_id)
        if meta_pe is None:
            flash('Meta não encontrada!', 'error')
            return redirect(url_for('get_coordenador'))
        
        # Criar um novo indicador associado à meta
        novo_indicador = IndicadorPlan(nome=nome_indicador, meta_pe_id=meta_pe_id,descricao=descricao)
        db.session.add(novo_indicador)
        db.session.commit()
        
        return 'Indicador cadastrado com sucesso!'
    
    # Se o método for GET, renderize o template HTML
    return render_template('indicadorpe.html')
##############################################################################################################
########################################################################################################
@app.route('/associar_acaope', methods=['GET', 'POST'])
def associar_acaope():
    if request.method == 'POST':
        meta_pe_id = request.form['meta_pe_id']
        nome = request.form['nome']
        porcentagem_execucao = request.form['porcentagem_execucao']   
        data_inicio = request.form['data_inicio']
        data_termino = request.form['data_termino']       


        meta_pe =MetaPE.query.get(meta_pe_id)
        if meta_pe is None:
            flash('Meta não encontrada!', 'error')
            return redirect(url_for('get_coordenador'))
        
        # Criar um novo indicador associado à meta
        nova_acao = AcaoPE(nome=nome, meta_pe_id=meta_pe_id,porcentagem_execucao=porcentagem_execucao,data_inicio=data_inicio,data_termino=data_termino)
        db.session.add(nova_acao)
        db.session.commit()
        
        return 'Ação cadastrada com sucesso!'
    
    # Se o método for GET, renderize o template HTML
    return render_template('acaope.html')

################################################################################################################################

@app.route('/relplano')
def relatorio_planejamento():
    # Aqui você pode adicionar qualquer lógica necessária para renderizar a página de planejamento estratégico
    return render_template('relplanejamento.html')
#################################################################################################################################
@app.route('/associar_metaspe', methods=['GET', 'POST'])
def associar_metaspe():

    # Aqui você pode adicionar qualquer lógica necessária para renderizar a página de planejamento estratégico
      return render_template('relatoriometas.html')
#################################################################################################################################
##############################################################################################################################
@app.route('/altpdi', methods=['GET', 'POST'])
def exibir_altpdi():
    if request.method == 'POST':
        pdi_id = request.form.get('pdi_id')
        return redirect(url_for('exibir_altpdi', pdi_id=pdi_id))

    pdi_id = request.args.get('pdi_id')
    if not pdi_id:
        pdi_data = PDI.query.all()
        return render_template('selecionar_programa.html', pdis=pdi_data)
    
    pdi_data = PDI.query.filter_by(id=pdi_id).first()
    if not pdi_data:
        flash('PDI não encontrado.')
        return redirect(url_for('exibir_altpdi'))

    objetivos = Objetivo.query.filter_by(pdi_id=pdi_id).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()

    return render_template('altpdi.html', pdi=pdi_data, objetivos=objetivos, metas=metas, indicadores=indicadores)


#######################################################################3
@app.route('/altpdipro', methods=['GET', 'POST'])
def exibir_altipdipro():
    if request.method == 'POST':
        pdi_id = request.form.get('pdi_id')
        return redirect(url_for('exibir_altpdipro', pdi_id=pdi_id))

    pdi_id = request.args.get('pdi_id')
    if not pdi_id:
        pdi_data = PDI.query.all()
        return render_template('selecionar_programapro.html', pdis=pdi_data)
    
    pdi_data = PDI.query.filter_by(id=pdi_id).first()
    if not pdi_data:
        flash('PDI não encontrado.')
        return redirect(url_for('exibir_altipdipro'))

    objetivos = Objetivo.query.filter_by(pdi_id=pdi_id).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()

    return render_template('altpdipro.html', pdi=pdi_data, objetivos=objetivos, metas=metas, indicadores=indicadores)


##################################################################################33
#######################################################
@app.route('/dbtest')
def dbtest():
    try:
        result = db.session.execute(text('SELECT 1')).scalar()
        logger.info('Teste de conexão com o banco de dados bem-sucedido')
        return 'Database connection successful!'
    except Exception as e:
        logger.error(f'Teste de conexão com o banco de dados falhou: {e}')
        return f'Database connection failed: {e}'
##################################################################################3
@app.route('/monitoramento', methods=['GET', 'POST'])
@login_required
def monitoramento():
    user_id = current_user.id
    programa_id = current_user.programa_id

    if not programa_id:
        flash("Usuário não tem um programa associado.", "error")
        return redirect(url_for('get_coordenador'))

    # Carregando planejamentos
    planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
    print(f"Planejamentos carregados: {planejamentos}")

    planejamento_selecionado = None
    objetivos = []
    metas = []
    indicadores = []
    acoes = []
    riscos = []

    if request.method == 'POST':
        planejamento_id = request.form.get('planejamento_id')
        if planejamento_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_id)
            print(f"Planejamento selecionado: {planejamento_selecionado}")

            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
            print(f"Objetivos carregados: {objetivos}")

            metas = MetaPE.query.join(ObjetivoPE).filter(ObjetivoPE.planejamento_estrategico_id == planejamento_id).all()
            print(f"Metas carregadas: {metas}")

            indicadores = IndicadorPlan.query.join(MetaPE).filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
            print(f"Indicadores carregados: {indicadores}")

            acoes = AcaoPE.query.join(MetaPE).filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
            print(f"Ações carregadas: {acoes}")

            riscos = Risco.query.join(MetaPE).filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
            print(f"Riscos carregados: {riscos}")

            # Calcular tempo restante para metas
            for meta in metas:
                if meta.data_termino:
                    meta.tempo_restante = (meta.data_termino - datetime.now().date()).days
                else:
                    meta.tempo_restante = 'Indefinido'
                print(f"Tempo restante para meta '{meta.nome}': {meta.tempo_restante}")

            # Calcular tempo restante para ações
            for acao in acoes:
                if acao.data_termino:
                    acao.tempo_restante = (acao.data_termino - datetime.now().date()).days
                else:
                    acao.tempo_restante = 'Indefinido'
                print(f"Tempo restante para ação '{acao.nome}': {acao.tempo_restante}")

    return render_template('monitoramento.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, objetivos=objetivos, metas=metas, indicadores=indicadores, acoes=acoes, riscos=riscos)

###################################################################################
@app.route('/monitoramento/gerar_pdf/<int:planejamento_id>', methods=['GET'])
@login_required
def gerar_pdf(planejamento_id):
    planejamento = PlanejamentoEstrategico.query.get_or_404(planejamento_id)
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas])).all()
    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).all()
    riscos = Risco.query.filter(Risco.meta_pe_id.in_([meta.id for meta in metas])).all()

    # Calcular tempo restante para metas
    for meta in metas:
        if meta.data_termino:
            meta.tempo_restante = (meta.data_termino - datetime.now().date()).days
        else:
            meta.tempo_restante = 'Indefinido'

    # Calcular tempo restante para ações
    for acao in acoes:
        if acao.data_termino:
            acao.tempo_restante = (acao.data_termino - datetime.now().date()).days
        else:
            acao.tempo_restante = 'Indefinido'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(name='Normal', fontSize=8)
    style_heading = ParagraphStyle(name='Heading', fontSize=10, fontName="Helvetica-Bold")

    elements.append(Paragraph("Relatório de Planejamento Estratégico", styles['Title']))

    elements.append(Paragraph("Objetivos", style_heading))
    objetivos_data = [["Nome"]]
    for objetivo in objetivos:
        objetivos_data.append([Paragraph(str(objetivo.nome), style_normal)])
    objetivos_table = Table(objetivos_data, colWidths=[450])
    objetivos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(objetivos_table)

    elements.append(Paragraph("Metas", style_heading))
    metas_data = [["Nome", "Status Inicial", "Tempo Restante (dias)"]]
    for meta in metas:
        metas_data.append([Paragraph(str(meta.nome), style_normal), Paragraph(str(meta.status_inicial), style_normal), Paragraph(str(meta.tempo_restante), style_normal)])
    metas_table = Table(metas_data, colWidths=[200, 100, 150])
    metas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(metas_table)

    elements.append(Paragraph("Indicadores", style_heading))
    indicadores_data = [["Nome", "Peso", "Frequência de Coleta"]]
    for indicador in indicadores:
        indicadores_data.append([Paragraph(str(indicador.nome), style_normal), Paragraph(str(indicador.peso), style_normal), Paragraph(str(indicador.frequencia_coleta), style_normal)])
    indicadores_table = Table(indicadores_data, colWidths=[200, 100, 150])
    indicadores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(indicadores_table)

    elements.append(Paragraph("Ações", style_heading))
    acoes_data = [["Nome", "Porcentagem de Execução", "Status", "Tempo Restante (dias)"]]
    for acao in acoes:
        acoes_data.append([Paragraph(str(acao.nome), style_normal), Paragraph(str(acao.porcentagem_execucao), style_normal), Paragraph(str(acao.status), style_normal), Paragraph(str(acao.tempo_restante), style_normal)])
    acoes_table = Table(acoes_data, colWidths=[200, 100, 100, 100])
    acoes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(acoes_table)

    elements.append(Paragraph("Riscos", style_heading))
    riscos_data = [["Descrição", "Ação Preventiva", "Impacto"]]
    for risco in riscos:
        riscos_data.append([Paragraph(str(risco.descricao), style_normal), Paragraph(str(risco.acao_preventiva), style_normal), Paragraph(str(risco.impacto), style_normal)])
    riscos_table = Table(riscos_data, colWidths=[200, 200, 100])
    riscos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(riscos_table)

    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'inline; filename=planejamento.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response

########################################Analise de IA###################################################
@app.route('/autoavaliacao/analisar_feedback', methods=['POST'])
def analisar_feedback_route():
    # Obter os comentários do formulário ou banco de dados
    comentarios = request.form.getlist('comentarios')
    
    # Chamar a função de análise de feedback
    sentimentos, palavras_chave = analisar_feedback(comentarios)
    
    # Passar os resultados para o template
    return render_template('resultado_analise.html', sentimentos=sentimentos, palavras_chave=palavras_chave)

###########################################################################
@app.route('/importar_planilha_feedback', methods=['GET', 'POST'])
@login_required
def importar_planilha_feedback():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)

        if file:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            filename = os.path.join(upload_folder, 'feedback.xlsx')

            try:
                file.save(filename)
                print(f"Arquivo salvo com sucesso em {filename}")
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")
                flash(f'Erro ao salvar o arquivo: {e}', 'danger')
                return redirect(request.url)

            try:
                # Ler e processar a planilha
                feedback_data = pd.read_excel(filename)
                print(f"Colunas disponíveis no dataframe: {feedback_data.columns}")

                # Realizar a análise (por exemplo, análise de sentimentos)
                feedback_data['Classificacao Sentimento'] = feedback_data['Comentario'].apply(analisar_sentimentos)

                # Salvar o dataframe em um arquivo temporário
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
                with open(temp_file.name, 'wb') as f:
                    pickle.dump(feedback_data, f)
                print(f"Dataframe salvo temporariamente em {temp_file.name}")

                # Armazenar o caminho do arquivo temporário na sessão
                session['dataframe_file'] = temp_file.name

                return redirect(url_for('mostrar_resultado_feedback'))

            except Exception as e:
                print(f"Erro ao processar a planilha: {e}")
                flash(f'Erro ao processar a planilha: {e}', 'danger')
                return redirect(request.url)

    return render_template('importar_planilha_feedback.html')

@app.route('/resultado_feedback')
@login_required
def mostrar_resultado_feedback():
    # Carregar o dataframe da sessão
    dataframe_file = session.get('dataframe_file')
    if dataframe_file:
        with open(dataframe_file, 'rb') as f:
            feedback_data = pickle.load(f)
        
        # Renderizar a página de resultados
        return render_template('resultado_feedback.html', dados=feedback_data.to_dict(orient='records'))
    else:
        flash('Nenhum dado de feedback encontrado', 'danger')
        return redirect(url_for('importar_planilha_feedback'))


################################# Analise cluster discente##############################################3
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from matplotlib import pyplot as plt
import pandas as pd
import io

@app.route('/exibir_relatorio_pdi')
@login_required
def exibir_relatorio_pdi():
    # Obtenha os dados reais do banco de dados
    pdi_data = PDI.query.all()
    objetivos = Objetivo.query.filter(Objetivo.pdi_id.in_([pdi.id for pdi in pdi_data])).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()
    
    # Organizar dados para exibição
    data = []
    for objetivo in objetivos:
        for meta in metas:
            if meta.objetivo_id == objetivo.id:
                for indicador in indicadores:
                    if indicador.meta_pdi_id == meta.id:
                        data.append({
                            'Objetivo': objetivo.nome,
                            'Meta': meta.nome,
                            'Porcentagem Execução': meta.porcentagem_execucao,
                            'Indicador': indicador.nome,
                            'Valor Atual': indicador.valor_atual,
                            'Valor Esperado': indicador.valor_esperado
                        })

    # Renderizar os dados na página
    return render_template('relatorio_pdi.html', data=data)

@app.route('/gerar_relatorio_pdi_pdf')
@login_required
def gerar_relatorio_pdi_pdf():
    # Obtenha os dados reais do banco de dados
    pdi_data = PDI.query.all()
    objetivos = Objetivo.query.filter(Objetivo.pdi_id.in_([pdi.id for pdi in pdi_data])).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()
    
    # Organizar dados para o relatório
    data = []
    for objetivo in objetivos:
        for meta in metas:
            if meta.objetivo_id == objetivo.id:
                for indicador in indicadores:
                    if indicador.meta_pdi_id == meta.id:
                        data.append([
                            objetivo.nome,
                            meta.nome,
                            f"{meta.porcentagem_execucao}%",
                            indicador.nome,
                            indicador.valor_atual,
                            indicador.valor_esperado
                        ])

    # Defina o estilo para o texto
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]

    # Transforme os dados para serem exibidos no PDF
    table_data = [
        [Paragraph("<b>Objetivo</b>", style_normal), Paragraph("<b>Meta</b>", style_normal),
         Paragraph("<b>Porcentagem Execução</b>", style_normal), Paragraph("<b>Indicador</b>", style_normal),
         Paragraph("<b>Valor Atual</b>", style_normal), Paragraph("<b>Valor Esperado</b>", style_normal)]
    ]

    for row in data:
        table_data.append([Paragraph(cell, style_normal) if isinstance(cell, str) else cell for cell in row])

    # Configuração de tabela
    table = Table(table_data, colWidths=[100, 120, 80, 100, 60, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # Criação do PDF
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)  # retrato

    elements = []
    elements.append(Paragraph("Relatório de Progresso do PDI", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(table)

    doc.build(elements)
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, as_attachment=True, download_name='relatorio_pdi.pdf', mimetype='application/pdf')
#######################################################################################################33333
@app.route('/analise_saude_pdi')
@login_required
def analise_saude_pdi():
    pdIs = PDI.query.all()  # Supondo que você tenha uma lista de PDIs

    # Calcule os scores para cada PDI
    pdi_data = []
    for pdi in pdIs:
        consistencia_score = avaliar_consistencia(pdi)
        frequencia_score = avaliar_frequencia_atualizacoes(pdi)
        cumprimento_score = avaliar_cumprimento_metas(pdi)

        pdi_data.append({
            'nome': pdi.nome,
            'consistencia_score': consistencia_score,
            'frequencia_score': frequencia_score,
            'cumprimento_score': cumprimento_score
        })

    return render_template('analise_saude_pdi.html', pdi_data=pdi_data)


def calcular_benchmark(pdi_id):
    pdi = PDI.query.get(pdi_id)
    # Obtenha os valores médios de outros PDIs
    benchmark_media = db.session.query(db.func.avg(PDI.saude)).filter(PDI.id != pdi_id).scalar()
    
    # Comparação e análise de posição
    diferenca = pdi.saude - benchmark_media
    return {
        'saude_pdi': pdi.saude,
        'benchmark_media': benchmark_media,
        'diferenca': diferenca
    }

def avaliar_frequencia_atualizacoes(pdi):
    total_atualizacoes = 0
    total_periodos = 0
    
    for objetivo in pdi.objetivos:
        for meta in objetivo.metas:
            if meta.data_ultima_atualizacao:
                dias_desde_atualizacao = (datetime.now() - meta.data_ultima_atualizacao).days
                # Evita divisão por zero
                if dias_desde_atualizacao > 0:
                    total_atualizacoes += 1 / dias_desde_atualizacao  # Menor intervalo dá maior peso
                    total_periodos += 1
                else:
                    # Caso onde dias_desde_atualizacao é zero (atualizado hoje)
                    total_atualizacoes += 1  # Considera como uma atualização completa
                    total_periodos += 1

    # Frequência média de atualizações em dias
    frequencia_score = (total_atualizacoes / total_periodos) * 100 if total_periodos > 0 else 0
    return frequencia_score



def avaliar_cumprimento_metas(pdi):
    total_metas = 0
    metas_cumpridas = 0

    for objetivo in pdi.objetivos:
        for meta in objetivo.metas:
            for indicador in meta.indicadores:
                # Verifica se `valor_atual` e `valor_esperado` não são `None`
                if indicador.valor_atual is not None and indicador.valor_esperado is not None:
                    if indicador.valor_atual >= indicador.valor_esperado:
                        metas_cumpridas += 1
                total_metas += 1

    # Calcula a porcentagem de metas cumpridas
    cumprimento_score = (metas_cumpridas / total_metas) * 100 if total_metas > 0 else 0
    return cumprimento_score


def calcular_saude_pdi(pdi):
    consistencia_score = avaliar_consistencia(pdi)
    frequencia_score = avaliar_frequencia_atualizacoes(pdi)
    cumprimento_score = avaliar_cumprimento_metas(pdi)

    # Combinação das pontuações com pesos específicos
    saude_total = (consistencia_score * 0.4) + (frequencia_score * 0.3) + (cumprimento_score * 0.3)
    return saude_total

def avaliar_consistencia(pdi):
    total_objetivos = len(pdi.objetivos)
    objetivos_consistentes = 0

    for objetivo in pdi.objetivos:
        metas = objetivo.metas
        # Verifica se o objetivo tem pelo menos uma meta e se cada meta tem pelo menos um indicador
        if metas and all(meta.indicadores for meta in metas):
            objetivos_consistentes += 1

    # Calcula a pontuação de consistência como a porcentagem de objetivos consistentes
    consistencia_score = (objetivos_consistentes / total_objetivos) * 100 if total_objetivos > 0 else 0
    return consistencia_score


##########################################################################################################
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)