import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
import unicodedata
import nltk
import numpy as np
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from flask import jsonify
from sklearn.ensemble import GradientBoostingRegressor

# Função para substituir "Sim" e "Não" mesmo em frases maiores
def substituir_sim_nao(valor):
    try:
        valor = str(valor).strip().lower()  # Converter o valor para string e remover espaços extras

        # Se contém "sim", retorna 1
        if "sim" in valor:
            return 1
        # Se contém "não", retorna 0
        if "não" in valor or "nao" in valor:
            return 0

        # Caso contrário, retorna o valor original
        return valor
    except Exception as e:
        print(f"Erro ao processar o valor: {valor}. Erro: {e}")
        return valor

# Função para aplicar a substituição de "Sim" e "Não" em colunas específicas
def limpar_e_converter_sim_nao(df, colunas):
    for col in colunas:
        df[col] = df[col].apply(substituir_sim_nao)  # Aplicar a função de substituição
    return df

# Função para calcular a média dos dígitos de uma string numérica
def calcular_media_digitos(valor):
    try:
        valor_str = str(valor).strip()
        if valor_str.isdigit():
            digitos = [int(digito) for digito in valor_str]
            return sum(digitos) / len(digitos)
        else:
            return np.nan
    except Exception as e:
        print(f"Erro ao calcular a média dos dígitos: {e}")
        return np.nan

# Função para substituir valores problemáticos e aplicar a média dos dígitos
def limpar_e_converter_para_numeric(df, colunas):
    # Substituir valores não numéricos específicos
    df.replace("Sem condições de avaliar", np.nan, inplace=True)
    df.replace("Sem condiÃ§Ãµes de avaliar", np.nan, inplace=True)
    df.replace("Sem condicoes de avaliar", np.nan, inplace=True)

    for col in colunas:
        df[col] = df[col].apply(calcular_media_digitos)  # Aplicar a função de média dos dígitos
    return df

