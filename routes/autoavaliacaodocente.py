import os
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app, send_file
from flask_login import login_required, current_user
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Configurando o backend do Matplotlib para evitar problemas de GUI
import matplotlib.pyplot as plt
import uuid
from fpdf import FPDF

autoavaliacaodocente_route = Blueprint('autoavaliacaodocente', __name__)

# Variável global para armazenar os caminhos dos gráficos (para testes)
plot_filenames_global = []

@autoavaliacaodocente_route.before_app_request
def setup_upload_folder():
    current_app.config['UPLOAD_FOLDER'] = 'static/uploads'
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])

@autoavaliacaodocente_route.route('/importar_planilha_docente', methods=['GET', 'POST'])
@login_required
def importar_planilha_docente():
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
            filename = os.path.join(upload_folder, 'docente.xlsx')
            file.save(filename)
            flash('Arquivo salvo com sucesso', 'success')

            try:
                docente_data = pd.read_excel(filename)
                plot_filenames = generate_docente_dashboard(docente_data)
                global plot_filenames_global
                plot_filenames_global = plot_filenames
                return redirect(url_for('autoavaliacaodocente.dashboard_docente'))
            except Exception as e:
                flash(f'Erro ao processar a planilha: {str(e)}', 'danger')
                return redirect(request.url)

    return render_template('importar_planilha_docente.html')

def generate_docente_dashboard(dataframe):
    plot_filenames = []
    upload_folder = current_app.config['UPLOAD_FOLDER']

    for column in dataframe.columns[1:]:
        if dataframe[column].dropna().empty:
            continue

        filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
        try:
            plt.figure(figsize=(8, 6))
            dataframe[column].value_counts().plot(kind='bar')
            plt.title(column, fontsize=12)
            plt.xlabel('Categorias', fontsize=9)
            plt.ylabel('Valores', fontsize=9)
            plt.xticks(rotation=45, fontsize=8)
            plt.yticks(fontsize=8)
            plt.tight_layout(pad=2)
            plt.savefig(filename)
            plt.close()
            plot_filenames.append(filename)
        except Exception as e:
            print(f'Erro ao gerar gráfico para a coluna {column}: {str(e)}')

    return plot_filenames

@autoavaliacaodocente_route.route('/dashboard_docente')
@login_required
def dashboard_docente():
    global plot_filenames_global
    plot_urls = [url_for('static', filename=f'uploads/{os.path.basename(filename)}') for filename in plot_filenames_global]
    return render_template('dashboard_docente.html', plot_urls=plot_urls)

@autoavaliacaodocente_route.route('/gerar_pdf_docente')
@login_required
def gerar_pdf_docente():
    global plot_filenames_global
    if not plot_filenames_global:
        flash('Nenhum gráfico disponível para gerar PDF', 'danger')
        return redirect(url_for('autoavaliacaodocente.dashboard_docente'))

    pdf = FPDF()
    pdf.add_page()

    for filename in plot_filenames_global:
        pdf.image(filename, x=10, y=None, w=pdf.w - 20)

    pdf_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dashboard_docente.pdf')
    pdf.output(pdf_filename)

    return send_file(pdf_filename, as_attachment=True)