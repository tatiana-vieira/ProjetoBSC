from flask import render_template, request, flash, redirect, url_for, session, make_response, jsonify
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan, Programa,CadeiaValor,Risco
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from flask_login import login_required
from io import BytesIO
import pandas as pd
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Spacer


relatorioplanejamento_route = Blueprint('relatorioplanejamento', __name__)

@relatorioplanejamento_route.route('/relplano', methods=['GET'])
@login_required
def exibir_detalhes_planejamento():
    if session.get('role') == 'Coordenador':
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)

        if not programa:
            flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
            return redirect(url_for('login.get_coordenador'))

        planejamentos = programa.planejamentos

        planejamento_selecionado_id = request.args.get('planejamento_selecionado')
        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                return jsonify({'error': 'Planejamento não encontrado'}), 404

            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
            indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas])).all()

            dados = []
            for objetivo in objetivos:
                metas_dados = []
                for meta in [m for m in metas if m.objetivo_pe_id == objetivo.id]:
                    indicadores_dados = [{'nome': indicador.nome} for indicador in indicadores if indicador.meta_pe_id == meta.id]
                    metas_dados.append({'nome': meta.nome, 'indicadores': indicadores_dados})
                dados.append({'nome': objetivo.nome, 'metas': metas_dados})

            return jsonify({'objetivos': dados})

        return render_template('relplanejamento.html', programa=programa, planejamentos=planejamentos)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))
########################################################################################################################
@relatorioplanejamento_route.route('/gerar_pdf/<int:planejamento_id>', methods=['GET'])
@login_required
def gerar_pdf(planejamento_id):
    planejamento = PlanejamentoEstrategico.query.get_or_404(planejamento_id)
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas])).all()

    dados = []
    for objetivo in objetivos:
        metas_dados = []
        for meta in [m for m in metas if m.objetivo_pe_id == objetivo.id]:
            indicadores_dados = [{'nome': indicador.nome} for indicador in indicadores if indicador.meta_pe_id == meta.id]
            metas_dados.append({'nome': meta.nome, 'indicadores': indicadores_dados})
        dados.append({'nome': objetivo.nome, 'metas': metas_dados})

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Relatório de Planejamento Estratégico", styles['Title']))

    for objetivo in dados:
        elements.append(Paragraph(f"Objetivo: {objetivo['nome']}", styles['Heading2']))
        for meta in objetivo['metas']:
            elements.append(Paragraph(f"Meta: {meta['nome']}", styles['Heading3']))
            data = [["Indicador"]]
            for indicador in meta['indicadores']:
                data.append([indicador['nome']])
            table = Table(data, colWidths=[450])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

    doc.build(elements)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'inline; filename=planejamento.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response

#################################################################################3
@relatorioplanejamento_route.route('/gerar_excel/<int:planejamento_id>', methods=['GET'])
@login_required
def gerar_excel(planejamento_id):
    planejamento = PlanejamentoEstrategico.query.get_or_404(planejamento_id)
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas])).all()

    data = []
    for objetivo in objetivos:
        for meta in [m for m in metas if m.objetivo_pe_id == objetivo.id]:
            for indicador in [i for i in indicadores if i.meta_pe_id == meta.id]:
                data.append({
                    'Objetivo': objetivo.nome,
                    'Meta': meta.nome,
                    'Indicador': indicador.nome,
                })

    df = pd.DataFrame(data)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Planejamento')
    writer.save()
    output.seek(0)

    return send_file(output, attachment_filename='planejamento.xlsx', as_attachment=True)


##################################################################################################################
@relatorioplanejamento_route.route('/relcadeia', methods=['GET', 'POST'])
@login_required
def exibir_detalhes_planejamentocadeia():
    if request.method == 'POST':
        planejamento_selecionado_id = request.form.get('planejamento_selecionado')
        
        if not planejamento_selecionado_id:
            flash('Por favor, selecione um planejamento.', 'danger')
            return redirect(url_for('relatorioplanejamento.exibir_detalhes_planejamentocadeia'))

        planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
        if not planejamento_selecionado:
            flash('Planejamento não encontrado.', 'danger')
            return redirect(url_for('relatorioplanejamento.exibir_detalhes_planejamentocadeia'))

        # Buscar os dados relacionados ao planejamento selecionado
        objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
        dados_objetivos = []

        for objetivo in objetivos:
            metas_dados = []
            metas = MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all()
            for meta in metas:
                indicadores = [{'nome': indicador.nome} for indicador in IndicadorPlan.query.filter_by(meta_pe_id=meta.id).all()]
                riscos = [{'descricao': risco.descricao, 'acao_preventiva': risco.acao_preventiva} for risco in Risco.query.filter_by(objetivo_pe_id=objetivo.id).all()]

                # Adiciona metas, indicadores e riscos
                metas_dados.append({
                    'nome': meta.nome,
                    'indicadores': indicadores,
                    'riscos': riscos
                })

            dados_objetivos.append({
                'nome': objetivo.nome,
                'metas': metas_dados
            })

        return render_template('relplanocadeia.html', planejamento_selecionado=planejamento_selecionado, dados_objetivos=dados_objetivos)

    else:
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)
        planejamentos = programa.planejamentos

        return render_template('relplanocadeia.html', planejamentos=planejamentos)


