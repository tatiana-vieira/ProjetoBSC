from flask import render_template,flash,request,redirect,session,url_for,send_file,make_response
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, AcaoPE,Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from io import BytesIO
from flask_login import login_required
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
import matplotlib.pyplot as plt
from reportlab.lib.enums import TA_JUSTIFY


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
####################################################################################################
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

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleN.alignment = TA_JUSTIFY

    elements = []
    elements.append(Paragraph("Relatório de Ações", styles['Title']))

    for objetivo in objetivospe:
        elements.append(Paragraph(f"Objetivo: {objetivo.nome}", styles['Heading2']))
        for meta in metaspe:
            if meta.objetivo_pe_id == objetivo.id:
                elements.append(Paragraph(f"Meta: {meta.nome}", styles['Heading3']))
                data = [["Porcentagem de Execução", "Ação", "Data de Início", "Data de Término", "Responsável", "Status", "Observação"]]
                for acao in acoespe:
                    if acao.meta_pe_id == meta.id:
                        data.append([acao.porcentagem_execucao, acao.nome, acao.data_inicio, acao.data_termino, acao.responsavel, acao.status, acao.observacao])
                
                t = Table(data, colWidths=[50, 100, 50, 50, 50, 50, 100])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(t)
                elements.append(Paragraph("", styleN))  # Linha em branco

    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=acoes.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response