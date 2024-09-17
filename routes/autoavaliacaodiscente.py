import os
import uuid
import pandas as pd
import matplotlib.pyplot as plt  # Usando Matplotlib para gráficos
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app, send_file
from flask_login import login_required
from textblob import TextBlob  # Para análise de sentimentos
from fpdf import FPDF
from wordcloud import WordCloud
import seaborn as sns

autoavaliacaodiscente_route = Blueprint('autoavaliacaodiscente', __name__)

# Lista de cores para serem aplicadas aos gráficos
cores = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c', '#d35400', '#8e44ad']


# Configurar diretório de upload
@autoavaliacaodiscente_route.before_app_request
def setup_upload_folder():
    current_app.config['UPLOAD_FOLDER'] = 'static/uploads'
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])


@autoavaliacaodiscente_route.route('/dashboard_discente')
def dashboard_discente():
    plot_filenames = session.get('plot_filenames', [])
    recommendations = session.get('recommendations', [])
    sentiment_analysis_plot = session.get('sentiment_analysis_plot', None)
    
    # Renderiza o template do dashboard discente
    return render_template('dashboard_discente.html', plot_urls=plot_filenames, recommendations=recommendations, sentiment_analysis_plot=sentiment_analysis_plot)


def generate_discente_dashboard(dataframe):
    plot_filenames = []  # Lista de gráficos gerados
    table_data = pd.DataFrame()  # Dados da tabela
    recommendations = []  # Lista de recomendações
    sentiment_analysis_plot = None  # Inicializando a variável para gráfico de sentimentos

    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Gera gráficos para cada coluna importante
    for i, column in enumerate(selecionar_colunas_importantes(dataframe)):
        if dataframe[column].dropna().empty:
            continue

        # Tentar converter a coluna para numérico (se possível)
        try:
            dataframe[column] = pd.to_numeric(dataframe[column], errors='coerce')  # Converte para numérico, ignorando valores inválidos
        except Exception as e:
            flash(f"Erro ao converter a coluna {column}: {str(e)}", 'danger')
            continue

        # Gera gráficos de barras com Matplotlib
        plt.figure(figsize=(10, 6))
        color_index = i % len(cores)  # Garante que as cores vão circular pela lista
        dataframe[column].value_counts().plot(kind='bar', title=f'Gráfico de {column}', color=cores[color_index])
        plt.xlabel(column)
        plt.ylabel('Frequência')

        # Salva o gráfico como PNG
        filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
        plt.savefig(filename)
        plot_filenames.append(filename)
        plt.close()

    # Exemplo de análise de sentimentos, se houver coluna de Comentários
    if 'Comentários' in dataframe.columns:
        sentiments = dataframe['Comentários'].apply(analyze_sentiments)
        plt.figure(figsize=(10, 6))
        plt.hist(sentiments, bins=20, color='purple')
        plt.title("Distribuição dos Sentimentos")
        plt.xlabel('Sentimento')
        plt.ylabel('Frequência')

        sentiment_plot_filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
        plt.savefig(sentiment_plot_filename)
        sentiment_analysis_plot = sentiment_plot_filename
        plt.close()

    # Retornar os gráficos gerados, tabela, recomendações e gráfico de sentimentos
    return plot_filenames, table_data, recommendations, sentiment_analysis_plot




@autoavaliacaodiscente_route.route('/gerar_pdf')
def gerar_pdf():
    plot_filenames = session.get('plot_filenames', [])
    if not plot_filenames:
        flash('Nenhum gráfico disponível para gerar PDF', 'danger')
        return redirect(url_for('autoavaliacaodiscente.dashboard_discente'))

    # Cria um PDF com os gráficos
    pdf = FPDF()
    pdf.add_page()
    
    for filename in plot_filenames:
        pdf.image(filename, x=10, y=None, w=pdf.w - 20)
    
    pdf_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dashboard_discente.pdf')
    pdf.output(pdf_filename)
    
    return send_file(pdf_filename, as_attachment=True)