# Definir o blueprint
avaliacaosecretaria_route = Blueprint('avaliacaosecretaria', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Verificar se o diretório de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Verifica se o arquivo tem uma extensão permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def renomear_colunas(secretaria):
    # Verificar as colunas antes de renomear
    print("Colunas antes da renomeação:", secretaria.columns)
    
    secretaria.rename({
        'A qual programa esta vinculado(a)?': 'programa',
        'Ha quanto tempo voce e secretario(a) do programa?': 'tempo_programa',
        'Como voce avalia a infraestrutura da secretaria do programa': 'infraestrutura_programa',
        'Existem praticas de acompanhamento dos discentes regularmente matriculados no programa?': 'acompanhamento_discentes',
        'Em caso afirmativo, quais sao essas praticas?': 'praticas_discentes',
        'Existem praticas de acompanhamento dos egressos do programa?': 'acompanhamento_egresso',
        'Em caso afirmativo, quais sao essas praticas?.1': 'pratica_egresso',
        'Que tipos de informacoes sao coletadas?': 'informacoes_coletadas',
        'Como sao armazenadas essas informacoes?': 'armazenadas',
        'O programa faz alguma analise das informacoes coletadas?': 'analise_informacoes',
        'O programa faz levantamento de dados dos egressos apenas para preenchimento da plataforma sucupira?': 'levantamento_egresso_apenas_capes',
        'O programa tem o habito de encaminhar mensagens ou mantem algum contato periodico com os egressos?': 'contato_mensagem_egressos',
        'Em caso afirmativo, com que frequencia?': 'frequencia_egresso',
        'Que tipo de informacoes sao encaminhadas?': 'informacoes_encaminhadas_egresso',
        'e comum os egressos contactarem o programa para buscar informacoes sobre concursos e/ou empregos?': 'egressos_contato_emprego',
        'Voce acha necessario um sistema de acompanhamento de egressos?': 'sistema_acompanhamento_egressos',
        'Quais questoes considera importantes a serem abordadas sobre o acompanhamento dos egressos?': 'consideracoes_egressos',
        'Fique a vontade para dar sugestoes sobre o que considera importante no acompanhamento de egressos?': 'sugestoes'
    }, axis=1, inplace=True)
    
    # Verificar as colunas após a renomeação
    print("Colunas após a renomeação:", secretaria.columns)
    
    # Verificar a presença da coluna 'infraestrutura_programa'
    if 'infraestrutura_programa' not in secretaria.columns:
        print("Erro: 'infraestrutura_programa' não encontrada após a renomeação.")
    else:
        print("Coluna 'infraestrutura_programa' encontrada.")
    
    return secretaria

def limpar_dados(df):
    # Substituir os valores problemáticos por NaN apenas em valores não nulos
    df = df.applymap(lambda x: np.nan if isinstance(x, str) and (
        "Sem condições de avaliar" in x or "Sem condiÃ§Ãµes de avaliar" in x or
        "Sem condicoes de avaliar" in x or "Não se aplica" or "Nao se aplica"in x) else x)
    
    # Garantir que valores de "Sim"/"Não" são corretamente convertidos para numérico
    df.replace({
        'Sim': 1, 'sim': 1, 
        'Não': 0, 'NÃO': 0, 'Nao': 0, 'nao': 0, 'não': 0
    }, inplace=True)
    
    return df         

@avaliacaosecretaria_route.route('/importar_planilhasecretaria', methods=['GET', 'POST'])
def importar_planilhasecretaria():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo foi enviado', 'danger')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Salvar o arquivo
            file.save(file_path)

            # Redirecionar para a geração de gráficos passando o nome do arquivo
            return redirect(url_for('avaliacaosecretaria.gerar_graficos_completos_secretaria', filename=filename))

    return render_template('importar_planilhasecretaria.html')

def normalize_column_names(df):
    df.columns = [unicodedata.normalize('NFKD', col).encode('ascii', 'ignore').decode('utf-8').strip().lower().replace('  ', ' ').replace(' ', '_').replace('[', '').replace(']', '') for col in df.columns]
    return df

# Função para calcular a média dos dígitos de uma string de números
def calcular_media_digitos(valor):
    try:
        digitos = [int(digito) for digito in str(valor)]  # Converter cada caractere em um número
        return sum(digitos) / len(digitos)  # Calcular a média dos dígitos
    except (ValueError, TypeError):
        return None  # Retornar None se houver erro na conversão

# Função para limpar e aplicar a média dos dígitos nas colunas problemáticas
def limpar_e_converter_para_numeric(df, colunas):
    # Substituir os valores problemáticos por 0
    df.replace("Sem condições de avaliar", 0, inplace=True)
    df.replace("Sem condiÃ§Ãµes de avaliar", 0, inplace=True)
    df.replace("Sem condicoes de avaliar", 0, inplace=True)

    df.replace({'Sim': 1, 'NÃO': 0, 'Não': 0, 'nao': 0}, inplace=True)
    
    for col in colunas:
        df[col] = df[col].apply(calcular_media_digitos)  # Aplicar a função de média dos dígitos
    return df


@avaliacaosecretaria_route.route('/gerar_graficos_completos_secretaria')
def gerar_graficos_completos_secretaria():
    graficos = []

    # Receber o nome do arquivo da URL
    filename = request.args.get('filename')
    
    if not filename:
        flash('Nenhum arquivo selecionado para gerar gráficos', 'danger')
        return redirect(url_for('avaliacaosecretaria.importar_planilhasecretaria'))
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        flash('Arquivo não encontrado', 'danger')
        return redirect(url_for('avaliacaosecretaria.importar_planilhasecretaria'))

    try:
        # Tentar ler o arquivo CSV e remover o BOM
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            secretaria = pd.read_csv(f, delimiter=';')

        # Renomear as colunas como no seu Colab
        secretaria.rename({
            'A qual programa esta vinculado(a)?': 'programa',
            'Ha quanto tempo voce e secretario(a) do programa?': 'tempo_programa',
            'Como voce avalia a infraestrutura da secretaria do programa': 'infraestrutura_programa',
            'Existem praticas de acompanhamento dos discentes regularmente matriculados no programa?': 'acompanhamento_discentes',
            'Em caso afirmativo, quais sao essas praticas?': 'praticas_discentes',
            'Existem praticas de acompanhamento dos egressos do programa?': 'acompanhamento_egresso',
            'Em caso afirmativo, quais sao essas praticas?': 'pratica_egresso',
            'Como sao armazenadas essas informacoes?': 'armazenadas',
            'O programa faz alguma analise das informacoes coletadas?': 'analise_informacoes',
            'O programa faz levantamento de dados dos egressos apenas para preenchimento da plataforma sucupira?': 'levantamento_egresso_apenas_capes',
            'O programa tem o habito de encaminhar mensagens ou mantem algum contato periodico com os egressos?': 'contato_mensagem_egressos',
            'Em caso afirmativo, com que frequencia?': 'frequencia_egresso',
            'Que tipo de informacoes sao encaminhadas?': 'informacaoes_encaminhadas_egresso',
            'e comum os egressos contactarem o programa para buscar informacoes sobre concursos e/ou empregos?': 'egressos_contato_emprego',
            'Voce acha necessario um sistema de acompanhamento de egressos?': 'sistema_acompanhamento_egressos',
            'Quais questoes considera importantes a serem abordadas sobre o acompanhamento dos egressos?': 'consideracoes_egressos',
            'Fique a vontade para dar sugestoes sobre o que considera importante no acompanhamento de egressos?': 'sugestoes'
        }, axis=1, inplace=True)

        # Mapeamento da coluna 'tempo_programa' para valores numéricos
        data = {
            'tempo_programa': [
                'Mais de 5 anos', 'Mais de 5 anos', 'Mais de 5 anos', 'Mais de 5 anos', 
                'Entre 1 e 2 anos', 'Mais de 5 anos', 'Mais de 5 anos', 'Mais de 5 anos',
                'Menos de 1 ano', 'Mais de 5 anos', 'Mais de 5 anos', 'Mais de 5 anos', 
                'Menos de 1 ano', 'Mais de 5 anos', 'Entre 3 e 4 anos', 'Mais de 5 anos', 
                'Mais de 5 anos', 'Entre 3 e 4 anos', 'Mais de 5 anos'
            ]
        }
        df = pd.DataFrame(data)

        # Definir o mapeamento para valores numéricos
        mapping = {
            'Mais de 5 anos': 6,
            'Entre 1 e 2 anos': 1.5,
            'Menos de 1 ano': 0.5,
            'Entre 3 e 4 anos': 3.5
        }

        # Aplicar o mapeamento à coluna
        df['tempo_programa_numeric'] = df['tempo_programa'].map(mapping)

        # Verificar a nova coluna numérica
        print(df[['tempo_programa', 'tempo_programa_numeric']])
        secretaria['tempo_programa_numeric'] = secretaria['tempo_programa'].map(mapping)

        # Verificar se a nova coluna numérica foi criada corretamente
        print(secretaria[['tempo_programa', 'tempo_programa_numeric']].head())

        # Verificar se as colunas necessárias estão presentes
        required_columns = ['tempo_programa_numeric', 'infraestrutura_programa']
        
        # Aplicar a função de cálculo da média dos dígitos, se aplicável
        secretaria = limpar_e_converter_para_numeric(secretaria, required_columns)
        print(secretaria.columns)

        # Criar novas colunas calculadas (médias)
        secretaria['Media_Programa'] = secretaria[['tempo_programa_numeric', 'infraestrutura_programa']].mean(axis=1)

        # Gráfico de barras - Avaliação do tempo no programa
        fig1, ax1 = plt.subplots()
        ax1.bar(secretaria['tempo_programa_numeric'].value_counts().index, 
                secretaria['tempo_programa_numeric'].value_counts())
        ax1.set_title('Distribuição de Tempo de Vinculação ao Programa')
        ax1.set_xlabel('Tempo no Programa (anos)')
        ax1.set_ylabel('Número de Secretarias')
        img1 = io.BytesIO()
        plt.savefig(img1, format='png')
        img1.seek(0)
        graficos.append(base64.b64encode(img1.getvalue()).decode('utf-8'))
        plt.close(fig1)

        # Histograma de Infraestrutura
        fig2, ax2 = plt.subplots()
        ax2.hist(secretaria['infraestrutura_programa'], bins=10, color='skyblue')
        ax2.set_title('Distribuição de Infraestrutura')
        ax2.set_xlabel('Infraestrutura do Programa')
        ax2.set_ylabel('Número de Secretarias')
        img2 = io.BytesIO()
        plt.savefig(img2, format='png')
        img2.seek(0)
        graficos.append(base64.b64encode(img2.getvalue()).decode('utf-8'))
        plt.close(fig2)

        # Boxplot - Sistema de Acompanhamento de Egressos vs Tempo no Programa
        # Boxplot - Sistema de Acompanhamento de Egressos vs Tempo no Programa
        fig3, ax3 = plt.subplots()

        # Verificar se os dados estão disponíveis e não têm valores faltantes
        if secretaria['sistema_acompanhamento_egressos'].notna().sum() > 0 and secretaria['tempo_programa_numeric'].notna().sum() > 0:
            sns.boxplot(x='sistema_acompanhamento_egressos', y='tempo_programa_numeric', data=secretaria, ax=ax3)
            ax3.set_title('Sistema de Acompanhamento de Egressos vs Tempo no Programa')
            ax3.set_xlabel('Sistema de Acompanhamento de Egressos')
            ax3.set_ylabel('Tempo no Programa (anos)')
            plt.xticks(rotation=45)
            
            img3 = io.BytesIO()
            plt.savefig(img3, format='png')
            img3.seek(0)
            graficos.append(base64.b64encode(img3.getvalue()).decode('utf-8'))
            plt.close(fig3)
        else:
            flash("Dados insuficientes para gerar o boxplot do Sistema de Acompanhamento de Egressos.", "warning")



        # Mapa de calor - Correlação entre variáveis
        fig4, ax4 = plt.subplots(figsize=(10, 7))
        sns.heatmap(secretaria[['tempo_programa_numeric', 'infraestrutura_programa']].corr(), 
                    annot=True, cmap='coolwarm', linewidths=0.4, ax=ax4)
        ax4.set_title('Mapa de Calor das Correlações')
        img4 = io.BytesIO()
        plt.savefig(img4, format='png')
        img4.seek(0)
        graficos.append(base64.b64encode(img4.getvalue()).decode('utf-8'))
        plt.close(fig4)

        # Gráfico de violino - Distribuição da Média de Qualidade do Programa
        fig5, ax5 = plt.subplots(figsize=(10, 6))  # Definir o tamanho do gráfico
        sns.violinplot(y=secretaria['Media_Programa'], ax=ax5, color='lightgreen')
        ax5.set_title('Distribuição da Média de Qualidade do Programa', fontsize=16)
        ax5.set_ylabel('Média de Avaliação', fontsize=14)

        # Adicionar anotação com a média
        media_valor = secretaria['Media_Programa'].mean()
        ax5.text(0.1, media_valor + 0.2, f'Média: {media_valor:.2f}', color='black', fontsize=12)

        plt.tight_layout()

        # Salvar o gráfico em buffer
        img5 = io.BytesIO()
        plt.savefig(img5, format='png')
        img5.seek(0)
        graficos.append(base64.b64encode(img5.getvalue()).decode('utf-8'))
        plt.close(fig5)

    except Exception as e:
        flash(f"Erro ao processar o arquivo: {e}", "danger")
        return redirect(url_for('avaliacaosecretaria.importar_planilhasecretaria'))

    # Retornar o template com os gráficos gerados
    return render_template('dashboard_secretaria.html', graficos=graficos)

# Inicializar o analisador de sentimentos
nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Função para processar o sentimento
def analisar_sentimento(texto):
    return sid.polarity_scores(texto)




def analisar_sentimentos_secretaria(secretaria):

        secretaria.rename({
        'sistema_acompanhamento_egressos': 'Sentimento_acompanhamento',
        'consideracoes_egressos': 'Sentimento_egressos',
        'sugestoes' : 'Suegestao'
        }, axis=1, inplace=True)

        # Remover linhas vazias das colunas de comentários
        df_comentarios = secretaria[['sistema_acompanhamento_egressos', 'consideracoes_egressos','sugestoes']].dropna(how='all')

        # Aplicar a função de sentimento para cada comentário
        df_comentarios['Sent_acompanhamento'] = df_comentarios['sistema_acompanhamento_egressos'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)
        df_comentarios['Sent_egressos'] = df_comentarios['consideracoes_egressos'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)
        df_comentarios['Sent_sugestoes'] = df_comentarios['sugestoes'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)

        # Quebrar os resultados do VADER (dicionário) em colunas separadas
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_acompanhamento']).add_prefix('Programa_'))
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_egressos']).add_prefix('Pro_Reitoria_'))
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_sugestoes']).add_prefix('Pro_Reitoria_'))

        # Calcular a média dos sentimentos
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()
        media_sentimentos_prppg = df_comentarios['Pro_Reitoria_compound'].mean()

        # Contar sentimentos negativos, positivos e neutros
        total_negativos_programa = len(df_comentarios[df_comentarios['Acompanhamento_compound'] < 0])
        total_positivos_programa = len(df_comentarios[df_comentarios['Acompanhamento_compound'] > 0])
        total_neutros_programa = len(df_comentarios[df_comentarios['Acompanhamento_compound'] == 0])

        # Criar gráfico de barras para distribuição de sentimentos
        dados_sentimentos = {'Negativos': total_negativos_programa, 'Positivos': total_positivos_programa, 'Neutros': total_neutros_programa}
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.bar(dados_sentimentos.keys(), dados_sentimentos.values(), color=['red', 'green', 'gray'])
        ax.set_title('Distribuição de Sentimentos sobre o Programa de Pós-Graduação')
        ax.set_xlabel('Tipo de Sentimento')
        ax.set_ylabel('Número de Comentários')

       # Salvar gráfico em buffer
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)

        # Retornar gráfico como base64
        grafico_sentimentos = base64.b64encode(img.getvalue()).decode('utf-8')
        return grafico_sentimentos


