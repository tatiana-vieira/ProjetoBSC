from flask import Flask, render_template, send_file, current_app
from .models import PDI, Objetivo, Meta, Indicador
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
from flask_login import login_required
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors

pdiprppg_route = Blueprint('pdiprppg', __name__)

@pdiprppg_route.route('/relpdi')
@login_required
def exibir_pdi():
    pdi_data = PDI.query.all()
    objetivos = Objetivo.query.filter(Objetivo.pdi_id.in_([pdi.id for pdi in pdi_data])).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()
    
    return render_template('pdi.html', objetivos=objetivos, metas=metas, indicadores=indicadores)

@pdiprppg_route.route('/export_pdi/excel')
@login_required
def export_pdi_excel():
    pdi_data = PDI.query.all()
    objetivos = Objetivo.query.filter(Objetivo.pdi_id.in_([pdi.id for pdi in pdi_data])).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()
    
    data = []
    for objetivo in objetivos:
        for meta in metas:
            if meta.objetivo_id == objetivo.id:
                for indicador in indicadores:
                    if indicador.meta_pdi_id == meta.id:
                        data.append({
                            'Objetivo': objetivo.nome,
                            'Meta': meta.nome,
                            'Indicador': indicador.nome
                        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='PDI')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name='pdi_report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@pdiprppg_route.route('/export_pdi/pdf')
@login_required
def export_pdi_pdf():
    pdi_data = PDI.query.all()
    objetivos = Objetivo.query.filter(Objetivo.pdi_id.in_([pdi.id for pdi in pdi_data])).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleN.alignment = 4  # Justify

    elements = []
    elements.append(Paragraph("Plano de Desenvolvimento Institucional", styles['Title']))

    data = [['Objetivo', 'Meta', 'Indicador']]
    
    for objetivo in objetivos:
        for meta in metas:
            if meta.objetivo_id == objetivo.id:
                for indicador in indicadores:
                    if indicador.meta_pdi_id == meta.id:
                        data.append([
                            Paragraph(objetivo.nome, styleN),
                            Paragraph(meta.nome, styleN),
                            Paragraph(indicador.nome, styleN)
                        ])

    table = Table(data, colWidths=[150, 150, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='pdi_report.pdf', mimetype='application/pdf')