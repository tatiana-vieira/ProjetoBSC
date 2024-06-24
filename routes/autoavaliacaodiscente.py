import os
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app, send_file
from flask_login import current_user, login_required
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import uuid
from fpdf import FPDF

autoavaliacaodiscente_route = Blueprint('autoavaliacaodiscente', __name__)

@autoavaliacaodiscente_route.before_app_request
def setup_upload_folder():
    current_app.config['UPLOAD_FOLDER'] = 'static/uploads'
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])

@autoavaliacaodiscente_route.route('/importar_planilha_discente', methods=['GET', 'POST'])
@login_required
def importar_planilha_discente():
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
            filename = os.path.join(upload_folder, 'discente.xlsx')
            file.save(filename)
            flash('Arquivo salvo com sucesso', 'success')

            try:
                discente_data = pd.read_excel(filename)
                plot_filenames, table_data = generate_discente_dashboard(discente_data)
                session['plot_filenames'] = plot_filenames
                session['table_data'] = table_data.to_dict('records')
                return redirect(url_for('autoavaliacaodiscente.dashboard_discente'))
            except Exception as e:
                flash(f'Erro ao processar a planilha: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('importar_planilhadiscente.html')

def generate_discente_dashboard(dataframe):
    plot_filenames = []
    table_data = pd.DataFrame()
    upload_folder = current_app.config['UPLOAD_FOLDER']

    internationalization_columns = [
        'Impressão: Internacionalização do Programa',
        'Impressão: Preparo para Internacionalização',
        'Nível de Inglês dos Discentes'
    ]

    for column in internationalization_columns:
        if column in dataframe.columns:
            value = dataframe[column].mean()
            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = value,
                title = {'text': column, 'font': {'size': 10}},  # Ajuste do tamanho do título
                gauge = {
                    'axis': {'range': [0, 10]},
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [0, 2], 'color': "red"},
                        {'range': [2, 4], 'color': "orange"},
                        {'range': [4, 6], 'color': "yellow"},
                        {'range': [6, 8], 'color': "lightgreen"},
                        {'range': [8, 10], 'color': "green"}]
                }
            ))
            fig.write_image(filename)
            plot_filenames.append(filename)
    
    for column in dataframe.columns:
        if column in internationalization_columns:
            continue
        
        if dataframe[column].dropna().empty:
            continue
        
        if len(dataframe[column].value_counts()) <= 10:  # Se tem menos de 10 categorias, mostrar como gráfico de barras
            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.figure(figsize=(10, 6))
            dataframe[column].value_counts().plot(kind='bar')
            plt.title(column, fontsize=12)  # Ajuste do tamanho do título
            plt.xlabel('Categorias', fontsize=10)
            plt.ylabel('Valores', fontsize=10)
            plt.xticks(fontsize=8)
            plt.yticks(fontsize=8)
            plt.tight_layout()
            plt.savefig(filename)
            plt.close()
            plot_filenames.append(filename)
        else:  # Se tem mais de 10 categorias, mostrar como tabela
            table_data[column] = dataframe[column]
    
    return plot_filenames, table_data

@autoavaliacaodiscente_route.route('/dashboard_discente')
@login_required
def dashboard_discente():
    plot_filenames = session.get('plot_filenames', [])
    table_data = session.get('table_data', [])
    plot_urls = [url_for('static', filename=f'uploads/{os.path.basename(filename)}') for filename in plot_filenames]
    return render_template('dashboard_discente.html', plot_urls=plot_urls, table_data=table_data)

@autoavaliacaodiscente_route.route('/gerar_pdf')
@login_required
def gerar_pdf():
    plot_filenames = session.get('plot_filenames', [])
    table_data = session.get('table_data', [])
    if not plot_filenames and not table_data:
        flash('Nenhum gráfico ou tabela disponível para gerar PDF', 'danger')
        return redirect(url_for('autoavaliacaodiscente.dashboard_discente'))

    pdf = FPDF()
    pdf.add_page()

    for filename in plot_filenames:
        pdf.image(filename, x=10, y=None, w=pdf.w - 20)
    
    if table_data:
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        line_height = pdf.font_size * 2.5
        col_width = pdf.w / 4  # Ajustar o número de colunas conforme necessário
        for row in table_data:
            for datum in row.values():
                pdf.multi_cell(col_width, line_height, str(datum), border=1, ln=3, max_line_height=pdf.font_size)
            pdf.ln(line_height)

    pdf_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dashboard_discente.pdf')
    pdf.output(pdf_filename)

    return send_file(pdf_filename, as_attachment=True)