# Função de upload e processamento da planilha
@autoavaliacaodiscente_route.route('/importar_planilha_discente', methods=['GET', 'POST'])
@login_required
def importar_planilha_discente():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        if file:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            filename = os.path.join(upload_folder, 'discente.xlsx')
            
            try:
                # Salvar o arquivo
                file.save(filename)
                flash('Arquivo salvo com sucesso', 'success')
                
                # Processa o arquivo Excel usando o Pandas
                try:
                    discente_data = pd.read_excel(filename)
                    
                    # Verificar as colunas importantes
                    colunas_necessarias = selecionar_colunas_importantes(discente_data)
                    for coluna in colunas_necessarias:
                        if coluna not in discente_data.columns:
                            flash(f"Erro: Coluna '{coluna}' não encontrada na planilha", 'danger')
                            return redirect(request.url)
                    
                    # Se as colunas forem válidas, prosseguir com o processamento
                    flash('Planilha validada com sucesso!', 'success')

                    # Analisar sentimentos (se houver uma coluna de comentários)
                    if 'Comentários' in discente_data.columns:
                        discente_data['Sentimento'] = discente_data['Comentários'].apply(analyze_sentiments)

                    # Gera gráficos, tabela e recomendações
                    plot_filenames, table_data, recommendations, sentiment_analysis_plot = generate_discente_dashboard(discente_data)
                    
                    # Armazena as informações na sessão para serem usadas no dashboard
                    session['plot_filenames'] = plot_filenames
                    session['sentiment_analysis_plot'] = sentiment_analysis_plot
                    session['table_data'] = table_data.to_dict('records')
                    session['recommendations'] = recommendations
                    
                    return redirect(url_for('autoavaliacaodiscente.dashboard_discente'))
                except Exception as e:
                    flash(f"Erro ao processar o arquivo Excel: {str(e)}", 'danger')
                    return redirect(request.url)

            except Exception as e:
                flash(f'Erro ao salvar o arquivo: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('importar_planilhadiscente.html')

# Função de análise de sentimentos para comentários
def analyze_sentiments(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity  # Retorna valor de -1 (negativo) a +1 (positivo)

# Função para selecionar colunas importantes
def selecionar_colunas_importantes(dataframe):
    # Definir colunas importantes (ajuste conforme necessário)
    colunas_importantes = [
        'Qualidade das aulas',
        'Material didático utilizado nas disciplinas',
        'Acervo disponível para consulta',
        'Infraestrutura geral',
        'Laboratorios Salas de estudo',
        'Insumos para pesquisa',
        'Processo de gestão/Administrativo do Programa',
        'Organização do Programa',
        'O Programa está preparado para a internacionalização',
        'Nivel de ingles'
    ]
    return colunas_importantes



def generate_diverse_dashboard(dataframe):
    plot_filenames = []  # Lista de gráficos gerados

    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    for column in dataframe.columns:
        # Verifique se a coluna está vazia antes de gerar o gráfico
        if dataframe[column].dropna().empty:
            continue

        try:
            # Gráfico de Barras para variáveis categóricas
            if len(dataframe[column].unique()) <= 10:
                plt.figure(figsize=(10, 6))
                dataframe[column].value_counts().plot(kind='bar', color='skyblue', title=f'Gráfico de Barras: {column}')
                plt.xlabel(column)
                plt.ylabel('Frequência')
                
                filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                plt.savefig(filename)
                plot_filenames.append(filename)
                plt.close()

            # Gráfico de Pizza para variáveis categóricas
            elif len(dataframe[column].unique()) <= 5:
                plt.figure(figsize=(8, 8))
                dataframe[column].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'], title=f'Gráfico de Pizza: {column}')
                plt.ylabel('')
                
                filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                plt.savefig(filename)
                plot_filenames.append(filename)
                plt.close()

            # Gráfico de Linhas para dados contínuos
            elif pd.api.types.is_numeric_dtype(dataframe[column]):
                plt.figure(figsize=(10, 6))
                dataframe[column].plot(kind='line', color='green', title=f'Gráfico de Linha: {column}')
                plt.xlabel('Índice')
                plt.ylabel(column)
                
                filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                plt.savefig(filename)
                plot_filenames.append(filename)
                plt.close()

            # Gráfico de Dispersão para variáveis numéricas
            if len(dataframe.columns) >= 2:
                for other_column in dataframe.columns:
                    if pd.api.types.is_numeric_dtype(dataframe[other_column]) and column != other_column:
                        plt.figure(figsize=(10, 6))
                        plt.scatter(dataframe[column], dataframe[other_column], c='purple', label=f'{column} vs {other_column}')
                        plt.title(f'Gráfico de Dispersão: {column} vs {other_column}')
                        plt.xlabel(column)
                        plt.ylabel(other_column)
                        
                        filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                        plt.savefig(filename)
                        plot_filenames.append(filename)
                        plt.close()

        except Exception as e:
            flash(f"Erro ao gerar gráfico para {column}: {str(e)}", 'danger')
    
    return plot_filenames

def gerar_graficos(dataframe):
    plot_filenames = []
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Paleta de cores
    cores = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c', '#d35400', '#8e44ad']

    for idx, column in enumerate(dataframe.columns):
        if pd.api.types.is_numeric_dtype(dataframe[column]):
            # Gera gráficos de barras para colunas numéricas
            plt.figure(figsize=(10, 6))
            dataframe[column].value_counts().plot(kind='bar', color=cores[idx % len(cores)])  # Aplica cor diversificada
            plt.title(f'Gráfico de {column}')
            plt.xlabel(column)
            plt.ylabel('Frequência')

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

        else:
            # Gera gráficos de pizza para colunas categóricas
            plt.figure(figsize=(8, 8))
            dataframe[column].value_counts().plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=cores)
            plt.title(f'Distribuição de {column}')
            plt.ylabel('')

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

    return plot_filenames


def gerar_graficos_dispersao(dataframe):
    plot_filenames = []
    upload_folder = current_app.config['UPLOAD_FOLDER']

    for column in dataframe.columns:
        if pd.api.types.is_numeric_dtype(dataframe[column]):
            plt.figure(figsize=(10, 6))
            plt.scatter(dataframe.index, dataframe[column], color='#9b59b6')
            plt.title(f'Distribuição de {column}')
            plt.xlabel('Índice')
            plt.ylabel(column)

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

    return plot_filenames


# Configurar diretório de upload
@autoavaliacaodiscente_route.before_app_request
def setup_upload_folder():
    current_app.config['UPLOAD_FOLDER'] = 'static/uploads'
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])


