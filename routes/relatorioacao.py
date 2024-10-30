from flask import render_template, flash, request, redirect, session, url_for, make_response  # Certifique-se de que request esteja aqui
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, AcaoPE, Programa, db
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from io import BytesIO
from flask_login import login_required
import csv
import io
import plotly.graph_objs as go
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib import colors
import xlsxwriter
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from datetime import datetime
import matplotlib.pyplot as plt
import base64  # Certifique-se de importar base64
from plotly.utils import PlotlyJSONEncoder
import json
import pandas as pd


relatorioacao_route = Blueprint('relatorioacao', __name__)



def calcular_previsao(meta_pe, porcentagem_execucao, data_inicio, data_termino):
    # Calcular a duração esperada e a duração atual da ação
    duracao_esperada = (meta_pe.data_termino - meta_pe.data_inicio).days
    duracao_atual = (data_termino - data_inicio).days
    dias_restantes = (meta_pe.data_termino - datetime.now().date()).days
    
    # Calcular a eficiência com base na porcentagem de execução e na duração
    eficiencia = (porcentagem_execucao / 100) / (duracao_atual / duracao_esperada)

    # Criar previsões com base em diferentes cenários
    if eficiencia >= 1:
        if dias_restantes > 0:
            return "Ação no caminho certo para atingir a meta no prazo."
        else:
            return "Ação atingiu a meta, mas ultrapassou o prazo."
    elif eficiencia < 1 and dias_restantes > 0:
        return "Ação pode não atingir a meta no tempo previsto. Considere ajustar os recursos ou prazos."
    else:
        return "Ação atrasada. Revise urgentemente o planejamento."


###################################################################################3
from plotly.utils import PlotlyJSONEncoder
import json
from flask import render_template

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
        graph_json = None  # Inicializando a variável para o gráfico interativo
        traces = []  # Certifique-se de inicializar 'traces' no início

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatorioacao.exibir_relatorioacao'))

            # Obter metas e ações associadas
            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
            acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

            if acoespe:
                # Filtra ações únicas por ID
                acoes_unicas = list({acao.id: acao for acao in acoespe}.values())

                for acao in acoes_unicas:
                    trace = go.Bar(
                        x=[acao.porcentagem_execucao],
                        y=[acao.nome],
                        name=acao.nome,  # Adiciona o nome da ação como título da série
                        text=f"Data Início: {acao.data_inicio}<br>Data Término: {acao.data_termino}<br>Status: {acao.status}",
                        hoverinfo='text',
                        marker=dict(
                            color='green' if acao.porcentagem_execucao == 100 else ('red' if datetime.now().date() > acao.data_termino else 'yellow')
                        ),
                        orientation='h'
                    )
                    traces.append(trace)

        # Apenas criar o layout e a figura se houver algo em 'traces'
        if traces:
            layout = go.Layout(
                title="Progresso das Ações",
                xaxis=dict(title="Progresso (%)"),
                yaxis=dict(title="Ação")
            )

            fig = go.Figure(data=traces, layout=layout)

            # Converter gráfico em JSON
            graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)

        return render_template('relatacao.html', 
                               planejamentos=planejamentos, 
                               planejamento_selecionado=planejamento_selecionado, 
                               objetivos=objetivospe, metas=metaspe, acoes=acoespe, 
                               graph_json=graph_json)

    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))


