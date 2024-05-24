from flask import render_template,request,flash,redirect,url_for,session,make_response
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan,Valorindicador,Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from flask_login import login_required
import random
import csv
import io
from fpdf import FPDF

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
##################################################################################################################################33333
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

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for meta in metaspe:
        pdf.cell(200, 10, txt=f"Meta: {meta.nome}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Porcentagem de Execução: {meta.porcentagem_execucao}", ln=True, align='L')

        indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
        for indicador in indicadores:
            valores_indicadores = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()
            for valorindicador in valores_indicadores:
                pdf.cell(200, 10, txt=f"Indicador: {indicador.nome}", ln=True, align='L')
                pdf.cell(200, 10, txt=f"Descrição: {indicador.descricao}", ln=True, align='L')
                pdf.cell(200, 10, txt=f"Ano: {valorindicador.ano}", ln=True, align='L')
                pdf.cell(200, 10, txt=f"Semestre: {valorindicador.semestre}", ln=True, align='L')
                pdf.cell(200, 10, txt=f"Valor: {valorindicador.valor}", ln=True, align='L')
                pdf.cell(200, 10, txt="", ln=True, align='L')  # Linha em branco

    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Disposition'] = 'attachment; filename=indicadores.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response