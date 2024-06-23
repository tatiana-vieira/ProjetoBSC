import os
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app, send_file
from flask_login import login_required, current_user
import pandas as pd
import uuid

autoavaliacaocoordenador_route = Blueprint('autoavaliacaocoordenador', __name__)

@autoavaliacaocoordenador_route.before_app_request
def setup_upload_folder():
    current_app.config['UPLOAD_FOLDER'] = 'static/uploads'
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])

@autoavaliacaocoordenador_route.route('/importar_planilha_coordenador', methods=['GET', 'POST'])
@login_required
def importar_planilha_coordenador():
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
            filename = os.path.join(upload_folder, 'coordenador.xlsx')
            file.save(filename)
            flash('Arquivo salvo com sucesso', 'success')

            try:
                coordenador_data = pd.read_excel(filename)
                table_html = generate_coordenador_table(coordenador_data)
                session['table_html_coordenador'] = table_html
                return redirect(url_for('autoavaliacaocoordenador.dashboard_coordenador'))
            except Exception as e:
                flash(f'Erro ao processar a planilha: {str(e)}', 'danger')
                return redirect(request.url)

    return render_template('importar_planilha_coordenador.html')

def generate_coordenador_table(dataframe):
    # Convertendo o DataFrame para uma tabela HTML
    table_html = dataframe.to_html(classes='table table-striped')
    return table_html

@autoavaliacaocoordenador_route.route('/dashboard_coordenador')
@login_required
def dashboard_coordenador():
    table_html = session.get('table_html_coordenador', None)
    if not table_html:
        flash('Nenhuma tabela disponível para exibir', 'danger')
        return redirect(url_for('autoavaliacaocoordenador.importar_planilha_coordenador'))

    return render_template('dashboard_coordenador.html', table_html=table_html)

@autoavaliacaocoordenador_route.route('/gerar_pdf_coordenador')
@login_required
def gerar_pdf_coordenador():
    table_html = session.get('table_html_coordenador', None)
    if not table_html:
        flash('Nenhuma tabela disponível para gerar PDF', 'danger')
        return redirect(url_for('autoavaliacaocoordenador.dashboard_coordenador'))

    from fpdf import FPDF
    from html import unescape

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Dashboard Coordenador', 0, 1, 'C')

        def chapter_title(self, title):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, title, 0, 1, 'L')
            self.ln(10)

        def chapter_body(self, body):
            self.set_font('Arial', '', 12)
            self.multi_cell(0, 10, body)
            self.ln()

        def add_table(self, html):
            self.set_font('Arial', '', 10)
            self.write_html(html)

    pdf = PDF()
    pdf.add_page()
    pdf.add_table(unescape(table_html))

    pdf_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dashboard_coordenador.pdf')
    pdf.output(pdf_filename)

    return send_file(pdf_filename, as_attachment=True)

@autoavaliacaocoordenador_route.route('/fechar_dashboard')
@login_required
def fechar_dashboard():
    session.pop('table_html_coordenador', None)
    return redirect(url_for('autoavaliacaocoordenador.importar_planilha_coordenador'))