from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
import pandas as pd
import os

# Blueprint setup
coordenador_route = Blueprint('coordenador', __name__)
UPLOAD_FOLDER = 'uploads'

# Função para carregar dados de autoavaliação filtrados por programa
def carregar_dados_autoavaliacao(arquivo, programa_id):
    file_path = os.path.join(UPLOAD_FOLDER, arquivo)
    if not os.path.exists(file_path):
        return pd.DataFrame()  # Retorna um DataFrame vazio se o arquivo não existir
    
    # Carregar o CSV e filtrar pelo programa
    df = pd.read_csv(file_path, delimiter=';')
    if 'programa_id' in df.columns:
        df = df[df['programa_id'] == programa_id]
    return df

# Rota para o dashboard do coordenador
@coordenador_route.route('/dashboard_coordenador')
@login_required
def dashboard_coordenador():
    try:
        # Obtém o usuário atual e seu programa
        programa_id = current_user.programa_id
        
        # Carregar dados filtrados por programa
        discentes = carregar_dados_autoavaliacao('discente.csv', programa_id)
        docentes = carregar_dados_autoavaliacao('docente.csv', programa_id)
        egressos = carregar_dados_autoavaliacao('egresso.csv', programa_id)
        secretarios = carregar_dados_autoavaliacao('secretario.csv', programa_id)
        coordenacao = carregar_dados_autoavaliacao('coordenacao.csv', programa_id)
        
        # Renderiza o template com os dados
        return render_template(
            'coordenador.html',
            discentes=discentes,
            docentes=docentes,
            egressos=egressos,
            secretarios=secretarios,
            coordenacao=coordenacao
        )
    except Exception as e:
        flash(f"Erro ao carregar o dashboard: {e}", 'danger')
        return redirect(url_for('login'))