########################################################################################
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
#################################################################################3
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

    headers = ['Objetivo', 'Meta', 'Porcentagem de Execução', 'Ação', 'Data de Início', 'Data de Término', 'Responsável', 'Status', 'Observação', 'Previsão de Impacto']
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    row_num = 1
    for objetivo in objetivospe:
        for meta in metaspe:
            if meta.objetivo_pe_id == objetivo.id:
                for acao in acoespe:
                    if acao.meta_pe_id == meta.id:
                        previsao = calcular_previsao(meta, acao.porcentagem_execucao, acao.data_inicio, acao.data_termino)
                        worksheet.write(row_num, 0, objetivo.nome, cell_format)
                        worksheet.write(row_num, 1, meta.nome, cell_format)
                        worksheet.write(row_num, 2, acao.porcentagem_execucao, cell_format)
                        worksheet.write(row_num, 3, acao.nome, cell_format)
                        worksheet.write(row_num, 4, acao.data_inicio, cell_format)
                        worksheet.write(row_num, 5, acao.data_termino, cell_format)
                        worksheet.write(row_num, 6, acao.responsavel, cell_format)
                        worksheet.write(row_num, 7, acao.status, cell_format)
                        worksheet.write(row_num, 8, acao.observacao, cell_format)
                        worksheet.write(row_num, 9, previsao, cell_format)
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
                        previsao = calcular_previsao(meta, acao.porcentagem_execucao, acao.data_inicio, acao.data_termino)
                        acao_text = (
                            f"<b>Nome da Ação:</b> {acao.nome}<br/>"
                            f"<b>Porcentagem de Execução:</b> {acao.porcentagem_execucao}%<br/>"
                            f"<b>Data de Início:</b> {acao.data_inicio}<br/>"
                            f"<b>Data de Término:</b> {acao.data_termino}<br/>"
                            f"<b>Responsável:</b> {acao.responsavel}<br/>"
                            f"<b>Status:</b> {acao.status}<br/>"
                            f"<b>Observação:</b> {acao.observacao}<br/>"
                            f"<b>Previsão de Impacto:</b> {previsao}<br/><br/>"
                        )
                        elements.append(Paragraph(acao_text, styleN))
                        elements.append(Spacer(1, 12))

    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=acoes.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response


def verificar_alerta_prazo(data_termino):
    dias_restantes = (data_termino - datetime.now().date()).days
    if dias_restantes <= 0:
        return "Ação atrasada!"
    elif dias_restantes <= 7:
        return "Ação próxima do prazo!"
    else:
        return "Ação no prazo."
    
def atualizar_status_automaticamente(acoespe):
    for acao in acoespe:
        if acao.porcentagem_execucao == 100 and acao.status != 'Concluída':
            acao.status = 'Concluída'
            db.session.commit()

def gerar_notificacoes(acoespe):
    notificacoes = []
    for acao in acoespe:
        alerta = verificar_alerta_prazo(acao.data_termino)
        if 'atrasada' in alerta or 'próxima do prazo' in alerta:
            notificacoes.append(f"Ação '{acao.nome}' está {alerta.lower()}.")
    return notificacoes


#######################Junatr relatorios de ação#####################################33
@relatorioacao_route.route('/relatorio_unificado', methods=['GET', 'POST'])
@login_required
def exibir_relatorio_unificado():
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
    objetivospe = []
    metaspe = []
    acoespe = []
    plot_url = None
    graph_json = None
    traces = []

    if planejamento_selecionado_id:
        planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
        if not planejamento_selecionado:
            flash('Planejamento não encontrado.', 'warning')
            return redirect(url_for('relatorio_unificado.exibir_relatorio_unificado'))

        # Obter objetivos, metas e ações associadas ao planejamento
        objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
        metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
        acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

        # Gerar gráfico de Gantt
        if acoespe:
            df = pd.DataFrame([(acao.nome, acao.data_inicio, acao.data_termino) for acao in acoespe], columns=['Ação', 'Início', 'Término'])
            fig, ax = plt.subplots(figsize=(10, 6))
            for i, (acao, inicio, termino) in enumerate(zip(df['Ação'], df['Início'], df['Término'])):
                ax.barh(acao, (termino - inicio).days, left=inicio, height=0.4)

            ax.set_xlabel('Data')
            ax.set_ylabel('Ação')
            ax.set_title('Período de execução das Ações')
            img = io.BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode('utf8')
            plt.close(fig)

        # Gerar gráfico de progresso das ações
        if acoespe:
            acoes_unicas = list({acao.id: acao for acao in acoespe}.values())
            for acao in acoes_unicas:
                trace = go.Bar(
                    x=[acao.porcentagem_execucao],
                    y=[acao.nome],
                    name=acao.nome,
                    text=f"Data Início: {acao.data_inicio}<br>Data Término: {acao.data_termino}<br>Status: {acao.status}",
                    hoverinfo='text',
                    marker=dict(
                        color='green' if acao.porcentagem_execucao == 100 else ('red' if datetime.now().date() > acao.data_termino else 'yellow')
                    ),
                    orientation='h'
                )
                traces.append(trace)

            if traces:
                layout = go.Layout(
                    title="Progresso das Ações",
                    xaxis=dict(title="Progresso (%)"),
                    yaxis=dict(title="Ação")
                )
                fig = go.Figure(data=traces, layout=layout)
                graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)

    return render_template('relatorio_unificado.html', 
                           planejamentos=planejamentos, 
                           planejamento_selecionado=planejamento_selecionado, 
                           objetivos=objetivospe, metas=metaspe, acoes=acoespe, 
                           plot_url=plot_url, graph_json=graph_json)



