import os  # Adicione esta linha no início do arquivo
from flask import Flask, render_template, request, redirect, url_for, Blueprint,send_file
from flask_sqlalchemy import SQLAlchemy
from .models import Discente,Programa,Docente
from flask_login import login_required, LoginManager, current_user
import matplotlib.pyplot as plt
import io
import base64
from flask import render_template
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
import matplotlib.pyplot as plt
from reportlab.lib.enums import TA_JUSTIFY
from datetime import datetime

calculoindicadores_route = Blueprint('calculoindicadores', __name__)
login_manager = LoginManager(calculoindicadores_route)


def calcular_taxa_conclusao_por_ano(programa_id):
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return {}

    anos_coleta = Discente.query.filter_by(codigoprograma=codigo_programa).with_entities(Discente.anocoleta).distinct()
    anos_coleta = sorted(set(ano.anocoleta for ano in anos_coleta))
    taxas_conclusao = {}

    for ano in anos_coleta:
        total_alunos = Discente.query.filter_by(codigoprograma=codigo_programa, anocoleta=ano).count()
        alunos_concluidos = Discente.query.filter_by(codigoprograma=codigo_programa, situacao="TITULADO", anocoleta=ano).count()
        taxa = (alunos_concluidos / total_alunos) * 100 if total_alunos > 0 else 0
        taxas_conclusao[ano] = taxa

    return taxas_conclusao

def calcular_taxa_abandono_por_ano(programa_id):
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return {}

    anos_coleta = Discente.query.filter_by(codigoprograma=codigo_programa).with_entities(Discente.anocoleta).distinct()
    anos_coleta = sorted(set(ano.anocoleta for ano in anos_coleta))
    taxas_abandono = {}

    for ano in anos_coleta:
        total_alunos = Discente.query.filter_by(codigoprograma=codigo_programa, anocoleta=ano).count()
        alunos_abandonados = Discente.query.filter_by(codigoprograma=codigo_programa, situacao="DESLIGADO", anocoleta=ano).count()
        taxa = (alunos_abandonados / total_alunos) * 100 if total_alunos > 0 else 0
        taxas_abandono[ano] = taxa

    return taxas_abandono

@calculoindicadores_route.route('/visualizar_indicadores/<int:programa_id>')
def visualizar_indicadores(programa_id):
    taxas_conclusao = calcular_taxa_conclusao_por_ano(programa_id)
    taxas_abandono = calcular_taxa_abandono_por_ano(programa_id)

    return render_template('view_indicators.html', 
                           taxas_conclusao=taxas_conclusao,
                           taxas_abandono=taxas_abandono,
                           programa_id=programa_id)

@calculoindicadores_route.route('/resultados_indicadores/<int:programa_id>/<int:ano_coleta>')
def resultados_indicadores(programa_id, ano_coleta):
    taxa_conclusao = calcular_taxa_conclusao_por_ano(programa_id, ano_coleta)
    taxa_abandono = calcular_taxa_abandono_por_ano(programa_id, ano_coleta)
 
    return render_template('resultados_indicadores.html', 
                           taxa_conclusao=taxa_conclusao,
                           taxa_abandono=taxa_abandono)


####################################################################################################3
@calculoindicadores_route.route('/visualizar_graficos/<int:programa_id>')
def visualizar_graficos(programa_id):
    taxas_conclusao = calcular_taxa_conclusao_por_ano(programa_id)
    taxas_abandono = calcular_taxa_abandono_por_ano(programa_id)

    # Gerar gráfico de Taxa de Conclusão e Taxa de Abandono
    fig, ax = plt.subplots()
    ax.plot(list(taxas_conclusao.keys()), list(taxas_conclusao.values()), marker='o', label='Taxa de Conclusão')
    ax.plot(list(taxas_abandono.keys()), list(taxas_abandono.values()), marker='x', label='Taxa de Abandono')
    ax.set_xlabel('Ano de Coleta')
    ax.set_ylabel('Taxa (%)')
    ax.set_title('Indicadores de Desempenho por Ano')
    ax.legend()
    plt.xticks(rotation=45)
    
    # Salvar gráfico em base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()

    return render_template('visualizargraficoindicador.html', graph_url=graph_url)

#######################################################################################################3
@calculoindicadores_route.route('/exportar_graficos_pdf/<int:programa_id>')
def exportar_graficos_pdf(programa_id):
    taxas_conclusao = calcular_taxa_conclusao_por_ano(programa_id)
    taxas_abandono = calcular_taxa_abandono_por_ano(programa_id)

    # Gerar gráfico de Taxa de Conclusão e Taxa de Abandono
    fig, ax = plt.subplots()
    ax.plot(list(taxas_conclusao.keys()), list(taxas_conclusao.values()), marker='o', label='Taxa de Conclusão')
    ax.plot(list(taxas_abandono.keys()), list(taxas_abandono.values()), marker='x', label='Taxa de Abandono')
    ax.set_xlabel('Ano de Coleta')
    ax.set_ylabel('Taxa (%)')
    ax.set_title('Indicadores de Desempenho por Ano')
    ax.legend()
    plt.xticks(rotation=45)

    # Salvar gráfico em uma imagem temporária no diretório atual
    img_path = 'indicadores_desempenho.png'
    plt.savefig(img_path)
    plt.close(fig)

    # Criar PDF com ReportLab
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Indicadores de Desempenho por Ano", styles['Title']))
    
    # Adicionar tabela de dados
    data = [["Ano de Coleta", "Indicador", "Valor (%)"]]
    for ano, taxa in taxas_conclusao.items():
        data.append([ano, "Taxa de Conclusão", f"{taxa:.2f}%"])
    for ano, taxa in taxas_abandono.items():
        data.append([ano, "Taxa de Abandono", f"{taxa:.2f}%"])
    
    table = Table(data)
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

    # Adicionar gráfico ao PDF
    elements.append(Paragraph("Gráfico dos Indicadores", styles['Heading2']))
    elements.append(Paragraph("<img src='{}' width='500' height='300' />".format(img_path), styles['BodyText']))

    doc.build(elements)
    buffer.seek(0)

    # Remover a imagem temporária
    os.remove(img_path)

    return send_file(buffer, as_attachment=True, download_name='indicadores_desempenho.pdf', mimetype='application/pdf')
