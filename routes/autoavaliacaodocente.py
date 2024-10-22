import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file
from flask_login import login_required, current_user
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pdfkit
from werkzeug.utils import secure_filename
import uuid  # Adicionar este import
import pickle
import tempfile

autoavaliacaodocente_route = Blueprint('autoavaliacaodocente', __name__)

# Defina o caminho para o upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
GRAPH_FOLDER = 'static/graficos'

# Certifique-se de que os diretórios para uploads e gráficos existam
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(GRAPH_FOLDER):
    os.makedirs(GRAPH_FOLDER)

# Definir a função para verificar a extensão do arquivo
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'xlsx'}  # Defina as extensões permitidas
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@autoavaliacaodocente_route.route('/dashboard_docente/<int:planejamento_id>')
def mostrar_dashboard_docente(planejamento_id):
    try:
        # Carregar os dados relevantes do CSV salvo
        csv_path = os.path.join(UPLOAD_FOLDER, 'dados_relevantes_docente.csv')
        if not os.path.exists(csv_path):
            flash('Arquivo de dados não encontrado. Importe a planilha primeiro.', 'danger')
            return redirect(url_for('autoavaliacaodocente.importar_planilha_docente'))

        df = pd.read_csv(csv_path)

        # Exibir as colunas disponíveis no DataFrame para verificar a formatação
        print("Colunas disponíveis no DataFrame:", df.columns)

        # Padronizar as colunas removendo espaços e convertendo para letras minúsculas
        df.columns = df.columns.str.strip().str.lower()

        # Verificar se as colunas de proficiência e capacitação estão presentes após a padronização
        prof_col_name = 'qual o seu nível de proficiência em língua inglesa?'.lower().strip()
        capacitado_col_name = 'sinto-me capacitado para oferecer disciplinas em língua inglesa:'.lower().strip()

        if prof_col_name in df.columns:
            df['proficiencia_ingles'] = pd.to_numeric(df[prof_col_name], errors='coerce')
        else:
            print("Colunas disponíveis no DataFrame:", df.columns)  # Imprimir as colunas disponíveis para verificar
            flash('A coluna de proficiência em inglês não foi encontrada.', 'danger')
            return redirect(url_for('autoavaliacaodocente.importar_planilha_docente'))

        if capacitado_col_name in df.columns:
            df['capacitado_em_ingles'] = pd.to_numeric(df[capacitado_col_name], errors='coerce')
        else:
            flash('A coluna de capacitação para ensinar em inglês não foi encontrada.', 'danger')
            return redirect(url_for('autoavaliacaodocente.importar_planilha_docente'))

        # Remover linhas com valores NaN nas colunas importantes
        df.dropna(subset=['proficiencia_ingles', 'capacitado_em_ingles'], inplace=True)

        # Criar gráficos e salvar nas pastas correspondentes

        # Gráfico 1: Pizza - Qualidade das aulas
        plt.figure(figsize=(6, 6))
        df['proficiencia_ingles'].value_counts().plot(kind='pie', autopct='%1.1f%%', startangle=90)
        plt.title('Distribuição da Qualidade das Aulas')
        pizza_path = os.path.join(GRAPH_FOLDER, 'pizza_qualidade_aulas_docente.png')
        plt.savefig(pizza_path)
        plt.close()

        # Gráfico 2: Barras - Infraestrutura geral
        plt.figure(figsize=(6, 6))
        df.groupby('proficiencia_ingles')['capacitado_em_ingles'].mean().plot(kind='bar', color='purple')
        plt.title('Infraestrutura Geral')
        barras_path = os.path.join(GRAPH_FOLDER, 'barras_infraestrutura_docente.png')
        plt.savefig(barras_path)
        plt.close()

        # Gráfico 3: Pizza - Proficiência em inglês
        plt.figure(figsize=(6, 6))
        df['proficiencia_ingles'].value_counts().plot(kind='pie', autopct='%1.1f%%', startangle=90)
        plt.title('Distribuição da Proficiência em Inglês')
        pizza_ingles_path = os.path.join(GRAPH_FOLDER, 'pizza_proficiencia_ingles.png')
        plt.savefig(pizza_ingles_path)
        plt.close()

        # Gráfico 4: Barras - Capacitado para ensinar em inglês
        plt.figure(figsize=(6, 6))
        df['capacitado_em_ingles'].value_counts().plot(kind='bar', color='orange')
        plt.title('Capacitação para Ensinar em Inglês')
        barras_ingles_path = os.path.join(GRAPH_FOLDER, 'barras_capacitacao_ingles.png')
        plt.savefig(barras_ingles_path)
        plt.close()

            # Contar quantos alunos não se sentiram aptos a avaliar
        sem_condicoes_proficiencia = df['proficiencia_ingles'].isna().sum()
        sem_condicoes_capacitado = df['capacitado_em_ingles'].isna().sum()

        # Exibir essas contagens no dashboard
        return render_template('dashboard_docente.html',
                            pizza_path='graficos/pizza_qualidade_aulas_docente.png',
                            barras_path='graficos/barras_infraestrutura_docente.png',
                            plot_url_3='graficos/pizza_proficiencia_ingles.png',
                            plot_url_4='graficos/barras_capacitacao_ingles.png',
                            planejamento_id=planejamento_id,
                            sem_condicoes_proficiencia=sem_condicoes_proficiencia,
                            sem_condicoes_capacitado=sem_condicoes_capacitado)

    except Exception as e:
                print(f"Erro ao carregar os dados: {e}")
                flash(f"Ocorreu um erro ao gerar os gráficos: {e}", 'danger')
                return redirect(url_for('autoavaliacaodocente.importar_planilha_docente'))



