from flask import render_template, request, flash, redirect, url_for, session, make_response
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan, Valorindicador, Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
import base64
from io import BytesIO
from flask_login import login_required
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors

relatorioindicador_route = Blueprint('relatorioindicador', __name__)

@relatorioindicador_route.route('/relatindicadores')
@login_required
def exibir_relatorioindicador():
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
        indicadores_por_meta = {}
        valores_indicadores = {}

        if planejamento_selecionado_id:
            print(f"Planejamento selecionado ID: {planejamento_selecionado_id}")
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))

            print(f"Planejamento selecionado: {planejamento_selecionado.nome}")
            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()

            for meta in metaspe:
                indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
                indicadores_por_meta[meta.id] = indicadores

            for indicador in IndicadorPlan.query.all():
                valores_indicadores[indicador.id] = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()

        return render_template('relatindicadores.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, objetivos=objetivospe, metas=metaspe, indicadores_por_meta=indicadores_por_meta, valores_indicadores=valores_indicadores)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

@relatorioindicador_route.route('/export/csv')
@login_required
def export_csv():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Meta', 'Porcentagem de Execução', 'Indicador', 'Descrição', 'Ano', 'Semestre', 'Valor'])

    for meta in metaspe:
        indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
        for indicador in indicadores:
            valores_indicadores = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()
            for valorindicador in valores_indicadores:
                writer.writerow([
                    meta.nome,
                    meta.porcentagem_execucao,
                    indicador.nome,
                    indicador.descricao,
                    valorindicador.ano,
                    valorindicador.semestre,
                    valorindicador.valor
                ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=indicadores.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

@relatorioindicador_route.route('/export/pdf')
@login_required
def export_pdf():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleN.alignment = 4  # Justify

    elements = []
    elements.append(Paragraph("Relatório de Indicadores", styles['Title']))

    for meta in metaspe:
        elements.append(Paragraph(f"Meta: {meta.nome}", styles['Heading2']))
        elements.append(Paragraph(f"Porcentagem de Execução: {meta.porcentagem_execucao}", styles['Normal']))
        
        indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
        for indicador in indicadores:
            elements.append(Paragraph(f"Indicador: {indicador.nome}", styles['Heading3']))
            elements.append(Paragraph(f"Descrição: {indicador.descricao}", styleN))
            
            valores_indicadores = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()
            for valor in valores_indicadores:
                elements.append(Paragraph(f"Ano: {valor.ano} Semestre: {valor.semestre} Valor: {valor.valor}", styleN))
            
            elements.append(Paragraph("", styleN))  # Linha em branco

    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=indicadores.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response