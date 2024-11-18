from flask import Flask, render_template,jsonify,request,url_for,redirect,flash,send_file
from .models import PDI, Objetivo, Meta, Indicador,db
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from flask_login import login_required
import pandas as pd
import io

#pdi_route = Flask(__name__)
altpdi_route = Blueprint('altpdi', __name__)

@altpdi_route.route('/selecionar_planejamento', methods=['GET', 'POST'])
def selecionar_programa():
    if request.method == 'POST':
        pdi_id = request.form['pdi_id']
        return redirect(url_for('altpdi.exibir_altpdi', pdi_id=pdi_id))

    pdis = PDI.query.all()
    return render_template('selecionar_programa.html', pdis=pdis)

@altpdi_route.route('/exibir_altpdi')
def exibir_altpdi():
    pdi_id = request.args.get('pdi_id')
    if not pdi_id:
        return redirect(url_for('altpdi.selecionar_programa'))

    pdi_data = PDI.query.filter_by(id=pdi_id).first()
    if not pdi_data:
        flash('Programa não encontrado.')
        return redirect(url_for('altpdi.selecionar_programa'))

    objetivos = Objetivo.query.filter_by(pdi_id=pdi_id).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()

    if not objetivos or not metas or not indicadores:
        flash('Ainda não há planejamento para este programa.')
        return redirect(url_for('altpdi.selecionar_programa'))

    return render_template('altpdi.html', pdi=pdi_data, objetivos=objetivos, metas=metas, indicadores=indicadores)
#############################################################################

@altpdi_route.route('/selecionar_planejamento', methods=['GET', 'POST'])
def selecionar_planejamento():
    if request.method == 'POST':
        pdi_id = request.form['pdi_id']
        return redirect(url_for('altpdi.exibir_planejamento', pdi_id=pdi_id))

    pdis = PDI.query.all()
    return render_template('selecionar_planejamento.html', pdis=pdis)

@altpdi_route.route('/exibir_planejamento')
def exibir_planejamento():
    pdi_id = request.args.get('pdi_id')
    if not pdi_id:
        return redirect(url_for('altpdi.selecionar_planejamento'))

    pdi_data = PDI.query.filter_by(id=pdi_id).first()
    if not pdi_data:
        flash('Planejamento não encontrado.')
        return redirect(url_for('altpdi.selecionar_planejamento'))

    objetivos = Objetivo.query.filter_by(pdi_id=pdi_id).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()

    if not objetivos and not metas and not indicadores:
        flash('Ainda não há planejamento para este PDI.')
        return redirect(url_for('altpdi.selecionar_planejamento'))

    print(f"PDI Data: {pdi_data}")  # Adicionado para depuração
    return render_template('exibir_planejamento.html', pdi=pdi_data, objetivos=objetivos, metas=metas, indicadores=indicadores)


###################################################################################################################################3
@altpdi_route.route('/export_pdi/excel')
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

@altpdi_route.route('/export_pdi/pdf')
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