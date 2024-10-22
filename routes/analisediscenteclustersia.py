import pandas as pd
from sklearn.cluster import KMeans
from textblob import TextBlob
from flask import Blueprint,request, redirect, url_for,render_template
import os


analisediscenteclustersia_route = Blueprint('analisediscenteclustersia', __name__)

def carregar_dados(filepath):
    # Carrega os dados da planilha
    dados = pd.read_csv(filepath)
    return dados

def aplicar_clusters(dados, n_clusters=5):
    # Selecionar colunas relevantes para a clusterização
    features = dados[['Coluna1', 'Coluna2', 'Coluna3']]  # Modifique para as colunas corretas
    
    # Aplicar KMeans para gerar clusters
    kmeans = KMeans(n_clusters=n_clusters)
    clusters = kmeans.fit_predict(features)
    
    # Adicionar a coluna de clusters aos dados
    dados['Cluster'] = clusters
    return dados


def analisar_sentimentos(texto):
    analise = TextBlob(texto)
    if analise.sentiment.polarity > 0:
        return 'Positivo'
    elif analise.sentiment.polarity == 0:
        return 'Neutro'
    else:
        return 'Negativo'

def gerar_insights(dados_clusterizados):
    insights = []
    for cluster, grupo in dados_clusterizados.groupby('Cluster'):
        media_satisfacao = grupo['Satisfacao'].mean()  # Modifique de acordo com as colunas de interesse
        if media_satisfacao < 3:
            insights.append(f"Cluster {cluster}: Baixa satisfação detectada. Ação recomendada: Melhorar infraestrutura.")
        else:
            insights.append(f"Cluster {cluster}: Satisfação adequada. Manter práticas atuais.")
    return insights

def executar_analise(filepath):
    dados = carregar_dados(filepath)
    dados_clusterizados = aplicar_clusters(dados)
    insights = gerar_insights(dados_clusterizados)
    
    for insight in insights:
        print(insight)


@analisediscenteclustersia_route.route('/executar_analise_upload', methods=['POST'])
def executar_analise_upload():
    if 'file' not in request.files:
        return "Nenhum arquivo foi enviado."

    file = request.files['file']

    if file.filename == '':
        return "Nenhum arquivo selecionado."

    if file:
        # Ler o arquivo CSV diretamente sem salvar no servidor
        dados = pd.read_csv(file)

        # Chamar a função de clusterização e análise
        dados_clusterizados = aplicar_clusters(dados)
        insights = gerar_insights(dados_clusterizados)

        # Exibir os insights
        for insight in insights:
            print(insight)

        return "Análise executada com sucesso!"



@analisediscenteclustersia_route.route('/uploadanalisediscente')
def upload_analise_discente():
    return render_template('uploadanalisediscente.html')