def normalize_column_names(df):
    df.columns = [
        unicodedata.normalize('NFKD', col)
        .encode('ascii', 'ignore')
        .decode('utf-8')
        .strip()
        .lower()
        .replace('  ', ' ')
        .replace(' ', '_')
        .replace('[', '')
        .replace(']', '')
        for col in df.columns
    ]
    return df


def gerar_estatisticas_descritivas(df):
    # Calcula as estatísticas descritivas e converte para HTML
    estatisticassecretaria = df.describe().transpose()
    estatisticassecretaria_html = estatisticassecretaria.to_html(classes="table table-striped")
    return estatisticassecretaria_html


@avaliacaosecretaria_route.route('/executar_analise')
def executar_analise():
    tipo = request.args.get('tipo')
    secretaria = pd.read_csv('uploads/secretaria.csv', delimiter=';')
    secretaria = renomear_colunas(secretaria)
    secretaria = limpar_dados(secretaria)

    graficos = []
    estatisticas_html = gerar_estatisticas_descritivas(secretaria)

    # Variáveis padrão para o template
    Media_Programa = None
    grafico_sentimentos_ingresso = None
    mse_otimizado = None
    recomendacoes_por_programa = {}  # Inicializado como dicionário vazio

    # Análise de Sentimento
    if tipo == 'sentimento':
        grafico_sentimentos_ingresso = aplicar_analise_sentimentos(secretaria)
        Media_Programa = secretaria['Media_Programa'].mean() if 'Media_Programa' in secretaria else None

    # Análise de Clustering
    elif tipo == 'clustering':
        grafico = aplicar_clustering(secretaria)
        graficos.append(grafico)

    # Análise de Regressão
    elif tipo == 'regressao':
        mse_otimizado = aplicar_regressao(secretaria)

    return render_template(
        'resultadosecretaria.html', 
        media_programa=Media_Programa,
        grafico_sentimentos_ingresso=grafico_sentimentos_ingresso,
        mse_otimizado=mse_otimizado,
        recomendacoes_por_programa=recomendacoes_por_programa,  # Passa o dicionário vazio se não houver dados
        estatisticas=estatisticas_html
    )


