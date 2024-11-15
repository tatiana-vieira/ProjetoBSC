from routes.db import db  # Importe o objeto db do arquivo db.py
from sqlalchemy.ext.declarative import declarative_base  # Importe a base declarativa do SQLAlchemy
from sqlalchemy import Column, String, Numeric
from routes.db import db  # Importe o objeto db do arquivo db.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from passlib.hash import scrypt
from bcrypt import gensalt
from flask_login import UserMixin, LoginManager
from datetime import datetime  # Correção



login_manager = LoginManager()

# Crie a base declarativa
Base = declarative_base()
bcrypt = Bcrypt()


class Discente(db.Model):
    __tablename__ = 'discente'
    nome = db.Column(db.String(250), primary_key=True)
    sexo = db.Column(db.String(30))
    nacionalidade = db.Column(db.String(60))
    email = db.Column(db.String(150))
    nivel = db.Column(db.String(25))
    curso = db.Column(db.String(150))
    anomatricula = db.Column(db.Integer, nullable=False) 
    situacao = db.Column(db.String(150))
    anosituacao = db.Column(db.Integer, nullable=False) 
    datasituacao = db.Column(db.String(20))
    autorcomplembolsa = db.Column(db.String(8))
    orientador= db.Column(db.String(150))
    periodoorientacao= db.Column(db.String(35))
    principal= db.Column(db.String(8))
    tipobolsa = db.Column(db.String(180))
    financiador = db.Column(db.String(200))
    programafomento = db.Column(db.String(200))
    ies = db.Column(db.String(200))
    nivelbolsa = db.Column(db.String(200))
    anocoleta = db.Column(db.String(10))
    codigoprograma = db.Column(db.String(30))
    datamatricula = db.Column(db.String(25))

class Docente(db.Model):
    __tablename__ = 'docente'
    nome = db.Column(db.String(100), primary_key=True)
    nacionalidade = db.Column(db.String(90))
    email = db.Column(db.String(200))
    nivel = db.Column(db.String(50))
    anotitulacao = db.Column(db.String(20))
    areconhecimento = db.Column(db.String(80))
    paisinstituicao = db.Column(db.String(50))
    instituicao = db.Column(db.String(250))
    categoria = db.Column(db.String(10))
    cargahoraria = db.Column(db.String(80))
    inicio = db.Column(db.String(50))
    fim = db.Column(db.String(50))
    mestradoacademico = db.Column(db.Integer)
    mestradoprofissional = db.Column(db.Integer)
    tutoria = db.Column(db.Integer)
    monografia = db.Column(db.Integer)
    iniciacaocinetifica = db.Column(db.Integer)
    disciplinagraducao = db.Column(db.Integer)
    cargahorariaanual  = db.Column(db.Integer)
    mestradoprofissional = db.Column(db.Integer)   
    motivoafastamento= db.Column(db.String(250))
    datainicioafast = db.Column(db.String(50))
    datafimafast = db.Column(db.String(50))
    instituicaoensinoafast= db.Column(db.String(250))
    anocoleta = db.Column(db.String(10))
    codigoprograma= db.Column(db.String(50))
    sexo = db.Column(db.String(50))
    regimetrabalho = db.Column(db.String(80))
    datanasc = db.Column(db.String(50))


class Engajamento(db.Model):
    __tablename__ = 'engajreg'
    nome = db.Column(db.String(200), primary_key=True)
    estagio = db.Column(db.Numeric(10, 2))
    publiconjuntareg = db.Column(db.Numeric(10, 2))
    rendasfontesreg = db.Column(db.Numeric(10, 2))
    codigo = db.Column(db.String(30))
    sigla = db.Column(db.String(20))
    pais = db.Column(db.String(150))
    programa = db.Column(db.String(250))
    areatematica = db.Column(db.String(450))
    estagioletra = db.Column(db.String(3))
    publiconjuntaregletra = db.Column(db.String(3))
    rendasfontesregletra = db.Column(db.String(3))
    regiao = db.Column(db.String(50))

