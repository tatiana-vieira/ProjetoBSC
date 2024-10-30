from flask import render_template, request, flash, redirect, url_for, session, make_response
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan, Valorindicador, Programa, db
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
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors
import xlsxwriter

relatorioindicador_route = Blueprint('relatorioindicador', __name__)


@relatorioindicador_route.route('/relatindicadores')
@login_required
def exibir_relatorioindicador():
    try:
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
    except Exception as e:
        print(f"Error: {e}")
        flash('Ocorreu um erro ao exibir o relatório. Tente novamente mais tarde.', 'danger')
        return redirect(url_for('login.get_coordenador'))



@relatorioindicador_route.route('/export/xlsx')
@login_required
def export_xlsx():
    try:
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

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
        cell_format = workbook.add_format({'border': 1})

        headers = ['Meta', 'Indicador', 'Descrição', 'Ano', 'Semestre', 'Valor']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        row_num = 1
        for meta in metaspe:
            indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
            for indicador in indicadores:
                valores_indicadores = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()
                for valorindicador in valores_indicadores:
                    worksheet.write(row_num, 0, meta.nome, cell_format)
                    worksheet.write(row_num, 1, indicador.nome, cell_format)
                    worksheet.write(row_num, 2, indicador.descricao, cell_format)
                    worksheet.write(row_num, 3, valorindicador.ano, cell_format)
                    worksheet.write(row_num, 4, valorindicador.semestre, cell_format)
                    worksheet.write(row_num, 5, valorindicador.valor, cell_format)
                    row_num += 1

        workbook.close()
        output.seek(0)

        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=indicadores.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response
    except Exception as e:
        print(f"Error: {e}")
        flash('Ocorreu um erro ao exportar a planilha. Tente novamente mais tarde.', 'danger')
        return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))

@relatorioindicador_route.route('/export/pdf')
@login_required
def export_pdf():
    try:
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
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        styles = getSampleStyleSheet()
        styleN = styles['BodyText']
        styleN.alignment = TA_JUSTIFY

        elements = []
        elements.append(Paragraph("Relatório de Indicadores", styles['Title']))

        for meta in metaspe:
            elements.append(Paragraph(f"Meta: {meta.nome}", styles['Heading2']))
            
            indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id == meta.id).all()
            data = [["Indicador", "Descrição", "Ano", "Semestre", "Valor"]]
            for indicador in indicadores:
                valores_indicadores = Valorindicador.query.filter(Valorindicador.indicadorpe_id == indicador.id).all()
                for valor in valores_indicadores:
                    data.append([indicador.nome, indicador.descricao, valor.ano, valor.semestre, valor.valor])
            
            t = Table(data, colWidths=[80, 150, 40, 40, 40])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(t)
            elements.append(Paragraph("", styleN))  # Linha em branco

        doc.build(elements)

        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=indicadores.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response
    except Exception as e:
        print(f"Error: {e}")
        flash('Ocorreu um erro ao exportar o PDF. Tente novamente mais tarde.', 'danger')
        return redirect(url_for('relatorioindicador.exibir_relatorioindicador'))