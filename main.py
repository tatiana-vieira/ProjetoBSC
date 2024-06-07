import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash, current_app
from sqlalchemy import select, text
from routes.models import (Ensino, Engajamento, Transfconhecimento, Pesquisar, Orientacao, PDI, Meta, Objetivo, Indicador, Producaointelectual, Users, Programa, BSC,
                           MetaPE, IndicadorPlan, AcaoPE, ObjetivoPE, PlanejamentoEstrategico)
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
from routes.graficogrant import graficogrant_route
from routes.graficoacaope import graficoacaope_route
from routes.calculoindicadores import calculoindicadores_route
from routes.graficoindicador import graficoindicador_route
from routes.relatoriocompletos import relatoriocompleto_route
from routes.db import db, init_db
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired
from flask_login import login_required, current_user, UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload

app = Flask(__name__)
#################################################
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Adiciona um handler de arquivo para registrar erros
handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info('Starting application...')
logger.info('Flask app created')

app.secret_key = "super secret key"
bcrypt = Bcrypt(app)

# Configuração do banco de dados
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:plYrJhKoYunNJZZRDQDOOzfiFSTJkFxd@monorail.proxy.rlwy.net:47902/railway')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialize o objeto db com o aplicativo
db = SQLAlchemy(app)

# Inicialize o objeto db com o aplicativo
try:
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Isso garantirá que todas as tabelas sejam criadas
    logger.info('Database initialized successfully')
except Exception as e:
    logger.error('Database initialization failed: %s', str(e))


# Inicialize o objeto Bcrypt
bcrypt = Bcrypt(app)

# Inicialize o objeto LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Defina o tempo de vida da sessão permanente em segundos
app.permanent_session_lifetime = 3600  # Por exemplo, 1 hora

@app.context_processor
def add_session_config():
    """Add current_app.permanent_session_lifetime converted to milliseconds
    to context. The config variable PERMANENT_SESSION_LIFETIME is not
    used because it could be either a timedelta object or an integer
    representing seconds.
    """
    permanent_session_lifetime = current_app.permanent_session_lifetime
    if isinstance(permanent_session_lifetime, int):
        permanent_session_lifetime_ms = permanent_session_lifetime * 1000
    else:
        permanent_session_lifetime_ms = permanent_session_lifetime.seconds * 1000

    return {
        'PERMANENT_SESSION_LIFETIME_MS': permanent_session_lifetime_ms,
    }


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
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        programa_id = request.form['programa_id']

        new_user = Users(username=username, email=email, role=role, programa_id=programa_id)

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user.password_hash = hashed_password

        if role != 'Coordenador':
            new_user.programa_id = 0  

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
            return 'PDI alterado com sucesso!'
        else:
            return 'PDI não encontrado'
    else:
        novo_pdi = PDI(nome=nome, datainicio=datainicio, datafim=datafim)
        db.session.add(novo_pdi)
        db.session.commit()
        return 'PDI cadastrado com sucesso!'

@app.route('/cadastro_pdi', methods=['GET', 'POST'])
def cadastro_pdi():
    if request.method == 'POST':
        return processar_formulario_pdi()
    
    return render_template('cadastropdi.html')

@app.route('/editar_pdi/<int:pdi_id>', methods=['GET', 'POST'])
def editar_pdi(pdi_id):
    success_message = None
    if request.method == 'POST':
        success_message = processar_formulario_pdi(pdi_id)
        pdi = PDI.query.get(pdi_id)
        return render_template('cadastropdi.html', pdi=pdi, success_message=success_message)
    
    pdi = PDI.query.get(pdi_id)
    return render_template('cadastropdi.html', pdi=pdi)

@app.route('/lista_pdis')
def lista_pdis():
    pdis = PDI.query.all()
    return render_template('editarpdi.html', pdis=pdis)

@app.route('/sucesso_cadastro')
def sucesso_cadastro():
    return 'Cadastro realizado com sucesso!'

######################Cadastro Objetivo ######################################
@app.route('/lista_objetivos')
def lista_objetivos():
    objetivos = Objetivo.query.options(joinedload(Objetivo.pdi)).all()
    return render_template('lista_objetivos.html', objetivos=objetivos)

@app.route('/cadastro_objetivo', methods=['GET', 'POST'])
def cadastro_objetivo():
    success_message = None
    if request.method == 'POST':
        success_message = processar_formulario_objetivo()
    
    lista_pdis = PDI.query.all()
    return render_template('cadastro_objetivo.html', lista_pdis=lista_pdis, objetivo=None, success_message=success_message)


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

    pdi_id = request.form['pdi_id']
    nome = request.form['nome']
    bsc = request.form['bsc']

    if objetivo_id:
        objetivo = Objetivo.query.get(objetivo_id)
        objetivo.pdi_id = pdi_id
        objetivo.nome = nome
        objetivo.bsc = bsc
        db.session.commit()
        return "Objetivo alterado com sucesso"
    else:
        novo_objetivo = Objetivo(pdi_id=pdi_id, nome=nome, bsc=bsc)
        db.session.add(novo_objetivo)
        db.session.commit()
        return "Objetivo cadastrado com sucesso"
##############################################################################################################################
###########################################################################################################################
@app.route('/cadastro_meta', methods=['GET', 'POST'])
def cadastro_meta():
    if request.method == 'POST':
        return processar_formulario_meta()

    # Se for método GET, obtém a lista de PDI do banco de dados
    lista_pdis = PDI.query.all()
    pdi_id = request.args.get('pdi_id')  # Obtém o ID do PDI selecionado
    if pdi_id:
        objetivos = buscar_objetivos_relacionados_pdi(int(pdi_id))
    else:
        # Se nenhum PDI foi selecionado, exibe uma lista vazia de objetivos
        objetivos = []

    # Renderiza a página com a lista de PDI e os objetivos relacionados
    return render_template('cadastro_meta.html', lista_pdis=lista_pdis, objetivos=objetivos)

