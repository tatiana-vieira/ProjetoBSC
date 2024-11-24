from flask import render_template, request, flash, redirect, url_for, session, make_response, jsonify
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
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, IndicadorPlan, Programa,  Risco, Valormeta, AcaoPE


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

##################################################################################################################
@relatorioplanejamento_route.route('/relcadeia', methods=['GET', 'POST'])
@login_required
def exibir_detalhes_planejamentocadeia():
    if request.method == 'POST':
        planejamento_selecionado_id = request.form.get('planejamento_selecionado')

        if not planejamento_selecionado_id:
            flash('Por favor, selecione um planejamento.', 'danger')
            return redirect(url_for('relatorioplanejamento.exibir_detalhes_planejamentocadeia'))

        # Buscar o planejamento selecionado
        planejamento = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
        if not planejamento:
            flash('Planejamento não encontrado.', 'danger')
            return redirect(url_for('relatorioplanejamento.exibir_detalhes_planejamentocadeia'))

        # Buscar os dados associados
        objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
        metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
        indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metaspe])).all()
        valores_metas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()
        riscos = Risco.query.filter(Risco.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
        acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

        # Estruturar os dados para o template
        dados_objetivos = []
        for objetivo in objetivospe:
            metas_dados = []
            for meta in [m for m in metaspe if m.objetivo_pe_id == objetivo.id]:
                indicadores_dados = [{'nome': indicador.nome} for indicador in indicadores if indicador.meta_pe_id == meta.id]
                valores_dados = [{'valor': valor.valor} for valor in valores_metas if valor.metape_id == meta.id]
                acoes_dados = [{'nome': acao.nome, 'porcentagem_execucao': acao.porcentagem_execucao} for acao in acoes if acao.meta_pe_id == meta.id]
                riscos_dados = [{'descricao': risco.descricao, 'acao_preventiva': risco.acao_preventiva} for risco in riscos if risco.meta_pe_id == meta.id]

                metas_dados.append({
                    'nome': meta.nome,
                    'indicadores': indicadores_dados,
                    'valores': valores_dados,
                    'acoes': acoes_dados,
                    'riscos': riscos_dados
                })

            dados_objetivos.append({
                'nome': objetivo.nome,
                'metas': metas_dados
            })


        # Renderizar o template com os dados estruturados
        return render_template('relplanocadeia.html', planejamento=planejamento, dados_objetivos=dados_objetivos)

    else:
        coordenador_programa_id = session.get('programa_id')
        programa = Programa.query.get(coordenador_programa_id)

        if not programa:
            flash('Não foi possível encontrar o programa associado ao coordenador.', 'danger')
            return redirect(url_for('login.get_coordenador'))

        planejamentos = programa.planejamentos

        # Renderizar o template com os planejamentos disponíveis
        return render_template(
            'relplanocadeia.html', 
            planejamentos=planejamentos, 
            planejamento=None, 
            planejamento_selecionado=None, 
            dados_objetivos=[]
        )

#################################################################################################################3
@relatorioplanejamento_route.route('/gerar_excel/<int:planejamento_id>', methods=['GET'], endpoint='gerar_excel')
@login_required
def gerar_excel(planejamento_id):
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



########################################################################################################################
@relatorioplanejamento_route.route('/gerarrel_pdf/<int:planejamento_id>', methods=['GET'], endpoint='gerarrelatorio_pdf')
@login_required
def gerarrel_pdf(planejamento_id):
    planejamento = PlanejamentoEstrategico.query.get_or_404(planejamento_id)
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas])).all()
    valores_metas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metas])).all()
    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).all()
    riscos = Risco.query.filter(Risco.objetivo_pe_id.in_([objetivo.id for objetivo in objetivos])).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Estilos do relatório
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Relatório de Planejamento Estratégico: {planejamento.nome}", styles['Title']))
    elements.append(Spacer(1, 12))

    # Adicionando dados por objetivo
    for objetivo in objetivos:
        elements.append(Paragraph(f"Objetivo: {objetivo.nome}", styles['Heading2']))
        elements.append(Spacer(1, 6))
        for meta in [m for m in metas if m.objetivo_pe_id == objetivo.id]:
            elements.append(Paragraph(f"Meta: {meta.nome}", styles['Heading3']))
            elements.append(Spacer(1, 6))
            
            # Indicadores
            data = [["Indicadores"]]
            for indicador in [i for i in indicadores if i.meta_pe_id == meta.id]:
                data.append([indicador.nome])
            table = Table(data, colWidths=[400])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))
            
            # Valores das metas
            elements.append(Paragraph("Valores da Meta:", styles['Heading4']))
            for valor in [v for v in valores_metas if v.metape_id == meta.id]:
                elements.append(Paragraph(f" - {valor.valor}", styles['BodyText']))
            elements.append(Spacer(1, 12))

            # Ações
            elements.append(Paragraph("Ações:", styles['Heading4']))
            for acao in [a for a in acoes if a.meta_pe_id == meta.id]:
                elements.append(Paragraph(f" - {acao.nome} (Execução: {acao.porcentagem_execucao}%)", styles['BodyText']))
            elements.append(Spacer(1, 12))

        # Riscos
        elements.append(Paragraph("Riscos:", styles['Heading4']))
        for risco in [r for r in riscos if r.objetivo_pe_id == objetivo.id]:
            elements.append(Paragraph(f" - {risco.descricao} (Ação Preventiva: {risco.acao_preventiva})", styles['BodyText']))
        elements.append(Spacer(1, 12))

    doc.build(elements)

    # Retornar o PDF como resposta
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = f'inline; filename=planejamento_{planejamento_id}.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response
