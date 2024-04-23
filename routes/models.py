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


# Crie a base declarativa
Base = declarative_base()
bcrypt = Bcrypt()


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
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    programa_id = db.Column(db.Integer, nullable=True)
    password_hash = db.Column(db.String(1500), nullable=False)

    def set_password(self, password):
        # Gere o hash da senha usando Flask-Bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        # Verifique se a senha fornecida corresponde à senha armazenada usando Flask-Bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)
########################################################################
class Token(Base):
  __tablename__ = 'token'

  id = Column(Integer, primary_key=True)
  user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
  token = Column(String(255), nullable=False)
  expired_at = Column(DateTime, nullable=False)

  user = relationship("Users", backref="tokens")  # Optional relationship for user access

  def __repr__(self):
    return f"<Token(id={self.id}, user_id={self.user_id}, token='{self.token[:10]}...', expired_at={self.expired_at})>"


##############################################################################33
class Programas(db.Model):
   __tablename__ = 'programas'
   id = db.Column(db.Integer, primary_key=True)  
   codigo = db.Column(db.String(50))
   nome = db.Column(db.String(255))
################################################## PDI###################################################################################3
class PDI(db.Model):
    __tablename__ = 'pdi'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(2500), nullable=False)  
    datainicio = db.Column(db.Integer, nullable=False) 
    datafim = db.Column(db.Integer, nullable=False) 

class Objetivo(db.Model):
    __tablename__ = 'objetivo_pdi'
    id = db.Column(db.Integer, primary_key=True)  # Aqui está a correção
    pdi_id = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(2500), nullable=False) 
    bsc = db.Column(db.String(100), nullable=False)  

class Meta(db.Model):
    __tablename__ = 'meta_pdi'
    id = db.Column(db.Numeric(4,2), primary_key=True)  # Aqui está a correção
    objetivo_id = db.Column(db.Integer)
    nome = db.Column(db.String(2500)) 
    porcentagem_execucao = db.Column(db.Numeric(4,2))    
   
class Indicador(db.Model):
    __tablename__ = 'indicador'
    id = db.Column(db.Integer, primary_key=True)
    meta_pdi_id = db.Column(db.Numeric, nullable=False)
    nome = db.Column(db.String(2500), nullable=False)
 