@avaliacaosecretaria_route.route('/visualizar_resultados', methods=['GET'])
def visualizar_resultados():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/secretaria.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('secretaria.importar_iplanilhasecretaria'))

        discentecurso = pd.read_csv(file_path, delimiter=';')

        # Verificar se os dados têm distribuição suficiente para treinamento
        print(secretaria.describe())  # Verificar estatísticas gerais para cada coluna

        # Avaliar os sentimentos do Programa de Pós-Graduação
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()

        # Gráfico de barras de sentimentos por ano de ingresso
        # Ajustar o gráfico com rotação dos rótulos no eixo X
        # Aumentar o tamanho da imagem com figsize
      # Aumentar o tamanho da imagem com figsize
        fig, ax = plt.subplots(figsize=(14, 8))  # Ajuste os valores para o tamanho desejado
        secretaria['Media_Programas'].plot(kind='bar', ax=ax)
        plt.title('Media_Programa')

        # Rotacionar os rótulos no eixo X, se necessário
        plt.xticks(rotation=90)
        plt.tight_layout()

        # Salvar gráfico em memória para exibir
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        grafico_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
        graficos.append(grafico_base64)


        # Resultados da RandomForest otimizada
        mse_otimizado = mean_squared_error(y_test, y_pred_best)
        grafico_sentimentos = base64.b64encode(img.getvalue()).decode('utf-8')

        # Exibir gráficos e resultados na página
        return render_template('resultadosecretaria.html', 
                               grafico_sentimentos=grafico_sentimentos,
                               mse_otimizado=mse_otimizado,
                               media_programa=media_sentimentos_programa)

    except Exception as e:
        flash(f"Erro ao gerar recomendações: {str(e)}", 'danger')
        return redirect(url_for('secretaria.importar_planilhasecretaria'))

