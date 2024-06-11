from flask import render_template, flash, request, redirect, session, url_for, make_response
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, AcaoPE, Programa, db
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from io import BytesIO
from flask_login import login_required
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib import colors
import xlsxwriter
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


relatorioacao_route = Blueprint('relatorioacao', __name__)

@relatorioacao_route.route('/relatacao', methods=['GET'])
@login_required
def exibir_relatorioacao():
    if session.get('role') == 'Coordenador':
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)

        if not programa:
            flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
            return redirect(url_for('login.get_coordenador'))

        planejamentos = programa.planejamentos
        planejamento_selecionado_id = request.args.get('planejamento_selecionado')
        planejamento_selecionado = None
        objetivospe = []
        metaspe = []
        acoespe = []

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatorioacao.exibir_relatorioacao'))

            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
            acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

        return render_template('relatacao.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, objetivos=objetivospe, metas=metaspe, acoes=acoespe)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

@relatorioacao_route.route('/export/csv_acoes')
@login_required
def export_csv_acoes():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatorioacao.exibir_relatorioacao'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatorioacao.exibir_relatorioacao'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Objetivo', 'Meta', 'Porcentagem de Execução', 'Ação', 'Data de Início', 'Data de Término', 'Responsável', 'Status', 'Observação'])

    for objetivo in objetivospe:
        for meta in metaspe:
            if meta.objetivo_pe_id == objetivo.id:
                for acao in acoespe:
                    if acao.meta_pe_id == meta.id:
                        writer.writerow([objetivo.nome, meta.nome, acao.porcentagem_execucao, acao.nome, acao.data_inicio, acao.data_termino, acao.responsavel, acao.status, acao.observacao])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=acoes.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

@relatorioacao_route.route('/export/xlsx_acoes')
@login_required
def export_xlsx_acoes():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatorioacao.exibir_relatorioacao'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatorioacao.exibir_relatorioacao'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
    cell_format = workbook.add_format({'border': 1})

    headers = ['Objetivo', 'Meta', 'Porcentagem de Execução', 'Ação', 'Data de Início', 'Data de Término', 'Responsável', 'Status', 'Observação']
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    row_num = 1
    for objetivo in objetivospe:
        for meta in metaspe:
            if meta.objetivo_pe_id == objetivo.id:
                for acao in acoespe:
                    if acao.meta_pe_id == meta.id:
                        worksheet.write(row_num, 0, objetivo.nome, cell_format)
                        worksheet.write(row_num, 1, meta.nome, cell_format)
                        worksheet.write(row_num, 2, acao.porcentagem_execucao, cell_format)
                        worksheet.write(row_num, 3, acao.nome, cell_format)
                        worksheet.write(row_num, 4, acao.data_inicio, cell_format)
                        worksheet.write(row_num, 5, acao.data_termino, cell_format)
                        worksheet.write(row_num, 6, acao.responsavel, cell_format)
                        worksheet.write(row_num, 7, acao.status, cell_format)
                        worksheet.write(row_num, 8, acao.observacao, cell_format)
                        row_num += 1

    workbook.close()
    output.seek(0)

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=acoes.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

#######################################################################################################################

@relatorioacao_route.route('/export/pdf_acoes')
@login_required
def export_pdf_acoes():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatorioacao.exibir_relatorioacao'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatorioacao.exibir_relatorioacao'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleN.alignment = TA_LEFT
    styleN.fontSize = 10
    style_heading = ParagraphStyle(name='Heading', fontSize=12, alignment=TA_LEFT, spaceAfter=10, fontName='Helvetica-Bold')
    style_subheading = ParagraphStyle(name='SubHeading', fontSize=11, alignment=TA_LEFT, spaceAfter=5, fontName='Helvetica-Bold')

    elements = []
    elements.append(Paragraph("Relatório de Ações", styles['Title']))
    elements.append(Spacer(1, 12))

    for objetivo in objetivospe:
        elements.append(Paragraph(f"Objetivo: {objetivo.nome}", style_heading))
        elements.append(Spacer(1, 12))
        for meta in metaspe:
            if meta.objetivo_pe_id == objetivo.id:
                elements.append(Paragraph(f"Meta: {meta.nome}", style_subheading))
                elements.append(Spacer(1, 8))
                for acao in acoespe:
                    if acao.meta_pe_id == meta.id:
                        acao_text = (
                            f"<b>Nome da Ação:</b> {acao.nome}<br/>"
                            f"<b>Porcentagem de Execução:</b> {acao.porcentagem_execucao}%<br/>"
                            f"<b>Data de Início:</b> {acao.data_inicio}<br/>"
                            f"<b>Data de Término:</b> {acao.data_termino}<br/>"
                            f"<b>Responsável:</b> {acao.responsavel}<br/>"
                            f"<b>Status:</b> {acao.status}<br/>"
                            f"<b>Observação:</b> {acao.observacao}<br/><br/>"
                        )
                        elements.append(Paragraph(acao_text, styleN))
                        elements.append(Spacer(1, 12))

    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=acoes.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response