@autoavaliacaodocente_route.route('/importar_planilha_docente', methods=['GET', 'POST'])
def importar_planilha_docente():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('Nenhum arquivo foi enviado.', 'danger')
                return redirect(request.url)

            file = request.files['file']

            if file.filename == '':
                flash('Nenhum arquivo selecionado.', 'danger')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                # Verifica se a pasta de upload existe, e cria se necessário
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)

                # Salva o arquivo no caminho especificado
                file.save(filepath)

                # Carrega a planilha em um DataFrame Pandas
                df = pd.read_excel(filepath)

                # Padronizar as colunas removendo espaços e convertendo para letras minúsculas
                df.columns = df.columns.str.strip().str.lower()

                # Verifique se as colunas necessárias estão presentes, incluindo proficiência e capacitação
                required_columns = [
                    'como_você_avalia_a_qualidade_das_aulas_e_do_material_utilizado_no_programa_qualidade_das_aulas', 
                    'como_você_avalia_a_infraestrutura_do_programa_infraestrutura_geral',
                    'como_você_avalia_o_seu_conhecimento_acerca_das_normas_capes',
                    'seu_programa_está_preparado_para_a_internacionalização',
                    'os_docentes_do_seu_programa_estão_preparados_para_a_internacionalização'
                ]

                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    flash(f"Erro: As seguintes colunas estão ausentes na planilha: {', '.join(missing_columns)}", 'danger')
                    return redirect(request.url)

                # Processar os dados necessários e salvar em CSV
                dados_relevantes = df[required_columns]
                dados_relevantes.to_csv(os.path.join(UPLOAD_FOLDER, 'dados_relevantes_docente.csv'), index=False)

                flash('Arquivo importado com sucesso!', 'success')

                # Certifique-se de passar o planejamento_id correto ao redirecionar
                planejamento_id = 1  # Troque para o valor correto
                return redirect(url_for('autoavaliacaodocente.mostrar_dashboard_docente', planejamento_id=planejamento_id))
            else:
                flash('Tipo de arquivo não permitido. Envie um arquivo .xlsx', 'danger')
                return redirect(request.url)

    except Exception as e:
        print(f"Erro ao processar a planilha: {e}")
        flash(f"Ocorreu um erro ao processar o arquivo: {e}", 'danger')
        return redirect(request.url)

    return render_template('importar_planilha_docente.html')


@autoavaliacaodocente_route.route('/gerar_pdf_docente')
@login_required
def gerar_pdf_docente():
    try:
        # Recuperar os gráficos e recomendações da sessão
        plot_filenames = session.get('plot_filenames', [])
        recomendacoes = session.get('recomendacoes', [])

        # Renderizar o template HTML com os gráficos e as recomendações
        rendered_html = render_template('dashboard_docente.html',
                                        plot_url_1=plot_filenames[0],
                                        plot_url_2=plot_filenames[1],
                                        recomendacoes=recomendacoes)

        # Gerar o PDF a partir do HTML renderizado
        pdf_path = f'static/relatorios/autoavaliacao_docente.pdf'
        pdfkit.from_string(rendered_html, pdf_path)

        # Enviar o PDF gerado para download
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        flash(f"Ocorreu um erro ao gerar o PDF: {e}", 'danger')
        return redirect(url_for('autoavaliacaodocente.dashboard_docente'))
    
def validate_data(df):
    # Verificar se todas as colunas necessárias estão presentes
    required_columns = ['avaliacao_qualidade', 'avaliacao_infraestrutura', ...]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"As seguintes colunas estão ausentes: {', '.join(missing_columns)}")

    # Verificar se os valores estão no intervalo esperado
    df['avaliacao_qualidade'] = pd.to_numeric(df['avaliacao_qualidade'], errors='coerce')
    df = df[df['avaliacao_qualidade'].between(1, 5)]

    return df