def generate_diverse_dashboard(dataframe):
    plot_filenames = []  # Lista de gráficos gerados
    upload_folder = current_app.config['UPLOAD_FOLDER']

    for idx, column in enumerate(dataframe.columns):
        if dataframe[column].dropna().empty:
            continue

        try:
            # Gráfico de Barras
            if pd.api.types.is_numeric_dtype(dataframe[column]):
                plt.figure(figsize=(10, 6))
                dataframe[column].value_counts().plot(kind='bar', color=cores[idx % len(cores)])
                plt.title(f'Gráfico de Barras: {column}')
                plt.xlabel(column)
                plt.ylabel('Frequência')

                filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                plt.savefig(filename)
                plot_filenames.append(filename)
                plt.close()

            # Gráfico de Linha
            if len(dataframe[column].unique()) > 5:
                plt.figure(figsize=(10, 6))
                dataframe[column].plot(kind='line', color=cores[idx % len(cores)], title=f'Gráfico de Linha: {column}')
                plt.xlabel('Índice')
                plt.ylabel(column)

                filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                plt.savefig(filename)
                plot_filenames.append(filename)
                plt.close()

            # Gráfico de Pizza (Setores)
            if len(dataframe[column].unique()) <= 5:
                plt.figure(figsize=(8, 8))
                dataframe[column].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=cores, startangle=90)
                plt.title(f'Gráfico de Pizza: {column}')
                plt.ylabel('')

                filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                plt.savefig(filename)
                plot_filenames.append(filename)
                plt.close()

            # Gráfico de Dispersão
            if len(dataframe.columns) >= 2:
                for other_column in dataframe.columns:
                    if pd.api.types.is_numeric_dtype(dataframe[other_column]) and column != other_column:
                        plt.figure(figsize=(10, 6))
                        plt.scatter(dataframe[column], dataframe[other_column], c='purple')
                        plt.title(f'Gráfico de Dispersão: {column} vs {other_column}')
                        plt.xlabel(column)
                        plt.ylabel(other_column)

                        filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                        plt.savefig(filename)
                        plot_filenames.append(filename)
                        plt.close()

            # Gráfico de Área
            plt.figure(figsize=(10, 6))
            dataframe[column].plot(kind='area', color=cores[idx % len(cores)], title=f'Gráfico de Área: {column}')
            plt.xlabel('Índice')
            plt.ylabel(column)

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

            # Gráfico de Pareto
            sorted_data = dataframe[column].value_counts().sort_values(ascending=False)
            cumulative_data = sorted_data.cumsum() / sorted_data.sum() * 100
            plt.figure(figsize=(10, 6))
            sorted_data.plot(kind='bar', color=cores[idx % len(cores)], alpha=0.7)
            plt.ylabel('Frequência')
            plt.title(f'Gráfico de Pareto: {column}')
            plt.twinx()
            cumulative_data.plot(color='r', marker='o')
            plt.ylabel('Cumulativo (%)')

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

            # Gráfico de Bolhas
            if len(dataframe.columns) >= 2:
                for other_column in dataframe.columns:
                    if pd.api.types.is_numeric_dtype(dataframe[other_column]) and column != other_column:
                        plt.figure(figsize=(10, 6))
                        plt.scatter(dataframe[column], dataframe[other_column], s=dataframe[other_column] * 100, alpha=0.5)
                        plt.title(f'Gráfico de Bolhas: {column} vs {other_column}')
                        plt.xlabel(column)
                        plt.ylabel(other_column)

                        filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                        plt.savefig(filename)
                        plot_filenames.append(filename)
                        plt.close()

        except Exception as e:
            flash(f"Erro ao gerar gráfico para {column}: {str(e)}", 'danger')

    return plot_filenames

