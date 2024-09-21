import pandas as pd
from textblob import TextBlob  # Para análise de sentimentos
import matplotlib.pyplot as plt  # Para visualização de gráficos

# Carregar os dados
def carregar_dados(caminho_arquivo):
    # Substitua o caminho com o local real do arquivo da planilha
    df = pd.read_excel(caminho_arquivo)
    return df

# Análise de Sentimentos
def analisar_sentimentos(comentario):
    if pd.isna(comentario):
        return "Nenhum Comentário"
    else:
        blob = TextBlob(comentario)
        sentimento = blob.sentiment.polarity
        if sentimento > 0:
            return "Positivo"
        elif sentimento < 0:
            return "Negativo"
        else:
            return "Neutro"

# Filtrar comentários válidos e aplicar análise de sentimentos
def aplicar_analise_sentimentos(df):
    df['Classificacao Sentimento'] = df['Comentario'].apply(analisar_sentimentos)
    return df

# Gráficos para Dados Numéricos
def gerar_graficos_numericos(df):
    # Exemplo de gráfico de barras
    df_numerico = df.dropna()  # Filtrar linhas sem valores
    df_numerico.plot(kind='bar', x='NomeColunaX', y='NomeColunaY')
    plt.title('Gráfico Exemplo')
    plt.show()

# Função principal para executar o processo
def main():
    caminho_arquivo = 'caminho_para_planilha.xlsx'
    df = carregar_dados(caminho_arquivo)

    # Aplicar análise de sentimentos
    df = aplicar_analise_sentimentos(df)

    # Exibir a tabela de resultados
    print(df[['Comentario', 'Classificacao Sentimento']])

    # Gerar gráficos numéricos
    gerar_graficos_numericos(df)

if __name__ == "__main__":
    main()
