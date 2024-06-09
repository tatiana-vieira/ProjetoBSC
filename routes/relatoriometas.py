from flask import render_template, request, redirect, url_for, jsonify, flash, session, make_response, send_file
from .models import PlanejamentoEstrategico, ObjetivoPE, MetaPE, Valormeta, db, Programa
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
import base64
from io import BytesIO  # Adicione esta linha para importar o módulo io
import csv
import io
import matplotlib.pyplot as plt
from flask_login import login_required
import matplotlib.cm as cm
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

LOGO_PATH = 'static/PPG.png'  # Atualize para o caminho correto do logo
PAGE_WIDTH, PAGE_HEIGHT = letter

relatoriometas_route = Blueprint('relatoriometas', __name__)

def get_planejamento_metas():
    metas = MetaPE.query.all()
    return metas

@relatoriometas_route.route('/relatmetas', methods=['GET'])
@login_required
def exibir_relatoriometas():
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
        valoresmetas = []  # Inicialize valoresmetas aqui

        if planejamento_selecionado_id:
            print(f"Planejamento selecionado ID: {planejamento_selecionado_id}")
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatoriometas.exibir_relatoriometas'))

            print(f"Planejamento selecionado: {planejamento_selecionado.nome}")
            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
            valoresmetas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()
            print(f"Objetivos: {len(objetivospe)}, Metas: {len(metaspe)}, Valores de Metas: {len(valoresmetas)}")
            for meta in metaspe:
                print(f"Meta: {meta.nome}")
                for valor in valoresmetas:
                    if valor.metape_id == meta.id:
                        print(f"  Valor - Ano: {valor.ano}, Semestre: {valor.semestre}, Valor: {valor.valor}")

        return render_template('relatoriometas.html', planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado, objetivos=objetivospe, metas=metaspe, valoresmetas=valoresmetas)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

@relatoriometas_route.route('/editar_meta/<int:meta_id>', methods=['GET'])
@login_required
def editar_meta(meta_id):
    meta = MetaPE.query.get_or_404(meta_id)
    valores_meta = Valormeta.query.filter_by(metape_id=meta_id).all()
    lista_pdis = PlanejamentoEstrategico.query.all()
    objetivos = ObjetivoPE.query.all()
    return render_template('alterar_meta.html', meta=meta, valores_meta=valores_meta, lista_pdis=lista_pdis, objetivos=objetivos)

@relatoriometas_route.route('/salvar_alteracao_meta/<int:meta_id>', methods=['POST'])
@login_required
def salvar_alteracao_meta(meta_id):
    meta = MetaPE.query.get_or_404(meta_id)
    
    # Atualizar campos da meta
    meta.nome = request.form.get('nome')
    meta.descricao = request.form.get('descricao')
    meta.responsavel = request.form.get('responsavel')
    meta.recursos_necessarios = request.form.get('recursos')
    meta.data_inicio = request.form.get('data_inicio')
    meta.data_termino = request.form.get('data_termino')
    meta.status_inicial = request.form.get('status_inicial')
    meta.valor_alvo = request.form.get('valor_alvo')
    
      # Atualizar ou adicionar valores da meta
    anos = request.form.getlist('anos[]')
    semestres = request.form.getlist('semestres[]')
    valores = request.form.getlist('valores[]')

    for ano, semestre, valor in zip(anos, semestres, valores):
        valor = valor.replace(',', '.')  # Substitui vírgula por ponto para garantir o formato correto
        valor_meta = Valormeta.query.filter_by(metape_id=meta_id, ano=ano, semestre=semestre).first()
        if valor_meta:
            valor_meta.valor = valor
        else:
            novo_valor_meta = Valormeta(metape_id=meta_id, ano=ano, semestre=semestre, valor=valor)
            db.session.add(novo_valor_meta)
    
    try:
        db.session.commit()
        flash('Meta alterada com sucesso!', 'success')
        print("Commit realizado com sucesso.")
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar a meta: {str(e)}', 'error')
        print(f"Erro ao salvar a meta: {str(e)}")
    
    return redirect(url_for('relatoriometas.exibir_relatoriometas', planejamento_selecionado=meta.objetivo_pe.planejamento_estrategico_id))


@relatoriometas_route.route('/sucesso')
def sucesso():
    return render_template('sucesso.html')
##############################################################################################################################3

@relatoriometas_route.route('/graficometas', methods=['GET'])
@login_required
def exibir_graficometas():
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
        valoresmetas = []

        if planejamento_selecionado_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
            if not planejamento_selecionado:
                flash('Planejamento não encontrado.', 'warning')
                return redirect(url_for('relatoriometas.exibir_graficometas'))

            objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
            metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
            valoresmetas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()

        # Preparar dados para o gráfico
        dados_graficos = []
        for meta in metaspe:
            valores = [valor for valor in valoresmetas if valor.metape_id == meta.id]
            for valor in valores:
                dados_graficos.append({
                    'meta': meta.nome,
                    'ano': valor.ano,
                    'semestre': valor.semestre,
                    'valor': valor.valor,
                    'valor_alvo': meta.valor_alvo if meta.valor_alvo is not None else 0  # Definindo valor padrão se for None
                })

        # Ordenar dados por ano e semestre
        dados_graficos = sorted(dados_graficos, key=lambda x: (x['ano'], x['semestre']))

        # Gerar o gráfico
        plt.figure(figsize=(14, 8))
        for dado in dados_graficos:
            plt.bar(f"{dado['ano']} S{dado['semestre']}", dado['valor'], label=f"Meta: {dado['meta']}", alpha=0.7)
            plt.axhline(dado['valor_alvo'], color='r', linestyle='--', linewidth=1, label=f"Meta Alvo: {dado['meta']}")

        plt.title('Progresso das Metas')
        plt.xlabel('Período')
        plt.ylabel('Valor')
        plt.xticks(rotation=45, ha='right')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.tight_layout()

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        # Codificar o gráfico em base64 para incorporação no HTML
        graph_base64 = base64.b64encode(img.getvalue()).decode()

        return render_template('graficometas.html', objetivos=objetivospe, metas=metaspe, valoresmetas=valoresmetas, graph_base64=graph_base64, planejamentos=planejamentos, planejamento_selecionado=planejamento_selecionado)
    
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))


