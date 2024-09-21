import os
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app, send_file,make_response
from flask_login import login_required, current_user
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
from wordcloud import WordCloud
from textblob import TextBlob
import uuid
from xhtml2pdf import pisa
from io import BytesIO
import base64
import tempfile
import pickle

autoavaliacaodocente_route = Blueprint('autoavaliacaodocente', __name__)

@autoavaliacaodocente_route.before_app_request
def setup_upload_folder():
    current_app.config['UPLOAD_FOLDER'] = 'static/uploads'
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])


@autoavaliacaodocente_route.route('/importar_planilha_docente', methods=['GET', 'POST'])
@login_required
def importar_planilha_docente():
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
            filename = os.path.join(upload_folder, 'docente.xlsx')

            try:
                file.save(filename)
                print(f"Arquivo salvo com sucesso em {filename}")
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")
                flash(f'Erro ao salvar o arquivo: {e}', 'danger')
                return redirect(request.url)

            try:
                # Ler e processar a planilha
                docente_data = pd.read_excel(filename)
                print(f"Colunas disponíveis no dataframe: {docente_data.columns}")
                plot_filenames, recomendacoes = generate_docente_dashboard(docente_data)

                # Salvar o dataframe em um arquivo temporário
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
                with open(temp_file.name, 'wb') as f:
                    pickle.dump(docente_data, f)
                print(f"Dataframe salvo temporariamente em {temp_file.name}")

                # Armazenar o caminho do arquivo temporário na sessão
                session['dataframe_file'] = temp_file.name
                session['plot_filenames'] = plot_filenames
                session['recomendacoes'] = recomendacoes

                return redirect(url_for('autoavaliacaodocente.dashboard_docente'))

            except Exception as e:
                print(f"Erro ao processar a planilha: {e}")
                flash(f'Erro ao processar a planilha: {e}', 'danger')
                return redirect(request.url)

    return render_template('importar_planilha_docente.html')


@autoavaliacaodocente_route.route('/dashboard_docente')
@login_required
def dashboard_docente():
    plot_filenames = session.get('plot_filenames', [])
    recomendacoes = session.get('recomendacoes', [])

    # Verificar o conteúdo de plot_filenames
    if len(plot_filenames) < 2:
        flash('Não foram gerados gráficos suficientes.', 'danger')
        return render_template('erro_graficos.html', recomendacoes=recomendacoes)

    # Gerar URLs para os gráficos
    plot_urls = [os.path.basename(filename) for filename in plot_filenames]

    # Carregar o dataframe do arquivo temporário
    dataframe_file = session.get('dataframe_file')
    if dataframe_file:
        with open(dataframe_file, 'rb') as f:
            docente_data = pickle.load(f)
        dataframe_dict = docente_data.to_dict(orient='records')
    else:
        dataframe_dict = []

    return render_template('dashboard_docente.html', plot_url_1=plot_urls[0], plot_url_2=plot_urls[1], recomendacoes=recomendacoes, dataframe=dataframe_dict)


def generate_docente_dashboard(dataframe):
    """
    Função para gerar gráficos e recomendações com base nos dados da planilha docente.
    """
    plot_filenames = []
    recomendacoes = []

    print("Iniciando a geração de gráficos...")

    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Gerar gráfico de pizza para 'Qualidade das Aulas'
    if 'Como você avalia a qualidade das aulas e do material utilizado? [Qualidade das aulas]' in dataframe.columns:
        caminho_pizza = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
        gerar_grafico_pizza(dataframe, 'Como você avalia a qualidade das aulas e do material utilizado? [Qualidade das aulas]', caminho_pizza)
        plot_filenames.append(caminho_pizza)
        print(f"Gráfico de pizza gerado: {caminho_pizza}")
    else:
        print("Coluna 'Qualidade das Aulas' não encontrada no dataframe")

    # Gerar gráfico de barra para 'Infraestrutura geral'
    if 'Como você avalia a infraestrutura do programa? [Infraestrutura geral]' in dataframe.columns:
        caminho_barra = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
        gerar_grafico_barra(dataframe, 'Como você avalia a infraestrutura do programa? [Infraestrutura geral]', caminho_barra)
        plot_filenames.append(caminho_barra)
        print(f"Gráfico de barra gerado: {caminho_barra}")
    else:
        print("Coluna 'Infraestrutura geral' não encontrada no dataframe")

    # Adicionar recomendações baseadas nos dados
    recomendacoes.append('Sugestões de melhoria baseadas nos dados...')

    return plot_filenames, recomendacoes


def gerar_grafico_pizza(data, coluna, caminho_saida):
    fig, ax = plt.subplots()
    data[coluna].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
    ax.set_ylabel('')
    fig.savefig(caminho_saida)  # Salvando o gráfico no caminho especificado
    plt.close(fig)

    return caminho_saida  # Retorna o caminho do gráfico gerado


