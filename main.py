from flask import Flask,jsonify, request, render_template, redirect, url_for,session
from sqlalchemy import select
from routes.models import Ensino, Engajamento, Transfconhecimento, Pesquisar, Orientacao, PDI, Meta, Objetivo, Indicador, Producaointelectual, Users, Programas
from routes.multidimensional import multidimensional_route
from routes.pdiprppg import pdi_route
from routes.producao import producao_route
from routes.indicador import indicador_route
from routes.login import login_route
from routes.planejamento import planejamento_route
from routes.db import db
from routes.PDICadastroForm import Objetivo,Meta,Indicador  # Altere o nome do arquivo conforme necessário
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
import logging

#logging.basicConfig(filename='app.log', level=logging.INFO)  # Isso criará um arquivo 'app.log' na mesma pasta do seu arquivo main.py


app = Flask(__name__)
app.secret_key = "super secret key"
bcrypt = Bcrypt(app)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/DB_PRPPG'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialize o objeto db com o aplicativo Flask
db.init_app(app)

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
       programas =  db.session.query(Programas).all()
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
    programa = db.session.query(Programas).all()
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
def processar_formulario_objetivo():
    # Verifica se o usuário está logado e é um Pró-reitor
    if 'email' not in session:
        return 'Acesso não autorizado'
    
    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    pdi_id=request.args.get('pdi_id'),
    nome=request.form['nome']
    bsc=request.form['bsc']       
     
  # Insere os dados no banco de dados
    novo_objetivo = Objetivo(pdi_id=pdi_id, nome=nome, bsc=bsc)
    db.session.add(novo_objetivo)
    db.session.commit
    
    return redirect(url_for('sucesso_cadastro'))

@app.route('/cadastro_objetivo', methods=['GET', 'POST'])
def cadastro_objetivo():
    if request.method == 'POST':
        return processar_formulario_objetivo()
    
    # Se for método GET, exibe o formulário de cadastro
    return render_template('cadastro_objetivo.html')

###############################################################################3
def processar_formulario_meta():
    # Verifica se o usuário está logado e é um Pró-reitor
    if 'email' not in session:
        return 'Acesso não autorizado'
    
    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
        return 'Acesso não autorizado'

    objetivo_id=request.args.get('objetivo_id'),
    nome=request.form['nome']
    porcentagem_execucao=request.form['porcentagem_execucao']       
     
  # Insere os dados no banco de dados
    novo_meta = Meta(objetivo_id=objetivo_id, nome=nome, porcentagem_execucao=porcentagem_execucao)
    db.session.add(novo_meta)
    db.session.commit

    return redirect(url_for('sucesso_cadastro'))

@app.route('/cadastro_meta', methods=['GET', 'POST'])
def cadastro_meta():
    if request.method == 'POST':
        return processar_formulario_meta()
    
    return render_template('cadastro_meta.html')

####################################################################################
def processar_formulario_indicador():
    if 'email' not in session:
            return 'Acesso não autorizado'
        
    user = Users.query.filter_by(email=session['email']).first()
    if user.role != 'Pro-reitor':
            return 'Acesso não autorizado'
    
    meta_id = request.args.get('meta_id'),
    nome = request.form['nome']

    novo_indicador = Indicador(meta_id=meta_id, nome=nome)
    db.session.add(novo_indicador)
    db.session.commit

    return redirect(url_for('sucesso_cadastro'))

@app.route('/cadastro_indicador', methods=['GET', 'POST'])
def cadastro_indicador():
   if request.method == 'POST':
           processar_formulario_indicador()

   return render_template('cadastro_indicador.html')
#############Cadastro de PDI ##################################
def processar_formulario_planejamento():
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

@app.route('/planejamento/', methods=['GET', 'POST'])
def cadastro_planejamento():
    if request.method == 'POST':
        return processar_formulario_planejamento()
    
    # Se for método GET, exibe o formulário de cadastro
    #return render_template('planejamento.html')

@app.route('/sucesso_Planejamento')
def sucesso_cad():
    return 'Cadastro realizado com sucesso!'

@app.route('/planejamento')
def kanban_board():
    # Exemplo de dados. Você pode substituir isso pelos seus próprios dados.
    tasks = {
        'To Do': ['Task 1', 'Task 2', 'Task 3'],
        'In Progress': ['Task 4'],
        'Done': ['Task 5', 'Task 6']
    }
    return render_template('planejamento.html', tasks=tasks)

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



if __name__ == '__main__':
    app.debug = True
    app.run()