class Ensino(db.Model):
    __tablename__ = 'ensinoaprendiz1'
    nome = db.Column(db.String(200), primary_key=True)
    mestradotempocerto = db.Column(db.Numeric(10, 2))
    equilibriogenero = db.Column(db.Numeric(10, 2))
    pessoalacaddoutorado = db.Column(db.Numeric(10, 2))
    contatoambientetrabalho = db.Column(db.Numeric(10, 2))
    proporcao = db.Column(db.Numeric(10, 2))
    mestratempocertoletra = db.Column(db.String(3))
    equilibriogeneroletra = db.Column(db.String(3))
    pessoalacademicoletra = db.Column(db.String(3))
    contaambienteletra = db.Column(db.String(3))
    proporcaoletra = db.Column(db.String(3))
    codigo = db.Column(db.String(30))
    sigla = db.Column(db.String(20))
    pais = db.Column(db.String(150))
    programa = db.Column(db.String(150))
    areatematica = db.Column(db.String(450))
    regiao = db.Column(db.String(50))

class Orientacao(db.Model):
    __tablename__ = 'orientacaointern'
    nome = db.Column(db.String(200), primary_key=True)
    orientacaointernmestrado = db.Column(db.Numeric(10, 2))
    oportunidadeestudarexterior = db.Column(db.Numeric(10, 2))
    doutaradointer = db.Column(db.Numeric(10, 2))
    publconjintern = db.Column(db.Numeric(10, 2))
    bolsapesquisaintern = db.Column(db.Numeric(10, 2))
    codigo = db.Column(db.String(30))
    sigla = db.Column(db.String(30))
    pais = db.Column(db.String(150))
    programa = db.Column(db.String(250))
    areatematica = db.Column(db.String(450))
    oportuniestexteletra = db.Column(db.String(3))
    coutinterletra = db.Column(db.String(3))
    publconinterletra = db.Column(db.String(3))
    bolsapesletra = db.Column(db.String(3))
    orientacaointernmestradoletra = db.Column(db.String(3))
    regiao = db.Column(db.String(50))

class Transfconhecimento(db.Model):
    __tablename__ = 'transfconhecimento'
    nome = db.Column(db.String(200), primary_key=True)
    rendafonteprivada = db.Column(db.Numeric(10, 2))
    copublicparcind = db.Column(db.Numeric(10, 2))
    publcitadaspatentes = db.Column(db.Numeric(10, 2))
    codigo = db.Column(db.String(30))
    sigla = db.Column(db.String(20))
    pais = db.Column(db.String(150))
    programa = db.Column(db.String(250))
    areatematica = db.Column(db.String(450))
    rendaletra = db.Column(db.String(3))
    copubletra = db.Column(db.String(3))
    publicitadasletra = db.Column(db.String(3))
    regiao = db.Column(db.String(50))

class Pesquisar(db.Model):
    __tablename__ = 'pesquisar'
    nome = db.Column(db.String(200), primary_key=True)
    receitapesquisaexterna = db.Column(db.Numeric(10, 2))
    produtividadedoutorado = db.Column(db.Numeric(10, 2))
    taxacitacao = db.Column(db.Numeric(10, 2))
    publicacaomaicitada = db.Column(db.Numeric(10, 2))
    publicacaointerdisciplinar = db.Column(db.Numeric(10, 2))
    publicacaoacessoaberto = db.Column(db.Numeric(10, 2))
    orientacaoopesqensino = db.Column(db.Numeric(10, 2))
    autoras = db.Column(db.Numeric(10, 2))
    codigo = db.Column(db.String(30))
    sigla = db.Column(db.String(20))
    pais = db.Column(db.String(150))
    programa = db.Column(db.String(250))
    areatematica = db.Column(db.String(450))
    regiao = db.Column(db.String(50))
    publpesqabsoluto = db.Column(db.Numeric(10, 2))
    receitapesquisaexternaletra = db.Column(db.String(3))
    produtividadedoutoradoletra = db.Column(db.String(3))
    publpesqabsolutoletra = db.Column(db.String(3))
    taxacitacaoletra = db.Column(db.String(3))
    publicacaomaicitadaletra = db.Column(db.String(3))
    publicacaointerdisciplinarletra = db.Column(db.String(3))
    publicacaoacessoabertoletra = db.Column(db.String(3))
    orientacaoopesqensinoletra = db.Column(db.String(3))
    autorasletra = db.Column(db.String(3))   