#################################################################################################################3

@relatorioplanejamento_route.route('/gerarrel_pdf/<int:planejamento_id>', methods=['GET'])
@login_required
def gerarrel_pdf(planejamento_id):
    planejamento = PlanejamentoEstrategico.query.get_or_404(planejamento_id)
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas])).all()
    riscos = Risco.query.filter(Risco.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
    

    dados = []
    for objetivo in objetivos:
        metas_dados = []
        for meta in [m for m in metas if m.objetivo_pe_id == objetivo.id]:
            indicadores_dados = [{'nome': indicador.nome} for indicador in indicadores if indicador.meta_pe_id == meta.id]
            metas_dados.append({'nome': meta.nome, 'indicadores': indicadores_dados})
        riscos_dados = [{'descricao': risco.descricao, 'acao_preventiva': risco.acao_preventiva} for risco in riscos if risco.objetivo_pe_id == objetivo.id]
        dados.append({'nome': objetivo.nome, 'metas': metas_dados, 'riscos': riscos_dados})

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Relatório de Planejamento Estratégico", styles['Title']))

    for objetivo in dados:
        elements.append(Paragraph(f"Objetivo: {objetivo['nome']}", styles['Heading2']))
        for meta in objetivo['metas']:
            elements.append(Paragraph(f"Meta: {meta['nome']}", styles['Heading3']))
            data = [["Indicador"]]
            for indicador in meta['indicadores']:
                data.append([indicador['nome']])
            table = Table(data, colWidths=[450])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

    for risco in objetivo['riscos']:
        # Ajustando a tabela com mais espaçamento
        acao_preventiva = risco.get('acao_preventiva', '') if risco.get('acao_preventiva') is not None else ''

        elements.append(Spacer(1, 12))  # Adiciona espaço entre o risco anterior e o novo parágrafo
        elements.append(Paragraph(f"Risco: {risco['descricao']}", styles['Heading3']))

        # Dados da tabela ajustados
        data = [["Descrição", "Ação Preventiva"], 
                [risco['descricao'], acao_preventiva]]

        # Ajustando a largura das colunas
        table = Table(data, colWidths=[6*cm, 6*cm])

        # Melhorando o estilo da tabela
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),  # Alinhando texto à esquerda nas células de dados
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Verticalmente alinhando as células no meio
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))  # Adiciona espaço após a tabela


    doc.build(elements)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'inline; filename=planejamentos.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response


########################################################################################################################
@relatorioplanejamento_route.route('/gerarrel_excel/<int:planejamento_id>', methods=['GET'])
@login_required
def gerarrel_excel(planejamento_id):
    planejamento = PlanejamentoEstrategico.query.get_or_404(planejamento_id)
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas])).all()
    riscos = Risco.query.filter(Risco.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()

    data = []
    for objetivo in objetivos:
        for meta in [m for m in metas if m.objetivo_pe_id == objetivo.id]:
            for indicador in [i for i in indicadores if i.meta_pe_id == meta.id]:
                data.append({
                    'Objetivo': objetivo.nome,
                    'Meta': meta.nome,
                    'Indicador': indicador.nome,
                    'Risco': '',
                    'Ação Preventiva': ''
                })

        for risco in [r for r in riscos if r.objetivo_pe_id == objetivo.id]:
            data.append({
                'Objetivo': objetivo.nome,
                'Meta': '',
                'Indicador': '',
                'Risco': risco.descricao,
                'Ação Preventiva': risco.acao_preventiva
            })

    df = pd.DataFrame(data)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Planejamento')
    writer.close()
    output.seek(0)

    return send_file(output, download_name='planejamento.xlsx', as_attachment=True)