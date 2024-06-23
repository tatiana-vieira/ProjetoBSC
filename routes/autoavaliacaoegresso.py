import os
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app, send_file
from flask_login import current_user, login_required
import pandas as pd
import matplotlib.pyplot as plt
import uuid

autoavaliacaoegresso_route = Blueprint('autoavaliacaoegresso', __name__)

@autoavaliacaoegresso_route.before_app_request
def setup_upload_folder():
    current_app.config['UPLOAD_FOLDER'] = 'static/uploads'
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])

@autoavaliacaoegresso_route.route('/importar_planilha_egresso', methods=['GET', 'POST'])
@login_required
def importar_planilha_egresso():
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
            filename = os.path.join(upload_folder, 'egresso.xlsx')
            file.save(filename)
            flash('Arquivo salvo com sucesso', 'success')

            try:
                egresso_data = pd.read_excel(filename)
                plot_filenames = generate_egresso_dashboard(egresso_data)
                session['plot_filenames_egresso'] = plot_filenames
                return redirect(url_for('autoavaliacaoegresso.dashboard_egresso'))
            except Exception as e:
                flash(f'Erro ao processar a planilha: {str(e)}', 'danger')
                return redirect(request.url)

    return render_template('importar_planilhaegresso.html')

def generate_egresso_dashboard(dataframe):
    plot_filenames = []
    upload_folder = current_app.config['UPLOAD_FOLDER']

    for column in dataframe.columns[1:]:
        if dataframe[column].dropna().empty:
            continue

        filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
        try:
            plt.figure(figsize=(5, 4))
            dataframe[column].value_counts().plot(kind='bar')
            plt.title(column, fontsize=7)
            plt.xlabel('Categorias', fontsize=6)
            plt.ylabel('Valores', fontsize=7)
            plt.xticks(rotation=45, fontsize=6)
            plt.yticks(fontsize=6)
            plt.tight_layout(pad=2)
            plt.savefig(filename)
            plt.close()
            plot_filenames.append(filename)
        except Exception as e:
            print(f'Erro ao gerar gráfico para a coluna {column}: {str(e)}')

    return plot_filenames

@autoavaliacaoegresso_route.route('/dashboard_egresso')
@login_required
def dashboard_egresso():
    plot_filenames = session.get('plot_filenames_egresso', [])
    plot_urls = [url_for('static', filename=f'uploads/{os.path.basename(filename)}') for filename in plot_filenames]
    return render_template('dashboard_egresso.html', plot_urls=plot_urls)

@autoavaliacaoegresso_route.route('/gerar_pdf_egresso')
@login_required
def gerar_pdf_egresso():
    plot_filenames = session.get('plot_filenames_egresso', [])
    if not plot_filenames:
        flash('Nenhum gráfico para gerar PDF', 'danger')
        return redirect(url_for('autoavaliacaoegresso.dashboard_egresso'))

    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for plot_filename in plot_filenames:
        pdf.image(plot_filename, x=10, y=None, w=190)
        pdf.ln(10)

    pdf_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dashboard_egresso.pdf')
    pdf.output(pdf_filename)

    return send_file(pdf_filename, as_attachment=True)