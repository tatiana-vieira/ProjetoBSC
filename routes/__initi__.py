# Importe os módulos necessários
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

class CadastroPDIForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    datainicio = IntegerField('Data de Início', validators=[DataRequired()])
    datafim = IntegerField('Data de Fim', validators=[DataRequired()])