def gerar_graficos_diversificados(dataframe):
    plot_filenames = []  # Lista de gráficos gerados
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Paleta de cores
    cores = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c', '#d35400', '#8e44ad']

    for idx, column in enumerate(dataframe.columns):
        # Verifica se a coluna não está vazia antes de gerar o gráfico
        if dataframe[column].dropna().empty:
            continue

        # Gera gráficos de barras para colunas categóricas
        if pd.api.types.is_categorical_dtype(dataframe[column]) or dataframe[column].dtype == 'object':
            plt.figure(figsize=(10, 6))
            dataframe[column].value_counts().plot(kind='bar', color=cores[idx % len(cores)])  # Aplica cor diversificada
            plt.title(f'Gráfico de Barras: {column}')
            plt.xlabel(column)
            plt.ylabel('Frequência')

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

        # Gráfico de pizza para colunas categóricas com até 5 categorias
        elif dataframe[column].nunique() <= 5:
            plt.figure(figsize=(8, 8))
            dataframe[column].value_counts().plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=cores)
            plt.title(f'Gráfico de Pizza: {column}')
            plt.ylabel('')

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

        # Gera gráfico de área para colunas numéricas
        elif pd.api.types.is_numeric_dtype(dataframe[column]):
            plt.figure(figsize=(10, 6))
            dataframe[column].plot(kind='area', color=cores[idx % len(cores)])
            plt.title(f'Gráfico de Área: {column}')
            plt.xlabel('Índice')
            plt.ylabel(column)

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

        # Gera gráfico de linha para colunas numéricas
        elif pd.api.types.is_numeric_dtype(dataframe[column]):
            plt.figure(figsize=(10, 6))
            dataframe[column].plot(kind='line', color=cores[idx % len(cores)])
            plt.title(f'Gráfico de Linha: {column}')
            plt.xlabel('Índice')
            plt.ylabel(column)

            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
            plt.savefig(filename)
            plot_filenames.append(filename)
            plt.close()

        # Gera gráfico de bolhas comparando duas colunas numéricas (caso tenha duas colunas numéricas)
        for other_column in dataframe.columns:
            if pd.api.types.is_numeric_dtype(dataframe[other_column]) and column != other_column:
                plt.figure(figsize=(10, 6))
                plt.scatter(dataframe[column], dataframe[other_column], s=100, alpha=0.5, c=cores[idx % len(cores)], label=f'{column} vs {other_column}')
                plt.title(f'Gráfico de Bolhas: {column} vs {other_column}')
                plt.xlabel(column)
                plt.ylabel(other_column)

                filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                plt.savefig(filename)
                plot_filenames.append(filename)
                plt.close()

    return plot_filenames