########################
def aplicar_analise_sentimentos(secretaria):
    # Verificar se as colunas originais estão presentes antes de renomeá-las
    required_columns = ['sistema_acompanhamento_egressos', 'consideracoes_egressos', 'sugestoes']
    missing_columns = [col for col in required_columns if col not in secretaria.columns]

    # Exibir uma mensagem de erro se alguma coluna estiver faltando
    if missing_columns:
        flash(f"Colunas faltando no arquivo: {', '.join(missing_columns)}", 'danger')
        return None  # Interromper a execução se houver colunas faltando

    # Continuar com a análise de sentimentos se todas as colunas estiverem presentes
    secretaria.rename({
        'sistema_acompanhamento_egressos': 'Sentimento_acompanhamento',
        'consideracoes_egressos': 'Sentimento_egressos',
        'sugestoes': 'Sugestao'
    }, axis=1, inplace=True)

    # Remover linhas vazias das colunas de comentários
    df_comentarios = secretaria[['Sentimento_acompanhamento', 'Sentimento_egressos', 'Sugestao']].dropna(how='all')

    # Aplicar a função de sentimento para cada comentário
    df_comentarios['Sent_acompanhamento'] = df_comentarios['Sentimento_acompanhamento'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)
    df_comentarios['Sent_egressos'] = df_comentarios['Sentimento_egressos'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)
    df_comentarios['Sent_sugestoes'] = df_comentarios['Sugestao'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)

    # Expandir os resultados do VADER em colunas separadas e verificar a criação das colunas
    try:
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_acompanhamento']).add_prefix('Programa_'))
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_egressos']).add_prefix('Pro_Reitoria_'))
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_sugestoes']).add_prefix('Sugestao_'))
    except Exception as e:
        flash(f"Erro ao expandir os resultados de sentimento: {e}", 'danger')
        return None

    # Verificar se as colunas expandidas estão presentes antes de calcular as médias
    if 'Programa_compound' in df_comentarios.columns:
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()
    else:
        media_sentimentos_programa = None

    if 'Pro_Reitoria_compound' in df_comentarios.columns:
        media_sentimentos_prppg = df_comentarios['Pro_Reitoria_compound'].mean()
    else:
        media_sentimentos_prppg = None

    # Contar sentimentos negativos, positivos e neutros (para Programa_compound)
    total_negativos_programa = len(df_comentarios[df_comentarios.get('Programa_compound', pd.Series()) < 0])
    total_positivos_programa = len(df_comentarios[df_comentarios.get('Programa_compound', pd.Series()) > 0])
    total_neutros_programa = len(df_comentarios[df_comentarios.get('Programa_compound', pd.Series()) == 0])

    # Criar gráfico de barras para distribuição de sentimentos
    dados_sentimentos = {'Negativos': total_negativos_programa, 'Positivos': total_positivos_programa, 'Neutros': total_neutros_programa}
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(dados_sentimentos.keys(), dados_sentimentos.values(), color=['red', 'green', 'gray'])
    ax.set_title('Distribuição de Sentimentos sobre o Programa de Pós-Graduação')
    ax.set_xlabel('Tipo de Sentimento')
    ax.set_ylabel('Número de Comentários')

    # Salvar o gráfico em buffer
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    # Retornar o gráfico como base64
    grafico_sentimentos = base64.b64encode(img.getvalue()).decode('utf-8')
    return grafico_sentimentos

