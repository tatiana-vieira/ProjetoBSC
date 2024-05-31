import io
from flask import Flask, render_template, flash, request, redirect, session, url_for, make_response
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, AcaoPE, Programa,IndicadorPlan,Valormeta,Valorindicador
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from flask_login import login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
import csv
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY

app = Flask(__name__)

relatoriocompleto_route = Blueprint('relatoriocompleto', __name__)
#############################################################################

@relatoriocompleto_route.route('/relatorio', methods=['GET'])
@login_required
def relatorio_completo():
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
        valores_meta = []

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatoriocompleto.relatorio_completo'))

            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
            valores_meta = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()

        return render_template('relatorio_completo.html', 
                               planejamentos=planejamentos, 
                               planejamento_selecionado=planejamento_selecionado, 
                               objetivos=objetivospe, 
                               metas=metaspe, 
                               valores_meta=valores_meta)
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))
 ###################################################################################################################
#######################################################################################################################
@relatoriocompleto_route.route('/export_pdf', methods=['GET'])
@login_required
def export_pdf():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatoriocompleto.relatorio_completo'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatoriocompleto.relatorio_completo'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    valores_meta = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleN.alignment = TA_LEFT  # Alinhamento à esquerda
    styleN.fontSize = 8  # Tamanho da fonte menor

    elements = []
    elements.append(Paragraph(f"Relatório Completo: {planejamento_selecionado.nome}", styles['Title']))

    # Largura total da página em pontos
    total_width = 792 - 60  # 11 inches (792 points) - margins
    col_widths = [total_width * 0.4, total_width * 0.4, total_width * 0.06, total_width * 0.07, total_width * 0.07]

    data = [["Nome Objetivo", "Nome Meta", "Ano Meta", "Semestre Meta", "Valor Meta (%)"]]

    for objetivo in objetivospe:
        metas_filtradas = [meta for meta in metaspe if meta.objetivo_pe_id == objetivo.id]
        for meta in metas_filtradas:
            valores_meta_filtrados = [valor for valor in valores_meta if valor.metape_id == meta.id]
            if valores_meta_filtrados:
                for valor_meta in valores_meta_filtrados:
                    data.append([
                        Paragraph(objetivo.nome, styleN),
                        Paragraph(meta.nome, styleN),
                        Paragraph(str(valor_meta.ano), styleN),
                        Paragraph(str(valor_meta.semestre), styleN),
                        Paragraph(f"{valor_meta.valor}%", styleN)
                    ])
            else:
                data.append([
                    Paragraph(objetivo.nome, styleN),
                    Paragraph(meta.nome, styleN),
                    Paragraph("Dados não disponíveis", styleN),
                    Paragraph("", styleN),
                    Paragraph("", styleN)
                ])

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Alinhamento do cabeçalho
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),  # Alinhamento dos dados preenchidos
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),  # Tamanho da fonte do cabeçalho
        ('FONTSIZE', (0, 1), (-1, -1), 6),  # Tamanho da fonte dos dados preenchidos
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_completo.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response

##################################################################################################################################
##################################################################################################################################
@relatoriocompleto_route.route('/relatorio_acao', methods=['GET'])
@login_required
def relatorio_acao():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    coordenador_programa_id = session.get('programa_id')
    programa = Programa.query.get(coordenador_programa_id)

    if not programa:
        flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
        return redirect(url_for('login.get_coordenador'))

    planejamentos = programa.planejamentos
    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    planejamento_selecionado = None
    metas = []
    acoes = []

    if planejamento_selecionado_id:
        planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
        if not planejamento_selecionado:
            flash('Planejamento não encontrado.', 'warning')
            return redirect(url_for('relatoriocompleto.relatorio_acao'))

        objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
        metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
        acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).all()

    return render_template('relatorio_acao.html', 
                           planejamentos=planejamentos, 
                           planejamento_selecionado=planejamento_selecionado, 
                           metas=metas, 
                           acoes=acoes)
    ###########################################################################################################################################
@relatoriocompleto_route.route('/export_pdf_acao', methods=['GET'])
@login_required
def export_pdf_acao():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatoriocompleto.relatorio_acao'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatoriocompleto.relatorio_acao'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleN.alignment = TA_LEFT  # Alinhamento à esquerda
    styleN.fontSize = 6  # Tamanho da fonte menor

    elements = []
    elements.append(Paragraph(f"Plano de Ação: {planejamento_selecionado.nome}", styles['Title']))

    # Largura total da página em pontos
    total_width = 792 - 60  # 11 inches (792 points) - margins
    col_widths = [total_width * 0.2, total_width * 0.2, total_width * 0.2, total_width * 0.1, total_width * 0.1, total_width * 0.1, total_width * 0.1, total_width * 0.1]

    data = [["Meta", "Ação", "Porcentagem Execução", "Data Início", "Data Término", "Responsável", "Status", "Observação"]]

    for meta in metas:
        acoes_filtradas = [acao for acao in acoes if acao.meta_pe_id == meta.id]
        first_row = True
        for acao in acoes_filtradas:
            row = [
                Paragraph(meta.nome, styleN) if first_row else "",
                Paragraph(acao.nome, styleN),
                Paragraph(f"{acao.porcentagem_execucao}%", styleN),
                Paragraph(acao.data_inicio.strftime("%d/%m/%Y") if acao.data_inicio else "", styleN),
                Paragraph(acao.data_termino.strftime("%d/%m/%Y") if acao.data_termino else "", styleN),
                Paragraph(acao.responsavel, styleN),
                Paragraph(acao.status, styleN),
                Paragraph(acao.observacao, styleN)
            ]
            data.append(row)
            first_row = False

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Alinhamento do cabeçalho
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),  # Alinhamento dos dados preenchidos
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),  # Tamanho da fonte do cabeçalho
        ('FONTSIZE', (0, 1), (-1, -1), 6),  # Tamanho da fonte dos dados preenchidos
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_completo.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response