class Eixomultidimensional(db.Model):
    __tablename__ = 'eixomultidimensional'
    codigoeixo = db.Column(db.Integer, primary_key=True)
    nome_eixo = db.Column(db.String(200))

class BSC(db.Model):
    __tablename__ = 'bsc'
    codigo = db.Column(db.Integer, primary_key=True)
    nome= db.Column(db.String(150))

class Producaointelectual(db.Model):
    __tablename__ = 'producaointelectual'
    codigoprograma = db.Column(db.String(50), primary_key=True)
    sigla = db.Column(db.String(15))
    instituicaoensino= db.Column(db.String(350))
    nomeprograma= db.Column(db.String(500))
    anaopublicacao = db.Column(db.Integer)
    titulo= db.Column(db.String(550))
    producaoglosada= db.Column(db.String(20))
    ordem= db.Column(db.String(15))
    autor= db.Column(db.String(150))
    categoria= db.Column(db.String(150))
    tipoproducao= db.Column(db.String(250))
    subtipo= db.Column(db.String(250))
    nomedetalhamento= db.Column(db.String(250))
    valordetalhamento= db.Column(db.String(850))
    areaconcentracao= db.Column(db.String(550))
    linhapesquisa= db.Column(db.String(550))
    projetopesquisa= db.Column(db.String(850))
    prodvinculadaconclusao= db.Column(db.String(35))
############################################################################33
class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    programa_id = db.Column(db.Integer, db.ForeignKey('programas.id'))

    programa = db.relationship('Programa', backref='users')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


    def set_password(self, password):
        # Gere o hash da senha usando Flask-Bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

     
    # Adicione esses métodos para Flask-Login
    def is_active(self):
        return True
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
########################################################################
class Token(db.Model):
    __tablename__ = 'token'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    expired_at = db.Column(db.DateTime, nullable=False)

    # Relacionamento com a tabela Users
    user = db.relationship("Users", backref="tokens")

    def __repr__(self):
        return f"<Token(id={self.id}, user_id={self.user_id}, token='{self.token[:10]}...', expired_at={self.expired_at})>"

##############################################################################33

class Programa(db.Model):
    __tablename__ = 'programas'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(255), nullable=False)

    # Relacionamento com ResultadosAutoavaliacao
    resultados = db.relationship(
        "ResultadosAutoavaliacao",
        back_populates="programa",
        cascade="all, delete-orphan"
    )

    # Relacionamento com PlanejamentoEstrategico
    planejamentos = db.relationship(
        "PlanejamentoEstrategico",
        back_populates="programa",
        cascade="all, delete-orphan"
    )

class ResultadosAutoavaliacao(db.Model):
    __tablename__ = 'resultados_autoavaliacao'
    id = db.Column(db.Integer, primary_key=True)
    tipo_analise = db.Column(db.String(50), nullable=False)
    graficos = db.Column(db.Text)
    recomendacoes = db.Column(db.Text)
    data_geracao = db.Column(db.TIMESTAMP, default=db.func.now())
    usuario_gerador = db.Column(db.Integer)
    id_programa = db.Column(db.Integer, db.ForeignKey('programas.id'))

    programa = db.relationship("Programa", back_populates="resultados")


class PlanejamentoEstrategico(db.Model):
    __tablename__ = 'planejamento_estrategico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(250), nullable=False)
    pdi_id = db.Column(db.Integer, db.ForeignKey('pdi.id'))
    id_programa = db.Column(db.Integer, db.ForeignKey('programas.id'))

    programa = db.relationship("Programa", back_populates="planejamentos")
    pdi = db.relationship('PDI', back_populates='planejamentos')
    objetivos_pe = db.relationship('ObjetivoPE', back_populates='planejamento_estrategico')

class Risco(db.Model):
    __tablename__ = 'risco'

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)
    objetivo_pe_id = db.Column(db.Integer, db.ForeignKey('objetivo_pe.id'))
    meta_pe_id = db.Column(db.Integer, db.ForeignKey('meta_pe.id'))
    probabilidade = db.Column(db.String(50))  # Campo probabilidade
    impacto = db.Column(db.String(50))        # Campo impacto
    acao_preventiva = db.Column(db.String(255))  # Campo acao_preventiva adicionado
    
    objetivo_pe = db.relationship('ObjetivoPE', backref='riscos')
    meta_pe = db.relationship('MetaPE', backref='riscos')