################################################################################################
@avaliacaosecretaria_route.route('/analisar_dados_ia', methods=['GET'])
def analisar_dados_ia():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/secretaria.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaosecretaria.importar_planilhasecretaria'))

        # Carregar os dados do CSV
        secretaria = pd.read_csv(file_path, delimiter=';')

        # Renomear as colunas como no seu Colab
        secretaria.rename({
            'A qual programa esta vinculado(a)?':'programa',
            'Ha quanto tempo voce e secretario(a) do programa?':'tempo_programa',
            'Como voce avalia a infraestrutura da secretaria do programa': 'infraestrutura_programa',
            'Existem praticas de acompanhamento dos discentes regularmente matriculados no programa?':'acompanhamento_discentes',
            'Em caso afirmativo, quais sao essas praticas?':'praticas_discentes',
            'Existem praticas de acompanhamento dos egressos do programa?':'acompanhamento_egresso',
            'Em caso afirmativo, quais sao essas praticas?':'pratica_egresso',
            'Como sao armazenadas essas informacoes?':'armazenadas',
            'O programa faz alguma analise das informacoes coletadas?':'analise_informacoes',
            'O programa faz levantamento de dados dos egressos apenas para preenchimento da plataforma sucupira?':'levantamento_egresso_apenas_capes',
            'O programa tem o habito de encaminhar mensagens ou mantem algum contato periodico com os egressos?':'contato_mensagem_egressos',
            'Em caso afirmativo, com que frequencia?':'frequencia_egresso',
            'Que tipo de informacoes sao encaminhadas?':'informacaoes_encaminhadas_egresso',
            'e comum os egressos contactarem o programa para buscar informacoes sobre concursos e/ou empregos?':'egressos_contato_emprego',
            'Voce acha necessario um sistema de acompanhamento de egressos?':'sistema_acompanhamento_egressos',
            'Quais questoes considera importantes a serem abordadas sobre o acompanhamento dos egressos?':'consideracoes_egressos',
            'Fique a vontade para dar sugestoes sobre o que considera importante no acompanhamento de egressos?':'sugestoes'

        }, axis=1, inplace=True)

        # 1. Garantir que todas as colunas são numéricas
        colunas_programa = ['tempo_programa', 'infraestrutura_programa']
        colunas_acompanhamento = ['acompanhamento_discentes', 'praticas_discentes', 'pratica_egresso',
                                'analise_informacoes']
        colunas_egressos = ['levantamento_egresso_apenas_capes','contato_mensagem_egressos', 'sistema_acompanhamento_egressos','consideracoes_egressos','sugestoes']
    
  

       # Converter as colunas para numéricas
        def converter_para_numerico(df, colunas):
            for coluna in colunas:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
            return df

        secretaria = converter_para_numerico(secretaria, colunas_programa + colunas_acompanhamento + colunas_egressos)

        # Agrupar os dados por programa
        agrupado_por_programa = secretaria.groupby('programa')

        # Variáveis para armazenar as recomendações por programa
        recomendacoes_por_programa = {}

        for programa, dados_programa in agrupado_por_programa:
            if len(dados_programa) < 2:
                continue  # Pular grupos com poucos dados para evitar erro no treino/teste

            # 2. Criar as médias por grupo de avaliação
            media_qualidade = dados_programa['tempo_programa_numerics'].mean()
            media_infraestrutura = dados_programa['Infraestrutura geral'].mean()

            # Verificar sentimentos nos comentários (se disponíveis)
            df_comentarios = dados_programa[['sugestoes']].dropna()
            media_sentimentos_programa = None  # valor padrão se não houver comentários

            if not df_comentarios.empty:
                df_comentarios['Sentimento_Programa_Score'] = df_comentarios['sugestoes'].apply(lambda x: analisar_sentimento(str(x))['compound'])
                media_sentimentos_programa = df_comentarios['Sentimento_Programa_Score'].mean()

            # 3. RandomForest e XGBoost para prever a qualidade das aulas
            X = dados_programa.drop(['tempo_programa_numerics'], axis=1)  # Variáveis independentes
            y = dados_programa['tempo_programa_numerics']  # Variável dependente

            # Transformar variáveis categóricas em dummies
            X = pd.get_dummies(X, drop_first=True)

            # Substituir caracteres especiais nos nomes das colunas
            X.columns = X.columns.str.replace(r'[\[\]<]', '', regex=True)

            # Dividir o conjunto de dados em treino e teste, se houver dados suficientes
            if len(X) < 2:
                mse_rf = None
                mse_xgb = None
            else:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                # Treinar o modelo RandomForest
                 # Treinar o modelo RandomForest
                rf_model = RandomForestRegressor(random_state=42)
                rf_model.fit(X_train, y_train)
                y_pred_rf = rf_model.predict(X_test)
                mse_rf = mean_squared_error(y_test, y_pred_rf)

                # Substituir XGBRegressor por GradientBoostingRegressor
                gb_model = GradientBoostingRegressor(random_state=42)
                gb_model.fit(X_train, y_train)
                y_pred_gb = gb_model.predict(X_test)
                mse_gb = mean_squared_error(y_test, y_pred_gb)

            # 4. Gerar recomendações com base nos resultados
            recomendacoes = []
            if mse_rf is not None and mse_rf > 1.0:
                recomendacoes.append(f"Aprimorar os métodos de ensino e avaliação para melhorar a qualidade das aulas no programa {programa}.")

            if media_sentimentos_programa is not None and media_sentimentos_programa < 0.0:
                recomendacoes.append(f"Investir em ações de melhoria na satisfação dos alunos no programa {programa}.")
            
            recomendacoes.append(f"Aumentar os esforços de internacionalização no programa {programa} com base nos baixos índices de proficiência em inglês.")
            
            # Adicionar as recomendações ao dicionário por programa
            recomendacoes_por_programa[programa] = {
                'mse_rf': mse_rf,
                'mse_xgb': mse_xgb,
                'media_sentimentos_programa': media_sentimentos_programa,
                'recomendacoes': recomendacoes
            }

        # Renderizar o template com as recomendações por programa
        return render_template('recomendacaosecretaria.html', recomendacoes_por_programa=recomendacoes_por_programa)

    except Exception as e:
        flash(f"Erro ao processar os dados: {e}", 'danger')
        return redirect(url_for('avaliacaosecretaria.importar_planilhasecretaria'))
    
