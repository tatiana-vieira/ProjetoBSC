import os
from flask import Flask, render_template, request, redirect, url_for, Blueprint, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from .models import Discente, Programa, Docente
from flask_login import login_required, LoginManager, current_user
import matplotlib.pyplot as plt
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
import pandas as pd
from io import BytesIO
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

def calcular_distribuicao_titulacao(programa_id):
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return {}

    docentes = Docente.query.filter_by(codigoprograma=codigo_programa).all()
    total_docentes = len(docentes)
    distribuicao = {}
    
    for docente in docentes:
        nivel = docente.nivel
        if nivel not in distribuicao:
            distribuicao[nivel] = 0
        distribuicao[nivel] += 1
    
    for nivel in distribuicao:
        distribuicao[nivel] = (distribuicao[nivel] / total_docentes) * 100 if total_docentes > 0 else 0
    
    return distribuicao

def calcular_carga_horaria_media(programa_id):
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return 0
    
    docentes = Docente.query.filter_by(codigoprograma=codigo_programa).all()
    total_docentes = len(docentes)
    total_carga_horaria = sum([docente.cargahorariaanual for docente in docentes])
    media_carga_horaria = total_carga_horaria / total_docentes if total_docentes > 0 else 0
    return media_carga_horaria

def calcular_atividades_orientacao_media(programa_id):
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return {}

    docentes = Docente.query.filter_by(codigoprograma=codigo_programa).all()
    total_docentes = len(docentes)
    total_orientacoes = {
        'mestrado_academico': sum([docente.mestradoacademico for docente in docentes]),
        'mestrado_profissional': sum([docente.mestradoprofissional for docente in docentes]),
        'tutoria': sum([docente.tutoria for docente in docentes]),
        'monografia': sum([docente.monografia for docente in docentes]),
        'iniciacao_cientifica': sum([docente.iniciacaocinetifica for docente in docentes]),
    }
    media_orientacoes = {k: (v / total_docentes if total_docentes > 0 else 0) for k, v in total_orientacoes.items()}
    return media_orientacoes

def calcular_distribuicao_regime_trabalho(programa_id):
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return {}

    docentes = Docente.query.filter_by(codigoprograma=codigo_programa).all()
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
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return {}

    docentes = Docente.query.filter_by(codigoprograma=codigo_programa).all()
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
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return {}

    docentes = Docente.query.filter_by(codigoprograma=codigo_programa).all()
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
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return 0
    
    docentes = Docente.query.filter_by(codigoprograma=codigo_programa).all()
    total_afastamentos = 0
    total_dias_afastados = 0
    
    for docente in docentes:
        if docente.datainicioafast and docente.datafimafast:
            try:
                data_inicio = datetime.strptime(docente.datainicioafast, '%Y-%m-%d')
                data_fim = datetime.strptime(docente.datafimafast, '%Y-%m-%d')
                dias_afastados = (data_fim - data_inicio).days
            except ValueError:
                continue
            total_dias_afastados += dias_afastados
            total_afastamentos += 1
    
    media_dias_afastados = total_dias_afastados / total_afastamentos if total_afastamentos > 0 else 0
    return media_dias_afastados

def calcular_idade_media_docentes(programa_id):
    programa = Programa.query.filter_by(id=programa_id).first()
    codigo_programa = programa.codigo if programa else None
    if not codigo_programa:
        return 0
    
    docentes = Docente.query.filter_by(codigoprograma=codigo_programa).all()
    total_idade = 0
    total_docentes = len(docentes)
    
    for docente in docentes:
        if docente.datanasc:
            try:
                data_nasc = datetime.strptime(docente.datanasc, '%Y-%m-%d')
                idade = (datetime.now() - data_nasc).days // 365
                total_idade += idade
            except ValueError:
                continue
    
    idade_media = total_idade / total_docentes if total_docentes > 0 else 0
    return idade_media