class CadeiaValor(db.Model):
    __tablename__ = 'cadeiavalor'
    id = db.Column(db.Integer, primary_key=True)
    macroprocessogerencial = db.Column(db.String(200))
    macroprocessofinalistico =db.Column(db.String(200))
    valorpublico =db.Column(db.String(200))
    macroprocessosuporte =db.Column(db.String(200))
    planejamento_estrategico_id = db.Column(db.Integer, db.ForeignKey('planejamento_estrategico.id'))
 
################################################## PDI###################################################################################3
class Indicador(db.Model):
    __tablename__ = 'indicador'
    id = db.Column(db.Integer, primary_key=True)
    meta_pdi_id = db.Column(db.Numeric(4, 2), db.ForeignKey('meta_pdi.id'), nullable=False)
    nome = db.Column(db.String(2500), nullable=False)
    valor_atual = db.Column(db.Float, nullable=True)
    valor_esperado = db.Column(db.Float, nullable=True)
    meta = db.relationship('Meta', back_populates='indicadores')

class PDI(db.Model):
    __tablename__ = 'pdi'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    datainicio = db.Column(db.Integer)
    datafim = db.Column(db.Integer)
    
    objetivos = db.relationship('Objetivo', back_populates='pdi')
    planejamentos = db.relationship('PlanejamentoEstrategico', back_populates='pdi')

class Meta(db.Model):
    __tablename__ = 'meta_pdi'
    id = db.Column(db.Numeric(4, 2), primary_key=True)
    objetivo_id = db.Column(db.Integer, db.ForeignKey('objetivo_pdi.id'), nullable=False)
    nome = db.Column(db.String(2500), nullable=False)
    porcentagem_execucao = db.Column(db.Numeric(4, 2), nullable=False)
    data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    objetivo = db.relationship('Objetivo', back_populates='metas')
    indicadores = db.relationship('Indicador', back_populates='meta')
#####################################################################################3
class Objetivo(db.Model):
    __tablename__ = 'objetivo_pdi'
    id = db.Column(db.Integer, primary_key=True)
    pdi_id = db.Column(db.Integer, db.ForeignKey('pdi.id'), nullable=False)
    nome = db.Column(db.String(2500), nullable=False)
    bsc = db.Column(db.String(100), nullable=False)
    
    pdi = db.relationship('PDI', back_populates='objetivos')
    metas = db.relationship('Meta', back_populates='objetivo')
    objetivos_pe = db.relationship('ObjetivoPE', back_populates='objetivo_pdi')

class ObjetivoPE(db.Model):
    __tablename__ = 'objetivo_pe'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(250), nullable=False)
    planejamento_estrategico_id = db.Column(db.Integer, db.ForeignKey('planejamento_estrategico.id'))
    objetivo_pdi_id = db.Column(db.Integer, db.ForeignKey('objetivo_pdi.id'))
    
    planejamento_estrategico = db.relationship('PlanejamentoEstrategico', back_populates='objetivos_pe')
    objetivo_pdi = db.relationship('Objetivo', back_populates='objetivos_pe')

    # Relacionamento com MetaPE usando back_populates
    metas = db.relationship('MetaPE', back_populates='objetivo_pe')

class MetaPE(db.Model):
    __tablename__ = 'meta_pe'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(250), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    responsavel = db.Column(db.String(255), nullable=True)
    recursos_necessarios = db.Column(db.Text, nullable=True)
    data_inicio = db.Column(db.Date, nullable=True)
    data_termino = db.Column(db.Date, nullable=True)
    status_inicial = db.Column(db.Numeric(5, 2), nullable=True)
    status = db.Column(db.String(50))
    valor_alvo = db.Column(db.Numeric(5, 2), nullable=True)
    objetivo_pe_id = db.Column(db.Integer, db.ForeignKey('objetivo_pe.id'), nullable=False)

    # Relacionamento com ObjetivoPE usando back_populates
    objetivo_pe = db.relationship('ObjetivoPE', back_populates='metas')


class Valormeta(db.Model):
    __tablename__ = 'valormeta'
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Numeric(10, 2))
    ano = db.Column(db.Integer, nullable=False)
    semestre = db.Column(db.Integer, nullable=False)
    metape_id = db.Column(db.Integer, db.ForeignKey('meta_pe.id'))
    meta_pe = db.relationship('MetaPE', backref='valores_metas')