@relatorioacao_route.route('/export_pdf_unificado', methods=['GET'])
@login_required
def export_pdf_unificado():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatorio_unificado.exibir_relatorio_unificado'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatorio_unificado.exibir_relatorio_unificado'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    acoespe = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

    if not acoespe:
        flash('Nenhuma ação disponível para exportar.', 'warning')
        return redirect(url_for('relatorio_unificado.exibir_relatorio_unificado'))

    # Gera o gráfico de Gantt
    gantt_img = BytesIO()
    df = pd.DataFrame([(acao.nome, acao.data_inicio, acao.data_termino) for acao in acoespe], columns=['Ação', 'Início', 'Término'])
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, (acao, inicio, termino) in enumerate(zip(df['Ação'], df['Início'], df['Término'])):
        ax.barh(acao, (termino - inicio).days, left=inicio, height=0.3, color='skyblue')
    ax.set_xlabel('Data')
    ax.set_ylabel('Ação')
    ax.set_title('Gráfico de Gantt - Período de Execução das Ações')
    plt.savefig(gantt_img, format='png', bbox_inches='tight')
    gantt_img.seek(0)
    plt.close(fig)

    # Gera o gráfico de Progresso das Ações
    progress_img = BytesIO()
    traces = []
    for acao in acoespe:
        trace = go.Bar(
            x=[acao.porcentagem_execucao],
            y=[acao.nome],
            name=acao.nome,
            marker=dict(
                color='green' if acao.porcentagem_execucao == 100 else ('red' if datetime.now().date() > acao.data_termino else 'yellow')
            ),
            orientation='h'
        )
        traces.append(trace)
    if traces:
        layout = go.Layout(
            title="Progresso das Ações",
            xaxis=dict(title="Progresso (%)"),
            yaxis=dict(title="Ação")
        )
        fig = go.Figure(data=traces, layout=layout)
        fig.write_image(progress_img, format='png')
    progress_img.seek(0)

    # Cria o PDF unificado
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Adiciona título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 780, "Relatório Unificado de Ações")

    # Adiciona o gráfico de Gantt
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 740, "Gráfico de Gantt - Período de Execução das Ações")
    c.drawImage(gantt_img, 50, 480, width=500, height=250)  # Ajusta a posição e o tamanho da imagem de Gantt

    # Adiciona o gráfico de Progresso das Ações
    c.drawString(50, 460, "Gráfico de Progresso das Ações")
    c.drawImage(progress_img, 50, 200, width=500, height=250)  # Ajusta a posição e o tamanho da imagem de Progresso

    # Adiciona a data no PDF
    c.setFont("Helvetica", 10)
    c.drawString(50, 180, f"Data de geração: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    c.showPage()
    c.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, download_name='relatorio_unificado_acoes.pdf', as_attachment=True)