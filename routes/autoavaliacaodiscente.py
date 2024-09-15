import os
import uuid
import pandas as pd
import plotly.express as px
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app, send_file
from flask_login import login_required
from textblob import TextBlob  # Para análise de sentimentos
from fpdf import FPDF
from wordcloud import WordCloud
import matplotlib.pyplot as plt

autoavaliacaodiscente_route = Blueprint('autoavaliacaodiscente', __name__)

# Configurar diretório de upload
@autoavaliacaodiscente_route.before_app_request
def setup_upload_folder():
    current_app.config['UPLOAD_FOLDER'] = 'static/uploads'
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])

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
                # Tenta salvar o arquivo
                file.save(filename)
                flash('Arquivo salvo com sucesso', 'success')
                print(f"Arquivo salvo com sucesso em: {filename}")
                
                # Processa o arquivo Excel usando o Pandas
                try:
                    discente_data = pd.read_excel(filename)
                    print("Dados carregados da planilha:")
                    print(discente_data.head())  # Mostra os primeiros 5 registros para verificar os dados
                    
                    # Verificar os nomes das colunas
                    print("Colunas do DataFrame:", discente_data.columns)
                    
                except Exception as e:
                    flash(f"Erro ao ler o arquivo Excel: {str(e)}", 'danger')
                    return redirect(request.url)

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
                flash(f'Erro ao salvar o arquivo: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('importar_planilhadiscente.html')


# Função de análise de sentimentos para comentários
def analyze_sentiments(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity  # Retorna valor de -1 (negativo) a +1 (positivo)

# Função para gerar gráficos e processar os dados da planilha
def generate_discente_dashboard(dataframe):
    plot_filenames = []  # Lista de gráficos gerados
    table_data = pd.DataFrame()  # Dados da tabela
    recommendations = []  # Lista de recomendações

    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Gera gráficos para cada coluna com até 10 categorias
    for column in dataframe.columns:
        if dataframe[column].dropna().empty:
            continue

        # Gráfico de barras para colunas com até 10 categorias
        if len(dataframe[column].value_counts()) <= 10:
            filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')  # Salvar como PNG
            fig = px.bar(dataframe, x=column, title=f'Gráfico de {column}')
            fig.write_image(filename)
            plot_filenames.append(filename)
        else:
            # Se tiver mais de 10 categorias, colocar na tabela
            table_data[column] = dataframe[column]

    # Análise de sentimentos com gráfico
    if 'Sentimento' in dataframe.columns:
        sentiment_plot_filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
        fig = px.histogram(dataframe, x='Sentimento', nbins=20, title="Distribuição dos Sentimentos dos Comentários")
        fig.write_image(sentiment_plot_filename)
        sentiment_analysis_plot = sentiment_plot_filename
    else:
        sentiment_analysis_plot = None

    # Exemplo de como gerar uma recomendação
    if 'Qualidade das Aulas' in dataframe.columns:
        avg_quality_classes = dataframe['Qualidade das Aulas'].mean()
        if avg_quality_classes < 4:
            recommendations.append('Recomenda-se revisar o método de ensino para melhorar a qualidade das aulas.')

    # Recomendações com base na análise de sentimentos
    if 'Sentimento' in dataframe.columns:
        avg_sentiment = dataframe['Sentimento'].mean()
        if avg_sentiment < 0:
            recommendations.append('Os comentários dos discentes indicam frustração. Considere verificar áreas problemáticas.')

    return plot_filenames, table_data, recommendations, sentiment_analysis_plot

# Rota para o dashboard com gráficos, tabelas e recomendações
@autoavaliacaodiscente_route.route('/dashboard_discente')
@login_required
def dashboard_discente():
    plot_filenames = session.get('plot_filenames', [])
    sentiment_analysis_plot = session.get('sentiment_analysis_plot', None)
    table_data = session.get('table_data', [])
    recommendations = session.get('recommendations', [])
    
    # Cria URLs para exibir os gráficos
    plot_urls = [url_for('static', filename=f'uploads/{os.path.basename(filename)}') for filename in plot_filenames]
    
    return render_template('dashboard_discente.html', plot_urls=plot_urls, sentiment_analysis_plot=sentiment_analysis_plot, table_data=table_data, recommendations=recommendations)

# Rota para gerar o PDF com gráficos e tabelas
@autoavaliacaodiscente_route.route('/gerar_pdf')
@login_required
def gerar_pdf():
    plot_filenames = session.get('plot_filenames', [])
    table_data = session.get('table_data', [])
    if not plot_filenames and not table_data:
        flash('Nenhum gráfico ou tabela disponível para gerar PDF', 'danger')
        return redirect(url_for('autoavaliacaodiscente.dashboard_discente'))

    pdf = FPDF()
    pdf.add_page()

    for filename in plot_filenames:
        pdf.image(filename, x=10, y=None, w=pdf.w - 20)

    # Adicionar análise de sentimentos ao PDF (se houver)
    sentiment_analysis_plot = session.get('sentiment_analysis_plot', None)
    if sentiment_analysis_plot:
        pdf.add_page()
        pdf.image(sentiment_analysis_plot, x=10, y=None, w=pdf.w - 20)
    
    if table_data:
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        line_height = pdf.font_size * 2.5
        col_width = pdf.w / 4  # Ajustar o número de colunas conforme necessário
        for row in table_data:
            for datum in row.values():
                pdf.multi_cell(col_width, line_height, str(datum), border=1, ln=3, max_line_height=pdf.font_size)
            pdf.ln(line_height)

    pdf_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dashboard_discente.pdf')
    pdf.output(pdf_filename)

    return send_file(pdf_filename, as_attachment=True)

def selecionar_colunas_importantes(dataframe):
    # Define colunas importantes com os nomes exatos, conforme exibido no print do DataFrame
    colunas_importantes = {
        'Como você avalia a qualidade das aulas e do material utilizado?  [Qualidade das aulas]': 'numerico',
        'Como você avalia a  infraestrutura do programa?  [Laboratórios de pesquisa/Salas de estudo]': 'numerico',
        'Como você avalia a gestão do programa? [Organização do Programa]': 'numerico',
        '2. Qual o seu ano de ingresso?': 'categorico',
        'Qual o seu nível de proficiência em língua inglesa?': 'numerico',
        'Você se sente preparado para a internacionalização do seu Programa de Pós-Graduação? ': 'numerico'
    }
    return colunas_importantes


def gerar_nuvem_palavras(texto):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(texto))
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()

def sugerir_metas_acao(dataframe):
    recomendacoes = []

    # Exemplo de recomendação para a coluna 'Qual o seu nível de proficiência em língua inglesa'
    if 'Qual o seu nível de proficiência em língua inglesa?' in dataframe.columns:
        avg_proficiencia = dataframe['Qual o seu nível de proficiência em língua inglesa?'].mean()
        if avg_proficiencia < 3:
            recomendacoes.append('Aprimorar programas de suporte ao ensino de língua inglesa.')

    # Outras regras baseadas em colunas específicas
    if 'Qualidade das Aulas' in dataframe.columns:
        avg_quality = dataframe['Qualidade das Aulas'].mean()
        if avg_quality < 4:
            recomendacoes.append('Revisar o método de ensino para melhorar a qualidade das aulas.')
    
    if 'Sentimento' in dataframe.columns:
        avg_sentiment = dataframe['Sentimento'].mean()
        if avg_sentiment < 0:
            recomendacoes.append('Os comentários indicam frustração. Considere investigar as áreas problemáticas.')
    
    return recomendacoes

def gerar_graficos_painel(dataframe):
    colunas_importantes = selecionar_colunas_importantes(dataframe)
    plot_filenames = []

    for column, tipo in colunas_importantes.items():
        print(f"Processando a coluna: {column}")
        print(dataframe[column].head())  # Exibe os primeiros 5 valores da coluna para verificar os dados
        try:
            if tipo == 'numerico':
                # Gera gráfico de barras para colunas numéricas
                filename = f"{uuid.uuid4()}.png"
                fig = px.bar(dataframe, x=column, title=f'Gráfico de {column}')
                fig.write_image(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                plot_filenames.append(filename)
                print(f"Gráfico de barras gerado com sucesso: {filename}")
            elif tipo == 'categorico':
                # Gera gráfico de pizza para colunas categóricas
                filename = f"{uuid.uuid4()}.png"
                fig = px.pie(dataframe, names=column, title=f'Distribuição de {column}')
                fig.write_image(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                plot_filenames.append(filename)
                print(f"Gráfico de pizza gerado com sucesso: {filename}")

        except Exception as e:
            print(f"Erro ao gerar gráfico para {column}: {str(e)}")

    return plot_filenames


def selecionar_colunas_importantes(dataframe):
    # Define colunas importantes manualmente para focar no que é essencial
    colunas_importantes = {
        'Como você avalia a qualidade das aulas e do material utilizado?': 'numerico',
        'Como você avalia a  infraestrutura do programa?  [Laboratórios de pesquisa/Salas de estudo]': 'numerico',
        'Como você avalia a gestão do programa? [Organização do Programa]': 'numerico',
        'Qual o seu ano de ingresso?': 'categorico',
         'Qual o seu nível de proficiência em língua inglesa?': 'numerico',
         'Você se sente preparado para a internacionalização do seu Programa de Pós-Graduação? ': 'numerico'
        # Adicione outras colunas importantes que deseja visualizar
    }
    return colunas_importantes

def gerar_relatorio_simples(dataframe):
    colunas_importantes = selecionar_colunas_importantes(dataframe)
    plot_filenames = []

    for column, tipo in colunas_importantes.items():
        try:
            if tipo == 'numerico':
                # Gera gráfico de barras para colunas numéricas
                filename = f"{uuid.uuid4()}.png"
                fig = px.bar(dataframe, x=column, title=f'Gráfico de {column}')
                fig.write_image(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                plot_filenames.append(filename)
            elif tipo == 'categorico':
                # Gera gráfico de pizza para colunas categóricas
                filename = f"{uuid.uuid4()}.png"
                fig = px.pie(dataframe, names=column, title=f'Distribuição de {column}')
                fig.write_image(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                plot_filenames.append(filename)

        except Exception as e:
            print(f"Erro ao gerar gráfico para {column}: {str(e)}")

    return plot_filenames