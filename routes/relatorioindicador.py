from flask import render_template, request, flash, redirect, url_for, session, make_response
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan, Valorindicador, Programa,db
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
import matplotlib.pyplot as plt

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
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))

            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()

            for meta in metaspe:
                indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
                indicadores_por_meta[meta.id] = indicadores

            for indicador in IndicadorPlan.query.all():
                valores_indicadores[indicador.id] = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()

        return render_template('dashboard.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, objetivos=objetivospe, metas=metaspe, indicadores_por_meta=indicadores_por_meta, valores_indicadores=valores_indicadores)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))
#################################################################################################333    
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
##################################################################################################################33
@relatorioindicador_route.route('/graficoindicador')
@login_required
def exibir_graficoindicador():
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

    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_(
        [objetivo.id for objetivo in ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()])).all()

    graphs = []
    for meta in metaspe:
        indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
        for indicador in indicadores:
            valores_indicadores = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).order_by(Valorindicador.ano, Valorindicador.semestre).all()
            anos = [f"{vi.ano}/{vi.semestre}" for vi in valores_indicadores]
            valores = [float(vi.valor) for vi in valores_indicadores]

            fig, ax = plt.subplots()
            ax.plot(anos, valores, marker='o')
            ax.set_title(f'{indicador.nome}')
            ax.set_xlabel('Ano/Semestre')
            ax.set_ylabel('Valor')
            ax.set_xticks(range(len(anos)))
            ax.set_xticklabels(anos, rotation=45, ha='right')

            img = BytesIO()
            fig.savefig(img, format='png')
            img.seek(0)
            graph_base64 = base64.b64encode(img.getvalue()).decode('utf8')
            graphs.append((graph_base64, f'{indicador.nome}'))

    return render_template('graficoindicador.html', planejamentos=PlanejamentoEstrategico.query.all(), planejamento_selecionado=planejamento_selecionado, graphs=graphs)
##################################################################################################################333