def gerar_grafico_barra(data, coluna, caminho_saida):
    fig, ax = plt.subplots()
    data[coluna].value_counts().plot(kind='bar', ax=ax)
    ax.set_ylabel('Frequência')
    ax.set_title(coluna)
    fig.savefig(caminho_saida)  # Salvando o gráfico no caminho especificado
    plt.close(fig)

    return caminho_saida  # Retorna o caminho do gráfico gerado



def gerar_nuvem_palavras(comentarios):
    """Gera uma nuvem de palavras com base nos comentários fornecidos."""
    all_comments = ' '.join(comentarios.dropna())  # Juntando todos os comentários
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_comments)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
    plt.savefig(filename)
    plt.close()

    return filename

def aplicar_clustering(dataframe, colunas):
    kmeans = KMeans(n_clusters=3)
    dataframe['Cluster'] = kmeans.fit_predict(dataframe[colunas])
    return dataframe

def sugerir_melhorias(dataframe):
    recomendacoes = []

    # Exemplo de análise de 'Qualidade das Aulas'
    if 'Qualidade das Aulas' in dataframe.columns:
        media_qualidade = dataframe['Qualidade das Aulas'].mean()
        if media_qualidade < 4:
            recomendacoes.append('Revisar os métodos de ensino para melhorar a qualidade das aulas.')
        else:
            recomendacoes.append('A qualidade das aulas está acima da média, continuar monitorando.')

    # Análise de sentimentos
    if 'Sentimentos' in dataframe.columns:
        media_sentimentos = dataframe['Sentimentos'].mean()
        if media_sentimentos < 0:
            recomendacoes.append('Os comentários indicam insatisfação. Sugerimos melhorar a comunicação com os docentes.')
        else:
            recomendacoes.append('Comentários gerais positivos, manter a comunicação atual.')

    # Infraestrutura
    if 'Infraestrutura' in dataframe.columns:
        media_infraestrutura = dataframe['Infraestrutura'].mean()
        if media_infraestrutura < 3:
            recomendacoes.append('Investir em melhorias na infraestrutura do programa.')
        else:
            recomendacoes.append('Infraestrutura satisfatória.')

    return recomendacoes


def gerar_pdf_docente():
    # Processar a planilha e gerar gráficos
    caminho_grafico_pizza, caminho_grafico_barra = processar_planilha('caminho_para_sua_planilha.xlsx')

    # Renderizar o template HTML com os gráficos
    html = render_template('pdf_template.html', 
                           plot_url_1=caminho_grafico_pizza, 
                           plot_url_2=caminho_grafico_barra)

    # Gerar o PDF
    response = make_response()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=relatorio_docente.pdf'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return "Erro ao gerar PDF", 500
    return response

def gerar_grafico_barra(data, coluna, caminho_saida):
    fig, ax = plt.subplots()
    data[coluna].value_counts().plot(kind='bar', ax=ax)
    ax.set_ylabel('Frequência')
    ax.set_title(coluna)
    fig.savefig(caminho_saida)  # Salvando o gráfico no caminho especificado
    plt.close(fig)

    return caminho_saida  # Retorna o caminho do gráfico gerado


def processar_planilha(planilha_path):
    # Carregar os dados da planilha
    dataframe = pd.read_excel(planilha_path)

    # Definir o caminho completo onde os gráficos serão salvos
    upload_folder = current_app.config['UPLOAD_FOLDER']
    caminho_pizza = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
    caminho_barra = os.path.join(upload_folder, f'{uuid.uuid4()}.png')

    # Gerar gráficos de pizza e barra
    gerar_grafico_pizza(dataframe, 'Como você avalia a qualidade das aulas e do material utilizado? [Qualidade das aulas]', caminho_pizza)
    gerar_grafico_barra(dataframe, 'Como você avalia a infraestrutura do programa? [Infraestrutura geral]', caminho_barra)

    # Retornar os caminhos dos gráficos para usar no PDF ou no dashboard
    return caminho_pizza, caminho_barra


def gerar_grafico_base64():
    # Exemplo simples de gráfico
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])

    # Salvar o gráfico em um buffer de bytes
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    # Codificar a imagem em base64
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return image_base64

def analisar_sentimento(texto):
    if pd.isna(texto) or texto == "":
        return 'Neutro'  # Se o texto estiver vazio ou for NaN, retorna "Neutro"
    analysis = TextBlob(texto)
    if analysis.sentiment.polarity > 0:
        return 'Positivo'
    elif analysis.sentiment.polarity == 0:
        return 'Neutro'
    else:
        return 'Negativo'

    
def classificar_comentario(texto):
    if any(palavra in texto.lower() for palavra in ['bom', 'excelente', 'ótimo']):
        return 'Elogio'
    elif any(palavra in texto.lower() for palavra in ['ruim', 'pior', 'péssimo']):
        return 'Crítica'
    else:
        return 'Sugestão'

