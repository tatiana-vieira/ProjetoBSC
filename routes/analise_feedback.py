import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Inicializar o analisador de sentimentos
nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Função para análise de sentimento
def analisar_sentimento(texto):
    scores = sid.polarity_scores(texto)
    if scores['compound'] >= 0.05:
        return 'Positivo'
    elif scores['compound'] <= -0.05:
        return 'Negativo'
    else:
        return 'Neutro'

# Função para gerar nuvem de palavras
def gerar_nuvem_palavras(texto):
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(texto)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()

# Função para extrair palavras-chave usando TF-IDF
def extrair_palavras_chave(comentarios):
    vectorizer = TfidfVectorizer(max_features=10)  # Número máximo de palavras importantes
    X = vectorizer.fit_transform(comentarios)
    palavras_chave = vectorizer.get_feature_names_out()
    return palavras_chave

# Função principal de análise de feedback
def analisar_feedback(comentarios):
    resultados_sentimento = [analisar_sentimento(comentario) for comentario in comentarios]
    texto_completo = " ".join(comentarios)
    gerar_nuvem_palavras(texto_completo)
    palavras_chave = extrair_palavras_chave(comentarios)
    
    return resultados_sentimento, palavras_chave
