from flask import Flask,jsonify, request, render_template, redirect, url_for,session,flash
from sqlalchemy import select
from routes.models import Ensino, Engajamento, Transfconhecimento, Pesquisar, Orientacao, PDI, Meta, Objetivo, Indicador, Producaointelectual, Users, Programa,BSC
from routes.models import MetaPE,IndicadorPE,AcaoPE,ObjetivoPE,PlanejamentoEstrategico
from routes.multidimensional import multidimensional_route
from routes.pdiprppg import pdi_route
from routes.producao import producao_route
from routes.indicador import indicador_route
from routes.login import login_route
from routes.planejamento import planejamento_route
from routes.db import db
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
import logging
from wtforms.validators import DataRequired
from flask_login import login_required
from flask_login import current_user
from flask_login import UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "super secret key"
bcrypt = Bcrypt(app)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/DB_PRPPG'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Inicialize o objeto db com o aplicativo 
db.init_app(app)

# Inicialize o objeto Bcrypt
bcrypt.init_app(app)

# Inicialize o objeto LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

app.register_blueprint(login_route)
app.register_blueprint(multidimensional_route)
app.register_blueprint(pdi_route)
app.register_blueprint(producao_route)
app.register_blueprint(indicador_route)
app.register_blueprint(planejamento_route)
##########################################################################################33
@app.route('/')
def index():
    return redirect('/login')

@app.route('/login')
def get_login():
    try:
       login =  db.session.query(Users).all()
       users = [{'id':row.id,'username': row.username,'email': row.email,
        'password': row.password,'role': row.role,'programa_id':row.programa_id } for row in login.execute()]
    except Exception as e:
        print(e)
        db.session.rollback()
        return "Erro ao buscar dados do Login"    
    
    return render_template('login.html',users=users)
############################################################################################################
@app.route('/coordenador')
def get_coordenador():
    return render_template('indexcord.html')

@app.route('/proreitor')
def get_proreitor():
    return render_template('indexpro.html')

@app.route('/home')
def get_index():
    return render_template('index.html')
   