#######################################################################################################################################
@relatoriometas_route.route('/gerar_pdf', methods=['GET'])
@login_required
def gerar_pdf():
    coordenador_programa_id = session.get('programa_id')
    programa = Programa.query.get(coordenador_programa_id)

    if not programa:
        flash('Não foi possível encontrar o programa associado ao coordenador.', 'warning')
        return redirect(url_for('login.get_coordenador'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)

    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatoriometas.exibir_graficometas'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    valoresmetas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()

    # Gerar o gráfico novamente
    plt.figure(figsize=(14, 8))  # Aumentar o tamanho da figura
    nomes_metas = [meta.nome for meta in metaspe]
    valores_execucao = [sum(valor.valor for valor in valoresmetas if valor.metape_id == meta.id) for meta in metaspe]

    colors = cm.get_cmap('tab20', len(metaspe))
    bars = plt.bar(range(len(metaspe)), valores_execucao, color=[colors(i / len(metaspe)) for i in range(len(metaspe))])
    plt.title('Valores das Metas')
    plt.xlabel('Meta')
    plt.ylabel('Valor')
    plt.xticks(range(len(metaspe)), [f'Meta {i+1}' for i in range(len(metaspe))], rotation=45, ha='right', fontsize=9)

    for bar, valor in zip(bars, valores_execucao):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom', fontsize=8)

    plt.legend(bars, nomes_metas, bbox_to_anchor=(0.5, -0.3), loc='upper center', ncol=1, fontsize=8)
    plt.subplots_adjust(bottom=0.4, top=0.9)

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    # Criar PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    
    # Adicionar logo centralizado
    logo_width = 100
    logo_height = 50
    c.drawImage(LOGO_PATH, (PAGE_WIDTH - logo_width) / 2, PAGE_HEIGHT - 100, width=logo_width, height=logo_height)
    
    # Adicionar gráfico centralizado
    graph_width = 500
    graph_height = 300
    c.drawImage(ImageReader(img), (PAGE_WIDTH - graph_width) / 2, 350, width=graph_width, height=graph_height)
    
    c.showPage()
    c.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, download_name='grafico_metas.pdf', as_attachment=True)

@relatoriometas_route.route('/export/csv_metas')
@login_required
def export_csv_metas():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatoriometas.exibir_relatoriometas'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatoriometas.exibir_relatoriometas'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    valoresmetas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Meta', 'Ano', 'Semestre', 'Valor'])

    for meta in metaspe:
        for valor in valoresmetas:
            if valor.metape_id == meta.id:
                writer.writerow([meta.nome, valor.ano, valor.semestre, valor.valor])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=metas.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

@relatoriometas_route.route('/export/pdf_metas')
@login_required
def export_pdf_metas():
    if session.get('role') != 'Coordenador':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('login.login_page'))

    planejamento_selecionado_id = request.args.get('planejamento_selecionado')
    if not planejamento_selecionado_id:
        flash('Nenhum planejamento selecionado.', 'warning')
        return redirect(url_for('relatoriometas.exibir_relatoriometas'))

    planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_selecionado_id)
    if not planejamento_selecionado:
        flash('Planejamento não encontrado.', 'warning')
        return redirect(url_for('relatoriometas.exibir_relatoriometas'))

    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_selecionado_id).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    valoresmetas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleN.alignment = TA_JUSTIFY

    elements = []
    elements.append(Paragraph("Relatório de Metas", styles['Title']))

    for meta in metaspe:
        elements.append(Paragraph(f"Meta: {meta.nome}", styles['Heading2']))
        elements.append(Paragraph(f"Descrição: {meta.descricao}", styleN))
        elements.append(Paragraph(f"Responsável: {meta.responsavel}", styleN))
        elements.append(Paragraph(f"Recursos Necessários: {meta.recursos_necessarios}", styleN))
        elements.append(Paragraph(f"Data de Início: {meta.data_inicio}", styleN))
        elements.append(Paragraph(f"Data de Término: {meta.data_termino}", styleN))
        elements.append(Paragraph(f"Status Inicial: {meta.status_inicial}%", styleN))
        elements.append(Paragraph(f"Valor Alvo: {meta.valor_alvo}%", styleN))

        data = [["Ano", "Semestre", "Valor"]]
        for valor in valoresmetas:
            if valor.metape_id == meta.id:
                data.append([valor.ano, valor.semestre, valor.valor])
        
        t = Table(data, colWidths=[50, 50, 50])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Paragraph("", styleN))  # Linha em branco

    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=metas.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response