############################################################################################################################
############################################  Docentes  ##################################################################
def calcular_distribuicao_titulacao(programa_id):
    docentes = Docente.query.filter_by(codigoprograma=programa_id).all()
    total_docentes = len(docentes)
    distribuicao = {}
    
    for docente in docentes:
        nivel = docente.nivel
        if nivel not in distribuicao:
            distribuicao[nivel] = 0
        distribuicao[nivel] += 1
    
    for nivel in distribuicao:
        distribuicao[nivel] = (distribuicao[nivel] / total_docentes) * 100
    
    return distribuicao

def calcular_carga_horaria_media(programa_id):
    docentes = Docente.query.filter_by(codigoprograma=programa_id).all()
    total_docentes = len(docentes)
    total_carga_horaria = sum([docente.cargahorariaanual for docente in docentes])
    media_carga_horaria = total_carga_horaria / total_docentes if total_docentes > 0 else 0
    return media_carga_horaria

def calcular_atividades_orientacao_media(programa_id):
    docentes = Docente.query.filter_by(codigoprograma=programa_id).all()
    total_docentes = len(docentes)
    total_orientacoes = {
        'mestrado_academico': sum([docente.mestradoacademico for docente in docentes]),
        'mestrado_profissional': sum([docente.mestradoprofissional for docente in docentes]),
        'tutoria': sum([docente.tutoria for docente in docentes]),
        'monografia': sum([docente.monografia for docente in docentes]),
        'iniciacao_cientifica': sum([docente.iniciacaocientifica for docente in docentes]),
    }
    media_orientacoes = {k: (v / total_docentes if total_docentes > 0 else 0) for k, v in total_orientacoes.items()}
    return media_orientacoes

def calcular_distribuicao_regime_trabalho(programa_id):
    docentes = Docente.query.filter_by(codigoprograma=programa_id).all()
    total_docentes = len(docentes)
    distribuicao = {}
    
    for docente in docentes:
        regime = docente.regimetrabalho
        if regime not in distribuicao:
            distribuicao[regime] = 0
        distribuicao[regime] += 1
    
    for regime in distribuicao:
        distribuicao[regime] = (distribuicao[regime] / total_docentes) * 100
    
    return distribuicao

def calcular_distribuicao_sexo(programa_id):
    docentes = Docente.query.filter_by(codigoprograma=programa_id).all()
    total_docentes = len(docentes)
    distribuicao = {}
    
    for docente in docentes:
        sexo = docente.sexo
        if sexo not in distribuicao:
            distribuicao[sexo] = 0
        distribuicao[sexo] += 1
    
    for sexo in distribuicao:
        distribuicao[sexo] = (distribuicao[sexo] / total_docentes) * 100
    
    return distribuicao

def calcular_distribuicao_categoria(programa_id):
    docentes = Docente.query.filter_by(codigoprograma=programa_id).all()
    total_docentes = len(docentes)
    distribuicao = {}
    
    for docente in docentes:
        categoria = docente.categoria
        if categoria not in distribuicao:
            distribuicao[categoria] = 0
        distribuicao[categoria] += 1
    
    for categoria in distribuicao:
        distribuicao[categoria] = (distribuicao[categoria] / total_docentes) * 100
    
    return distribuicao

def calcular_tempo_medio_afastamento(programa_id):
    docentes = Docente.query.filter_by(codigoprograma=programa_id).all()
    total_afastamentos = 0
    total_dias_afastados = 0
    
    for docente in docentes:
        if docente.datainicioafast and docente.datafimafast:
            data_inicio = datetime.strptime(docente.datainicioafast, '%Y-%m-%d')
            data_fim = datetime.strptime(docente.datafimafast, '%Y-%m-%d')
            dias_afastados = (data_fim - data_inicio).days
            total_dias_afastados += dias_afastados
            total_afastamentos += 1
    
    media_dias_afastados = total_dias_afastados / total_afastamentos if total_afastamentos > 0 else 0
    return media_dias_afastados


def calcular_idade_media_docentes(programa_id):
    docentes = Docente.query.filter_by(codigoprograma=programa_id).all()
    total_idade = 0
    total_docentes = len(docentes)
    
    for docente in docentes:
        if docente.datanasc:
            data_nasc = datetime.strptime(docente.datanasc, '%Y-%m-%d')
            idade = (datetime.now() - data_nasc).days // 365
            total_idade += idade
    
    idade_media = total_idade / total_docentes if total_docentes > 0 else 0
    return idade_media