######################################################################################################################################
@app.route('/multidimensional')
def get_multidimensional_data():
    try:
        consulta_ensinoaprendiz1 = select([Ensino]).where(Ensino.c.areatematica == 'Ciência da Computação')
        resultados_ensinoaprendiz1 = [{'nome': row.nome, 'mestradotempocerto': row.mestradotempocerto, 
                                       'equilibriogenero': row.equilibriogenero, 'pessoalacaddoutorado': row.pessoalacaddoutorado,
                                       'contatoambientetrabalho': row.contatoambientetrabalho,'proporcao': row.proporcao,'mestratempocertoletra': row.mestratempocertoletra,
                                       'equilibriogeneroletra': row.equilibriogeneroletra, 'pessoalacademicoletra': row.pessoalacademicoletra,
                                       'contaambienteletra': row.contaambienteletra,'proporcaoletra': row.proporcaoletra,'codigo': row.codigo,'sigla': row.sigla,
                                       'pais': row.pais,'programa': row.programa,'areatematica': row.areatematica,'regiao': row.regiao} for row in consulta_ensinoaprendiz1.execute()]

        consulta_engajreg = select([Engajamento]).where(Engajamento.c.areatematica == 'Ciência da Computação')  
        resultados_engajreg = [{'nome': row.nome,'estagio': row.estagio,'publiconjuntareg': row.publiconjuntareg,
                                'rendasfontesreg': row.rendasfontesreg,'codigo':row.codigo,'nome':row.nome,'sigla':row.sigla,'pais':row.pais,
                                'programa': row.programa,'areatematica':row.areatematica,'estagioletra':row.estagioletra,
                                'publiconjuntaregletra':row.publiconjuntaregletra,'rendasfontesregletra':row.rendasfontesregletra,'regiao':row.regiao} for row in consulta_engajreg.execute()]

        consulta_transfconhecimento = select([Transfconhecimento]).where(Transfconhecimento.c.areatematica == 'Ciência da Computação')
        resultados_transfconhecimento = [{'nome':row.nome,'rendafonteprivada':row.rendafonteprivada,'copublicparcind': row.copublicparcind,
                                          'publcitadaspatentes':row.publcitadaspatentes,'codigo':row.codigo,'sigla':row.sigla,'pais':row.pais,'programa':row.programa,
                                          'areatematica':row.areatematica,'rendaletra':row.rendaletra,' copubletra':row. copubletra,'publicitadasletra':row.publicitadasletra,
                                          'regiao':row.regiao} for row in consulta_transfconhecimento.execute()]

        consulta_pesquisar = select([Pesquisar]).where(Pesquisar.c.areatematica== 'Ciência da Computação')
        resultados_pesquisar = [{'nome':row.nome,'receitapesquisaexterna':row.receitapesquisaexterna,'produtividadedoutorado': row.produtividadedoutorado,
                                 'publpesqabsoluto':row.publpesqabsoluto,'taxacitacao':row.taxacitacao,'publicacaomaicitada':row.publicacaomaicitada,
                                 'publicacaointerdisciplinar': row.publicacaointerdisciplinar,'publicacaoacessoaberto': row.publicacaoacessoaberto,'orientacaoopesqensino':row.orientacaoopesqensino,
                                 'autoras': row.autoras,'codigo': row.codigo,'sigla':row.sigla,'pais': row.pais,'programa':row.programa,'areatematica':row.areatematica,
                                 'receitapesquisaexternaletra': row.receitapesquisaexternaletra,'produtividadedoutoradoletra': row.produtividadedoutoradoletra,'publpesqabsolutoletra':row.publpesqabsolutoletra,'taxacitacaoletra': row.taxacitacaoletra,
                                 'publicacaomaicitadaletra':row.publicacaomaicitadaletra,'publicacaointerdisciplinarletra':row.publicacaointerdisciplinarletra,
                                 'publicacaoacessoabertoletra':row.publicacaoacessoabertoletra,'orientacaoopesqensinoletra':row.orientacaoopesqensinoletra,
                                 'autorasletra':row.autorasletra,'regiao':row.regiao} for row in consulta_pesquisar.execute()]

        consulta_orientacaointern = select([Orientacao]).where(Orientacao.c.areatematica == 'Ciência da Computação')
        resultados_orientacaointern = [{'nome': row.nome,'professortitular':row.professortitular,'alunosenvolvidosorient':row.alunosenvolvidosorient,
                                         'prodoutcomorient':row.prodoutcomorient,'publicacoescoautoriaorient':row.publicacoescoautoriaorient,
                                         'publicpubcteorient':row.publicpubcteorient,'prodoutcomorientletra':row.prodoutcomorientletra,
                                         'publicacoescoautoriaorientletra':row.publicacoescoautoriaorientletra,
                                         'publicpubcteorientletra':row.publicpubcteorientletra,'codigo':row.codigo,'sigla':row.sigla,'pais':row.pais,'programa':row.programa,
                                         'areatematica':row.areatematica,'professortitularletra':row.professortitularletra,
                                         'regiao':row.regiao} for row in consulta_orientacaointern.execute()]

        return render_template('multidimensional.html', ensino=resultados_ensinoaprendiz1, engajamento=resultados_engajreg,
                                transfconhecimento=resultados_transfconhecimento, pesquisar=resultados_pesquisar,
                                orientacao=resultados_orientacaointern)
    
    except Exception as e:
        print(e)
        db.session.rollback()
        return "Erro ao buscar dados multidimensionais"

#####################################################################################################################################
@app.route('/producao')
def get_producao():
    try:
       producao = select([Producaointelectual]).where(Producaointelectual.codigoprograma =='32003013008P4')
       resutado = [{'titulo':row.titulo,'autor': row.autor,'categoria': row.categoria,
        'tipoproducao': row.tipoproducao,'subtipo': row.subtipo,'areaconcentracao': row.areaconcentracao, 
        'linhapesquisa': row.linhapesquisa,'projetopesquisa': row.projetopesquisa,'anaopublicacao':row.anaopublicacao } for row in producao.execute()]
    except Exception as e:
        print(e)
        db.session.rollback()
        return "Erro ao buscar dados de Produção Intelectaul"    
    
    return render_template('producao.html',producao=resutado)
##########################################################################################################################################

@app.route('/programas')
def get_programas():
    try:
       programas =  db.session.query(Programa).all()
       resultados = [{'id':row.id,'codigo': row.codigo,'nome': row.nome} for row in programas.execute()]
       return jsonify(resultados)

    except Exception as e:
        print(e)
        db.session.rollback()

    return "Erro ao buscar dados de Programas"    
   
