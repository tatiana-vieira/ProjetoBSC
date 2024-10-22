from textblob import TextBlob

# Função para análise de sentimentos
def analisar_sentimento(comentarios):
    sentimentos = []
    for comentario in comentarios:
        blob = TextBlob(comentario)
        polaridade = blob.sentiment.polarity
        if polaridade > 0:
            sentimentos.append('Positivo')
        elif polaridade < 0:
            sentimentos.append('Negativo')
        else:
            sentimentos.append('Neutro')
    return sentimentos

# Função para detectar padrões nas respostas (exemplo simples)
def detectar_padroes(respostas):
    padroes = {}
    for resposta in respostas:
        if 'infraestrutura' in resposta.lower():
            if 'infraestrutura' in padroes:
                padroes['infraestrutura'] += 1
            else:
                padroes['infraestrutura'] = 1
        # Adicione mais padrões conforme necessário
    return padroes

# Função para classificar comentários (elogios, críticas, sugestões)
def classificar_comentarios(comentarios):
    categorias = {'elogio': [], 'critica': [], 'sugestao': []}
    for comentario in comentarios:
        blob = TextBlob(comentario)
        if "gostei" in comentario or blob.sentiment.polarity > 0.5:
            categorias['elogio'].append(comentario)
        elif "não gostei" in comentario or blob.sentiment.polarity < 0:
            categorias['critica'].append(comentario)
        else:
            categorias['sugestao'].append(comentario)
    return categorias