@calculoindicadores_route.route('/visualizar_indicadores/<int:programa_id>')
def visualizar_indicadores(programa_id):
    taxa_conclusao = calcular_taxa_conclusao_por_ano(programa_id)
    taxa_abandono = calcular_taxa_abandono_por_ano(programa_id)
    distribuicao_titulacao = calcular_distribuicao_titulacao(programa_id)
    carga_horaria_media = calcular_carga_horaria_media(programa_id)
    atividades_orientacao_media = calcular_atividades_orientacao_media(programa_id)
    distribuicao_regime_trabalho = calcular_distribuicao_regime_trabalho(programa_id)
    distribuicao_sexo = calcular_distribuicao_sexo(programa_id)
    distribuicao_categoria = calcular_distribuicao_categoria(programa_id)
    tempo_medio_afastamento = calcular_tempo_medio_afastamento(programa_id)
    idade_media_docentes = calcular_idade_media_docentes(programa_id)

    return render_template('view_indicators.html', 
                           taxa_conclusao=taxa_conclusao,
                           taxa_abandono=taxa_abandono, 
                           distribuicao_titulacao=distribuicao_titulacao,
                           carga_horaria_media=carga_horaria_media,
                           atividades_orientacao_media=atividades_orientacao_media,
                           distribuicao_regime_trabalho=distribuicao_regime_trabalho,
                           distribuicao_sexo=distribuicao_sexo,
                           distribuicao_categoria=distribuicao_categoria,
                           tempo_medio_afastamento=tempo_medio_afastamento,
                           idade_media_docentes=idade_media_docentes,
                           programa_id=programa_id)

@calculoindicadores_route.route('/exportar_graficos_pdf/<int:programa_id>')
def exportar_graficos_pdf(programa_id):
    taxas_conclusao = calcular_taxa_conclusao_por_ano(programa_id)
    taxas_abandono = calcular_taxa_abandono_por_ano(programa_id)
    distribuicao_titulacao = calcular_distribuicao_titulacao(programa_id)
    carga_horaria_media = calcular_carga_horaria_media(programa_id)
    atividades_orientacao_media = calcular_atividades_orientacao_media(programa_id)
    distribuicao_regime_trabalho = calcular_distribuicao_regime_trabalho(programa_id)
    distribuicao_sexo = calcular_distribuicao_sexo(programa_id)
    distribuicao_categoria = calcular_distribuicao_categoria(programa_id)
    tempo_medio_afastamento = calcular_tempo_medio_afastamento(programa_id)
    idade_media_docentes = calcular_idade_media_docentes(programa_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Indicadores de Desempenho", styles['Title']))

    elements.append(Paragraph("Indicadores de Discentes", styles['Heading2']))

    elements.append(Paragraph("Taxa de Conclusão por Ano", styles['Heading3']))
    data = [["Ano", "Taxa de Conclusão (%)"]]
    for ano, taxa in taxas_conclusao.items():
        data.append([ano, f"{taxa:.2f}"])
    table = Table(data)
    elements.append(table)

    elements.append(Paragraph("Taxa de Abandono por Ano", styles['Heading3']))
    data = [["Ano", "Taxa de Abandono (%)"]]
    for ano, taxa in taxas_abandono.items():
        data.append([ano, f"{taxa:.2f}"])
    table = Table(data)
    elements.append(table)

    elements.append(Paragraph("Indicadores de Docentes", styles['Heading2']))

    elements.append(Paragraph("Distribuição de Titulação", styles['Heading3']))
    data = [["Titulação", "Percentual (%)"]]
    for nivel, percentual in distribuicao_titulacao.items():
        data.append([nivel, f"{percentual:.2f}"])
    table = Table(data)
    elements.append(table)

    elements.append(Paragraph("Carga Horária Média", styles['Heading3']))
    elements.append(Paragraph(f"{carga_horaria_media:.2f} horas", styles['BodyText']))

    elements.append(Paragraph("Atividades de Orientação Média", styles['Heading3']))
    data = [["Tipo", "Média"]]
    for tipo, media in atividades_orientacao_media.items():
        data.append([tipo, f"{media:.2f}"])
    table = Table(data)
    elements.append(table)

    elements.append(Paragraph("Distribuição por Regime de Trabalho", styles['Heading3']))
    data = [["Regime de Trabalho", "Percentual (%)"]]
    for regime, percentual in distribuicao_regime_trabalho.items():
        data.append([regime, f"{percentual:.2f}"])
    table = Table(data)
    elements.append(table)

    elements.append(Paragraph("Distribuição por Sexo", styles['Heading3']))
    data = [["Sexo", "Percentual (%)"]]
    for sexo, percentual in distribuicao_sexo.items():
        data.append([sexo, f"{percentual:.2f}"])
    table = Table(data)
    elements.append(table)

    elements.append(Paragraph("Distribuição por Categoria", styles['Heading3']))
    data = [["Categoria", "Percentual (%)"]]
    for categoria, percentual in distribuicao_categoria.items():
        data.append([categoria, f"{percentual:.2f}"])
    table = Table(data)
    elements.append(table)

    elements.append(Paragraph("Tempo Médio de Afastamento", styles['Heading3']))
    elements.append(Paragraph(f"{tempo_medio_afastamento:.2f} dias", styles['BodyText']))

    elements.append(Paragraph("Idade Média dos Docentes", styles['Heading3']))
    elements.append(Paragraph(f"{idade_media_docentes:.2f} anos", styles['BodyText']))

    doc.build(elements)
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='indicadores_desempenho.pdf', mimetype='application/pdf')