############################################################## PDI ##############################################
app.route('/pdi')
def get_indicador():
   try:
       pdi = db.session.query(PDI).all()
       resultados_pdi = [{'id':row.id,'nome': row.nome,'datainicio': row.datainicio,'datafim': row.datafim,} for row in pdi.execute()]
       return jsonify(resultados_pdi)
   except Exception as e:
        print(e)
        db.session.rollback()

   return "Erro ao buscar dados do PDI"  
##############################
app.route('/objetivo')
def get_objetivo():
   try:
       objetivo = db.session.query(Objetivo).all()
       resultados_objetivo = [{'id':row.id,'pdi_id': row.pdi_id,'nome': row.nome,'bsc':row.bsc} for row in objetivo.execute()]
       return jsonify(resultados_objetivo) 
   except Exception as e:
        print(e)
        db.session.rollback()

   return "Erro ao buscar dados de Objetivo"
####################################
app.route('/meta')
def get_meta():
   try:
       meta = db.session.query(Meta).all()
       resultados_meta = [{'id':row.id,'objetivo_id': row.objetivo_id,'nome': row.nome,'porcentagem_execucao':row.porcentagem_execucao} for row in meta.execute()]
       return jsonify(resultados_meta)
   except Exception as e:
        print(e)
        db.session.rollback()

   return "Erro ao buscar dados de Meta"    

######################################################################################################################
@app.route('/login/register')
def get_register():
    try:
       
       login =  db.session.query(Users).all()
       users = [{'id':row.id,'username': row.username,'email': row.email,
       'password': row.password,'role': row.role,'programa_id':row.programa_id } for row in login]    
       
    except Exception as e:
        print(e)
        db.session.rollback()
        return "Erro ao buscar dados do usuário"      
    
    return render_template('register.html',users=users)

def register_page():
    programa = db.session.query(Programa).all()
    programas =[{'id':row.id,'codigo': row.codigo,'nome': row.nome} for row in programa] 
    
    return render_template('register.html', programas=programas)

#############Cadastro de PDI ##################################
def processar_formulario_pdi():
    # Verifica se o usuário está logado e é um Pró-reitor
    if 'email' not in session:
        return 'Acesso não autorizado'
    
    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    # Processa os dados do formulário
    nome = request.form['nome']
    datainicio = request.form['datainicio']
    datafim = request.form['datafim']
    
    # Insere os dados no banco de dados
    novo_pdi = PDI(nome=nome, datainicio=datainicio, datafim=datafim)
    db.session.add(novo_pdi)
    db.session.commit()
    
    return redirect(url_for('sucesso_cadastro'))
######################################################################################
@app.route('/cadastro_pdi', methods=['GET', 'POST'])
def cadastro_pdi():
    if request.method == 'POST':
        return processar_formulario_pdi()
    
    # Se for método GET, exibe o formulário de cadastro
    return render_template('cadastropdi.html')

@app.route('/sucesso_cadastro')
def sucesso_cadastro():
    return 'Cadastro realizado com sucesso!'

######################Cadastro Objetivo ######################################
@app.route('/cadastro_objetivo', methods=['GET', 'POST'])
def cadastro_objetivo():
    if request.method == 'POST':
        return processar_formulario_objetivo()
    
    # Se for método GET, obtém a lista de PDI do banco de dados
    lista_pdis = PDI.query.all()
    
    # Exibe o formulário de cadastro com a lista de PDI
    return render_template('cadastro_objetivo.html', lista_pdis=lista_pdis)

def processar_formulario_objetivo():
    # Verifica se o usuário está logado e é um Pró-reitor
    if 'email' not in session:
        return 'Acesso não autorizado'
    
    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    pdi_id = request.form['pdi_id']
    nome = request.form['nome']
    bsc = request.form['bsc']       
     
    # Insere os dados no banco de dados
    novo_objetivo = Objetivo(pdi_id=pdi_id, nome=nome, bsc=bsc)
    db.session.add(novo_objetivo)
    db.session.commit()
    
    return redirect(url_for('sucesso_cadastro'))
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

    # Verifica se a lista de objetivos está sendo passada corretamente para o template
    print("Lista de Objetivos:", objetivos)

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