####################################################################################################3333333
@avaliacaosecretaria_route.route('/exibir_recomendacoes_programasecretaria', methods=['GET'])
def exibir_recomendacoes_programasecretaria():
    try:
        file_path = os.path.join(UPLOAD_FOLDER, 'secretaria.csv')
        if not os.path.exists(file_path):
            flash('Arquivo "secretaria.csv" não encontrado na pasta uploads.', 'danger')
            return redirect(url_for('secretaria.importar_planilhacoordenador'))
        
        # Carregar o DataFrame do CSV
        secretaria = pd.read_csv(file_path, delimiter=';')
        
        # Renomear e limpar dados
        secretaria = renomear_colunas(secretaria)
        if secretaria is None:
            raise ValueError("Erro ao renomear colunas. Verifique a função 'renomear_colunas'.")

        secretaria = limpar_dados(secretaria)
        if secretaria is None:
            raise ValueError("Erro ao limpar dados. Verifique a função 'limpar_dados'.")

        # Calcular médias por grupo
        colunas_programa = ['tempo_programa', 'infraestrutura_programa']
        colunas_acompanhamento = ['acompanhamento_discentes', 'praticas_discentes', 'pratica_egresso',
                               'analise_informacoes']
        colunas_egressos = ['levantamento_egresso_apenas_capes','contato_mensagem_egressos', 'sistema_acompanhamento_egressos','consideracoes_egressos','sugestoes']
    

        def converter_para_numerico(df, colunas):
            for coluna in colunas:
                if coluna in df.columns:
                    df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
            return df

        secretaria = converter_para_numerico(secretaria, 
                                              colunas_programa + colunas_acompanhamento + 
                                              colunas_egressos )

        secretaria['Media_Qualidade'] = secretaria[colunas_programa].mean(axis=1)
        secretaria['Media_Acompanhamento'] = secretaria[colunas_acompanhamento].mean(axis=1)
        secretaria['Media_Egressos'] = secretaria[colunas_egressos].mean(axis=1)
       

        # Agrupar por programa e calcular médias
        df_por_programa = secretaria.groupby('programa').agg({
            'Media_Qualidade': 'mean',
            'Media_Acompanhamento': 'mean',
            'Media_Egressos': 'mean'
        }).reset_index()

        # Função para gerar recomendações por programa
        def gerar_recomendacoes_programa(df_agrupado):
            recomendacoes_por_programa = {}
            for _, row in df_agrupado.iterrows():
                programa = row['programa']
                recomendacoes = []

                # Regras de recomendações
                if row['Media_Qualidade'] < 3:
                    recomendacoes.append("Melhorar a qualidade das aulas e do material didático.")
                
                if row['Media_Acompanhamento'] < 3:
                    recomendacoes.append("Reavaliar o acompanhamento de discentes e egressos")
                
                if row['Media_Infraestrutura'] < 3:
                    recomendacoes.append("Investir em infraestrutura, incluindo laboratórios e insumos de pesquisa.")
                
                if row['Media_Egressos'] < 3:
                    recomendacoes.append("Aprimorar o relacionamento egressos.")
                
               
            return recomendacoes_por_programa

        # Gerar recomendações para cada programa
        recomendacoes_programa = gerar_recomendacoes_programa(df_por_programa)

        # Passar recomendações para o template
        return render_template('recomendacaosecretaria.html', recomendacoes=recomendacoes_programa)

    except Exception as e:
        flash(f"Erro ao gerar recomendações: {e}", 'danger')
        return redirect(url_for('avaliacaosecretaria.importar_planilhasecretaria'))