@calculoindicadores_route.route('/gerar_excel_completo/<int:programa_id>', methods=['GET'])
@login_required
def gerar_excel_completo(programa_id):
    taxas_conclusao = calcular_taxa_conclusao_por_ano(programa_id)
    taxas_abandono = calcular_taxa_abandono_por_ano(programa_id)
    distribuicao_titulacao = calcular_distribuicao_titulacao(programa_id)
    carga_horaria_media = calcular_carga_horaria_media(programa_id)
    atividades_orientacao_media = calcular_atividades_orientacao_media(programa_id)
    distribuicao_regime_trabalho = calcular_distribuicao_regime_trabalho(programa_id)
    distribuicao_sexo = calcular_distribuicao_sexo(programa_id)
    distribuicao_categoria = calcular_distribuicao_categoria(programa_id)
    tempo_medio_afastamento = calcular_tempo_medio_afastamento(programa_id)
    idade_media_docentes = calcular_idade_media_docentes(programa_id)

    data = []

    for ano, taxa in taxas_conclusao.items():
        data.append({
            'Indicador': 'Taxa de Conclusão',
            'Categoria': ano,
            'Valor': f"{taxa:.2f}%"
        })

    for ano, taxa in taxas_abandono.items():
        data.append({
            'Indicador': 'Taxa de Abandono',
            'Categoria': ano,
            'Valor': f"{taxa:.2f}%"
        })

    for nivel, percentual in distribuicao_titulacao.items():
        data.append({
            'Indicador': 'Distribuição de Titulação',
            'Categoria': nivel,
            'Valor': f"{percentual:.2f}%"
        })

    data.append({
        'Indicador': 'Carga Horária Média',
        'Categoria': '',
        'Valor': f"{carga_horaria_media:.2f} horas"
    })

    for tipo, media in atividades_orientacao_media.items():
        data.append({
            'Indicador': 'Atividades de Orientação Média',
            'Categoria': tipo,
            'Valor': f"{media:.2f}"
        })

    for regime, percentual in distribuicao_regime_trabalho.items():
        data.append({
            'Indicador': 'Distribuição por Regime de Trabalho',
            'Categoria': regime,
            'Valor': f"{percentual:.2f}%"
        })

    for sexo, percentual in distribuicao_sexo.items():
        data.append({
            'Indicador': 'Distribuição por Sexo',
            'Categoria': sexo,
            'Valor': f"{percentual:.2f}%"
        })

    for categoria, percentual in distribuicao_categoria.items():
        data.append({
            'Indicador': 'Distribuição por Categoria',
            'Categoria': categoria,
            'Valor': f"{percentual:.2f}%"
        })

    data.append({
        'Indicador': 'Tempo Médio de Afastamento',
        'Categoria': '',
        'Valor': f"{tempo_medio_afastamento:.2f} dias"
    })

    data.append({
        'Indicador': 'Idade Média dos Docentes',
        'Categoria': '',
        'Valor': f"{idade_media_docentes:.2f} anos"
    })

    df = pd.DataFrame(data)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Indicadores Completos')
    writer.close()
    output.seek(0)

    return send_file(output, download_name='indicadores_completos.xlsx', as_attachment=True)