################################################################################################################################
######################################################################
@app.route('/cadastro_indicador', methods=['GET', 'POST'])
def cadastro_indicador():
    if request.method == 'POST':
        return processar_formulario_indicador()

    # Busca todos os PDIs
    pdis = PDI.query.all()

    # Filtra os objetivos relacionados aos PDIs
    objetivos = Objetivo.query.filter(Objetivo.pdi_id.in_([pdi.id for pdi in pdis])).all()

    # Filtra as metas relacionadas aos objetivos
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()

    # Filtra os indicadores relacionados às metas
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()

    return render_template('cadastro_indicador.html', pdis=pdis, objetivos=objetivos, metas=metas, indicadores=indicadores)

def processar_formulario_indicador():
    if 'email' not in session:
        return 'Acesso não autorizado'

    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    indicador_id = request.form['indicador_id']
    meta_pdi_id = request.form['meta_pdi_id']
    nome = request.form['nome']

    novo_indicador = Indicador(meta_pdi_id=meta_pdi_id, indicador_id=indicador_id, nome=nome)
    db.session.add(novo_indicador)
    db.session.commit()

    return redirect(url_for('sucesso_cadastro'))

###############################################################
@app.route('/PDI')
def page_pdi():
    return render_template('pdi.html')

@app.route('/visualizacao')
def visualizacao():
     return render_template('bsc.html')

@app.route('/register')
def register():
  return render_template('register.html')

@app.route('/logout')
def logout():
    logging.info('Rota de logout acessada')  # Registra quando a rota é acessada
    session.pop('email', None)  # Remove a chave de e-mail da sessão
    logging.info('Chave de sessão removida')  # Registra quando a chave de sessão é removida
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
        print("Ocorreu um erro ao cadastrar o planejamento:", e)
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
    # Esta rota só será acessível para usuários autenticados
    return 'Esta rota é protegida!'
##################################################################################################################################
@app.route('/associar_objetivospe', methods=['POST'])
def associar_objetivospe():
    if 'email' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        objetivo_pdi_id= request.form['objetivo_id']   
        planejamento_estrategico_id = request.form['planejamento_id']

        # Verifica se o programa_id está na sessão
        if 'programa_id' not in session:
            flash('Nenhum programa do usuário encontrado. Faça login novamente.', 'danger')
            return redirect(url_for('login.login_page'))

        # Cria uma nova meta e a adiciona ao banco de dados
        novo_objetivo = ObjetivoPE(
             nome=nome, objetivo_id=objetivo_pdi_id, planejamento_estrategico_id=planejamento_estrategico_id)
        
        db.session.add(novo_objetivo)
        db.session.commit()

        flash('Objetivo cadastrado com sucesso!', 'success')
        return redirect(url_for('get_coordenador'))
    else:
        # Se o método não for POST, apenas renderiza o formulário HTML
        planejamento_estrategico = PlanejamentoEstrategico.query.all()
        objetivos_por_planejamento = []

        for pe in planejamento_estrategico:
            objetivos = ObjetivoPE.query.filter_by(pdi_id=pe.pdi_id).all()
            objetivos_por_planejamento.append((pe, objetivos))

        # Renderiza o formulário HTML com os objetivos associados a cada planejamento estratégico
        return render_template('objetivope.html', objetivos_por_planejamento=objetivos_por_planejamento)
##################################################################################################################################
###############################################################################################################################
@app.route('/associar_metaspe', methods=['POST'])
def associar_metaspe():
    if request.method == 'POST':
        # Aqui vai o código para lidar com o formulário submetido
        nome = request.form['nome']
        objetivope_id = request.form['objetivope_id']
        porcentagem_execucao = request.form['porcentagem_execucao']
        
        # Verifica se o objetivo existe
        objetivo_pe = ObjetivoPE.query.get(objetivope_id)
        if objetivo_pe is None:
            flash('Objetivo PE não encontrado!', 'error')
            return redirect(url_for('get_coordenador'))
        
        # Cria uma nova meta PE e a associa ao objetivo PE
        nova_meta = MetaPE(
            nome=nome,
            objetivope_id=objetivope_id,
            porcentagem_execucao=porcentagem_execucao
        )

        db.session.add(nova_meta)
        db.session.commit()

        flash('Meta cadastrada com sucesso!', 'success')
        return redirect(url_for('get_coordenador'))
    else:
        # Se o método não for POST, obtenha os dados necessários para o formulário
        objetivos_pe = ObjetivoPE.query.all()
        
        # Renderiza o formulário HTML com os dados obtidos
        return render_template('metaspe.html', objetivos_pe=objetivos_pe)

########################################################################################################
if __name__ == '__main__':
    app.run(debug=True)