class IndicadorPlan(db.Model):
    __tablename__ = 'indicador_pe'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(250), nullable=False)
    descricao = db.Column(db.String(550), nullable=False)
    meta_pe_id = db.Column(db.Integer, db.ForeignKey('meta_pe.id'))
    frequencia_coleta = db.Column(db.String(50), nullable=False)
    valor_meta = db.Column(db.Float, nullable=False)
    peso = db.Column(db.Float, nullable=False, default=1.0)
    data_inicio = db.Column(db.Date, nullable=True)  # Campo para Data de Início
    data_fim = db.Column(db.Date, nullable=True)  # Campo para Data de Fim
    responsavel = db.Column(db.String(255), nullable=False)  # Novo campo

    meta_pe = db.relationship('MetaPE', backref="indicador_pe")
    variaveis = db.relationship('VariavelPE', backref='indicador', lazy=True)
    historico_valores = db.relationship('HistoricoIndicador', backref='indicador', lazy=True)

class HistoricoIndicador(db.Model):
    __tablename__ = 'historico_indicador'
    id = db.Column(db.Integer, primary_key=True)
    indicador_pe_id = db.Column(db.Integer, db.ForeignKey('indicador_pe.id'))
    data = db.Column(db.Date, nullable=False)
    valor_progresso = db.Column(db.Float, nullable=False)



class VariavelPE(db.Model):
    __tablename__ = 'variavel_pe'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(250), nullable=False)
    indicador_pe_id = db.Column(db.Integer, db.ForeignKey('indicador_pe.id'))
  
class DadosAnuaisPE(db.Model):
  __tablename__ = 'dados_anuais_pe'
  id = db.Column(db.Integer, primary_key=True)
  ano = db.Column(db.Integer, nullable=False)
  valor = db.Column(db.Integer, nullable=False)
  variavel_pe_id = db.Column(db.Integer, db.ForeignKey('variavel_pe.id'))   

class SinalPE(db.Model):
    __tablename__ = 'sinal_pe'
    id = db.Column(db.Integer, primary_key=True)
    sinal = db.Column(db.String(10), nullable=False)
    indicador_pe_id = db.Column(db.Integer, db.ForeignKey('indicador_pe.id'))

    indicador = db.relationship('IndicadorPlan', backref='sinal_pe')

class Formula(db.Model):
    __tablename__ = 'formulas'
    id = db.Column(db.Integer, primary_key=True)
    indicador_id = db.Column(db.Integer, db.ForeignKey('indicador_pe.id'))
    expressao = db.Column(db.Text, nullable=False)
    
    indicador = db.relationship('IndicadorPlan', backref=db.backref('formulas', lazy=True))

class Valorindicador(db.Model):
    __tablename__ = 'valorindicador'
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Numeric(10, 2))
    ano= db.Column(db.Integer,nullable=False)
    semestre = db.Column(db.Integer,nullable=False)
    indicadorpe_id = db.Column(db.Integer, db.ForeignKey('indicador_pe.id'))  # Correção aqui

class AcaoPE(db.Model):
    __tablename__ = 'acao_pe'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(250), nullable=False)
    meta_pe_id = db.Column(db.Integer, db.ForeignKey('meta_pe.id'))
    porcentagem_execucao=db.Column(db.Float)
    data_inicio = db.Column(db.Date)
    data_termino = db.Column(db.Date)
    responsavel=db.Column(db.String(350))
    status = db.Column(db.String(350))
    observacao = db.Column(db.String(3500))

    meta_pe = db.relationship('MetaPE',backref="acao_pe")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Defina outros campos de usuário aqui...

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Avaliacao(db.Model):
    __tablename__ = 'avaliacoes'  # Defina o nome da tabela
    id = db.Column(db.Integer, primary_key=True)  # Correta indentação
    data_avaliacao = db.Column(db.DateTime, default=datetime.utcnow)  # Correta indentação
    qualidade_aulas = db.Column(db.Float, nullable=False)  # Correta indentação
    infraestrutura = db.Column(db.Float, nullable=False)  # Correta indentação
    sentimento_geral = db.Column(db.Float, nullable=True)  # Correta indentação