# Rota para análise de clustering
def aplicar_clustering(secretaria, num_clusters=3):
    # Garantir que as colunas estejam livres de valores não numéricos
    secretaria[['tempo_programa', 'Infraestrutura_geral']] = secretaria[['tempo_programa', 'Infraestrutura_geral']].apply(pd.to_numeric, errors='coerce')
    secretaria.dropna(subset=['tempo_programa', 'Infraestrutura_geral'], inplace=True)

    # Aplicar KMeans
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    secretaria['Cluster'] = kmeans.fit_predict(secretaria[['tempo_programa', 'Infraestrutura_geral']])
    
    # Gráfico de dispersão
    fig, ax = plt.subplots()
    sns.scatterplot(x='infraestrutura_programa', y='tempo_programa', hue='Cluster', data=secretaria, palette='viridis', ax=ax)
    ax.set_title('Clusters de Alunos com Base nas Avaliações')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode('utf-8')

# Função para análise de regressão
def aplicar_regressao(secretaria):
    # Ensure numeric values in relevant columns
    secretaria[['Infraestrutura_geral', 'acompanhamento_egresso', 'tempo_programa']] = secretaria[['Infraestrutura_geral', 'acompanhamento_egresso', 'tempo_programa']].apply(pd.to_numeric, errors='coerce')
    secretaria.dropna(subset=['Infraestrutura_geral', 'acompanhamento_egresso', 'tempo_programa'], inplace=True)

    # Define features and target
    X = secretaria[['Infraestrutura_geral', 'acompanhamento_egresso']]
    y = secretaria['tempo_programa']
    
    # Debugging output
    print("Features for regression analysis (first rows):", X.head())
    print("Target variable for regression (first rows):", y.head())

    # Split data and train model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    # Calculate MSE and print for debugging
    mse = mean_squared_error(y_test, y_pred)
    print("Mean Squared Error of Regression:", mse)
    print("Predictions vs Actual values:", list(zip(y_test, y_pred)))

    return f'MSE da regressão: {mse}'
