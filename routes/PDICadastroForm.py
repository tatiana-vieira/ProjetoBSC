from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField,DecimalField
from wtforms.validators import DataRequired

class PDICadastroForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    datainicio = IntegerField('Data de Início', validators=[DataRequired()])
    datafim = IntegerField('Data de Fim', validators=[DataRequired()])

class Objetivo(FlaskForm):
    pdi_id = IntegerField(' pdi_id', validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])
    bsc = StringField('BSC', validators=[DataRequired()])

class Meta(FlaskForm):
    objetivo_id = IntegerField('Id do Objetivo', validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()]) 
    porcentagem_execucao = DecimalField('Porcentagem de Execução', validators=[DataRequired()])
   
class Indicador(FlaskForm):
    
    meta_pdi_id = DecimalField('Id da Meta', validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()]) 