def processar_formulario_meta():
    # Verifica se o usuário está logado e é um Pró-reitor
    if 'email' not in session:
        return 'Acesso não autorizado'

    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    objetivo_id = request.form['objetivo_id']
    nome = request.form['nome']
    porcentagem_execucao = request.form['porcentagem_execucao']

    # Insere os dados no banco de dados
    novo_meta = Meta(objetivo_id=objetivo_id, nome=nome, porcentagem_execucao=porcentagem_execucao)
    db.session.add(novo_meta)
    db.session.commit()

    return redirect(url_for('sucesso_cadastro'))

def buscar_objetivos_relacionados_pdi(pdi_id):
    # Busca os objetivos relacionados ao PDI
    objetivos = Objetivo.query.filter_by(pdi_id=pdi_id).all()
    return objetivos

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
#####################################################################3
@app.route('/alterar_meta', methods=['GET', 'POST'])
def alterar_meta():
    success_message = None
    if request.method == 'POST':
        meta_id = request.form.get('meta_id')
        if meta_id:
            success_message = processar_formulario_alterar_meta(meta_id)
    
    lista_pdis = PDI.query.all()
    pdi_id = request.args.get('pdi_id')
    objetivos = []
    meta = None
    
    if pdi_id:
        objetivos = buscar_objetivos_relacionados_pdi(int(pdi_id))
        
    objetivo_id = request.args.get('objetivo_id')
    if objetivo_id:
        meta = Meta.query.filter_by(objetivo_id=int(objetivo_id)).first()

    return render_template('alterarmetapdi.html', lista_pdis=lista_pdis, objetivos=objetivos, meta=meta, success_message=success_message)

def processar_formulario_alterar_meta(meta_id):
    if 'email' not in session:
        return 'Acesso não autorizado'

    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    meta = Meta.query.get(meta_id)
    if not meta:
        return 'Meta não encontrada', 404

    objetivo_id = request.form['objetivo_id']
    nome = request.form['nome']
    porcentagem_execucao = request.form['porcentagem_execucao']

    meta.objetivo_id = objetivo_id
    meta.nome = nome
    meta.porcentagem_execucao = porcentagem_execucao
    db.session.commit()

    return "Meta alterada com sucesso"


#################################33333

@app.route('/selecionar_pdi_para_alteracao', methods=['GET'])
def selecionar_pdi_para_alteracao():
    # Obtém a lista de PDI do banco de dados
    lista_pdis = PDI.query.all()
    return render_template('selecionarpdimeta.html', lista_pdis=lista_pdis)

@app.route('/escolher_objetivo_para_alteracao', methods=['GET'])
def escolher_objetivo_para_alteracao():
    pdi_id = request.args.get('pdi_id')
    if not pdi_id:
        return redirect(url_for('selecionar_pdi_para_alteracao'))

    # Busca os objetivos relacionados ao PDI
    objetivos = buscar_objetivos_relacionados_pdi(int(pdi_id))
    return render_template('escolher_objetivo_para_alteracao.html', pdi_id=pdi_id, objetivos=objetivos)

    
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
@app.route('/associar_objetivospe', methods=['POST', 'GET'])
def associar_objetivospe():
    if 'email' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login_page'))

    # Verifica se o usuário é um coordenador e se o programa_id corresponde ao programa do usuário logado
    if not current_user.is_authenticated or current_user.role != 'Coordenador':
        return 'Acesso não autorizado'
    
    # Verifica se o programa_id do coordenador está na sessão
    if 'programa_id' not in session:
        flash('Você precisa estar associado a um programa para acessar esta página.', 'danger')
        return redirect(url_for('get_coordenador'))

    # Recupera o programa_id do coordenador da sessão
    programa_id = session['programa_id']

    if request.method == 'POST':
        nome = request.form['nome']
        objetivo_pdi_id = request.form['objetivo_id']   
        planejamento_estrategico_id = request.form['planejamento_id']

        # Verifica se o programa_id corresponde ao programa do coordenador logado
        if planejamento_estrategico_id != programa_id:
            return 'Acesso não autorizado'

        # Recupera os objetivos associados ao programa do coordenador logado
        objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=programa_id).all()

        # Cria uma nova meta e a adiciona ao banco de dados
        novo_objetivo = ObjetivoPE(
             nome=nome, objetivo_id=objetivo_pdi_id, planejamento_estrategico_id=planejamento_estrategico_id)
        
        db.session.add(novo_objetivo)
        db.session.commit()

        flash('Objetivo cadastrado com sucesso!', 'success')
        return redirect(url_for('get_coordenador'))
    else:
        # Se o método não for POST, apenas renderiza o formulário HTML com os objetivos associados ao programa do coordenador logado
        objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=programa_id).all()

        return render_template('objetivope.html', objetivos=objetivos)
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


##################################################################################33
#######################################################
@app.route('/dbtest')
def dbtest():
    try:
        result = db.session.execute(db.text('SELECT 1')).scalar()
        return 'Database connection successful!'
    except Exception as e:
        logger.error(f'Database connection failed: {e}')
        return f'Database connection failed: {e}'
    
@app.route('/test')
def test_route():
    return "Test route is working!"

@app.route('/check')
def check_route():
    return "Check route is working!"

logger.info('Flask app created')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)