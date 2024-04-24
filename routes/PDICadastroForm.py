from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField
from wtforms.validators import DataRequired
from .models import PDI,Objetivo,Meta,Indicador


class PDICadastroForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    datainicio = IntegerField('Data de Início', validators=[DataRequired()])
    datafim = IntegerField('Data de Fim', validators=[DataRequired()])

class ObjetivoForm(FlaskForm):
    pdi_id = IntegerField('PDI ID', validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])
    bsc = StringField('BSC', validators=[DataRequired()])

class MetaForm(FlaskForm):
    objetivo_id = IntegerField('ID do Objetivo', validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()]) 
    porcentagem_execucao = DecimalField('Porcentagem de Execução', validators=[DataRequired()])
   
class IndicadorForm(FlaskForm):
    meta_pdi_id = IntegerField('ID da Meta', validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])