import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os
import unicodedata
import nltk
import numpy as np
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Blueprint setup
discente_route = Blueprint('discente', __name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Utility function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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


# Função para substituir "Sim"/"Não" e valores problemáticos
def limpar_dados(df):
    df.replace({
        "Sem condições de avaliar": np.nan,
        "Sem condiÃ§Ãµes de avaliar": np.nan,
        "Sem condicoes de avaliar": np.nan,
        "Não se aplica": np.nan
    }, inplace=True)
    return df

# Função para substituir valores de 'Sim' e 'Não' por 1 e 0
def substituir_sim_nao(valor):
    if isinstance(valor, str):
        valor = valor.strip().lower()
        if "sim" or "Sim" in valor:
            return 1
        elif "não" in valor or "nao" or "Nao" in valor:
            return 0
    return np.nan

# Lista de colunas para converter 'Sim'/'Não'
colunas_sim_nao_corrigido = [
    'Voce recebe bolsa de pos-graduacao?',
    'Para a realizacao de seu projeto de pesquisa houve algum tipo de captacao de recurso externo (exceto bolsa)? ',
    'Producao de inovacao tecnologica e uma prioridade em seu programa de pos-graduacao?',
    'Voce acredita que sua linha de pesquisa se destaca pela producao de inovacao tecnologica?',
    'Voce ja depositou alguma patente proveniente de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?',
    'Producao de tecnologias de APLICAcaO SOCIAL e uma prioridade em seu programa de pos-graduacao?',
    'Alguma tecnologia de aplicacao social ja foi criada como resultado de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?',
    'Voce ja apresentou algum resultado de sua pesquisa em algum evento voltado para a COMUNIDADE, ou pretende apresentar?',
    'Voce ja apresentou algum resultado de sua pesquisa em algum evento CIENTiFICO, ou pretende apresentar?'
]

# Carregar o arquivo CSV antes de utilizar o discentecurso
file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
if os.path.exists(file_path):
    discentecurso = pd.read_csv(file_path, delimiter=';')
    discentecurso[colunas_sim_nao_corrigido] = discentecurso[colunas_sim_nao_corrigido].applymap(substituir_sim_nao)
else:
    raise FileNotFoundError("O arquivo discente.csv não foi encontrado no diretório uploads.")


def renomear_colunas(discentecurso):
     # Renomear as colunas como no seu Colab
        discentecurso.rename({
            'Qual o seu nivel de formacao?':'formacao',
            'Qual o seu ano de ingresso?': 'ingresso',
            'A qual programa esta vinculado?': 'programa',
            'Como voce avalia a qualidade das aulas e do material utilizado?[Qualidade das aulas]':'Qualidade_aulas',
            'Como voce avalia a qualidade das aulas e do material utilizado? [Material didatico utilizado nas disciplinas]':'Material_didatico',
            'Como voce avalia a qualidade das aulas e do material utilizado?  [Acervo disponivel para consulta]':'Acervo_disponivel',
            'Como voce avalia a  infraestrutura do programa?[Infraestrutura geral]':'Infraestrutura_geral',
            'Como voce avalia a  infraestrutura do programa?[Laboratorios de pesquisa/Salas de estudo]':'laboratorio_sala',
            'Como voce avalia a  infraestrutura do programa?  [Insumos para pesquisa]':'insumos_pesquisa',
            'Como voce avalia o relacionamento entre voce e: [os colegas]':'Relacionamento_colegas',
            'Como voce avalia o relacionamento entre voce e: [a comissao orientadora]':'Relacionamento_orientador',
            'Como voce avalia o relacionamento entre voce e: [a comissao coordenadora]':'Relacionamento_coordenador',
            'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'Relacionamento_secretaria',
            'Como voce avalia a gestão do programa? [Processo de gestao/Administrativo do Programa]':'processo_programa',
            'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizacao_programa',
            'Como voce avalia o seu conhecimento acerca: [do seu papel enquanto aluno]':'Seu_conhecimento',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Interno do Programa]':'regimento_interno',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Geral da Pos-Graduacao]':'regimento_geral',
            'Como voce avalia o seu conhecimento acerca: [das normas da Capes]':'normas_CAPES',
            'Como voce avalia o seu conhecimento acerca: [do processo de avaliacao da Capes]':'processo_CAPES',
            'Em relacao ao seu PROJETO DE PESQUISA, voce esta:':'projeto pesquisa',
            'Em relacao a sua PRODUcaO CIENTiFICA, voce esta:':'producao cientifica',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia social?':'pesquisa_relevancia_social',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia economica?':'pesquisa relevancia economica',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia ambiental?':'pesquisa relevancia ambiental',
            'Voce acredita que sua pesquisa promove avanco cientifico?':'pesquisa avanço cientifico',
            'O seu Programa possui visao, missao e objetivos claros?':'visao-missao-objetivos',
            'Voce acredita que sua pesquisa esta alinhada com o objetivo e missao de seu Programa?':'pesquisa alinhada visao-missao-objetivos',
            'Voce recebe bolsa de pos-graduacao?':'possui_bolsa',
            'Para a realizacao de seu projeto de pesquisa houve algum tipo de captacao de recurso externo (exceto bolsa)? ':'captacao_recurso_externo',
            'Producao de inovacao tecnologica e uma prioridade em seu programa de pos-graduacao?':'producao_inovacao_tecnologica',
            'Voce acredita que sua linha de pesquisa se destaca pela producao de inovacao tecnologica?':'linha pesquisa inovacao tecnologica',
            'Voce ja depositou alguma patente proveniente de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?':'patente linha pesquisa',
            'Produção de tecnologias de APLICAcaO SOCIAL e uma prioridade em seu programa de pos-graduacao?':'tecnologia de aplicacao social',
            'Alguma tecnologia de aplicacao social ja foi criada como resultado de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?':'projeto de pesquisa tecnologia aplicacao social',
            'Voce ja apresentou algum resultado de sua pesquisa em algum evento voltado para a COMUNIDADE, ou pretende apresentar?':'evento_comunidade',
            'Voce ja apresentou algum resultado de sua pesquisa em algum evento CIENTiFICO, ou pretende apresentar?':'resultado_evento_cientifico',
            'Sua pesquisa podera gerar solucoes para os problemas que a sociedade enfrenta ou vira a enfrentar?':'pesquisa solucoes sociedade',
            'No momento, ha interesse por parte do seu Programa de Pos-Graduacao em iniciar um processo de Internacionalizacao?':'interesse_internacionalizacao',
            'Voce se sente preparado para a internacionalizacao do seu Programa de Pos-Graduacao? ':'preparado_internacionalizacao',
            'Voce entende que o seu Programa de Pos-Graduacao esta preparado para a internacionalizacao?':'PRPPG_preparado_internacionalizacao',
            'Seu projeto de pesquisa possui parcerias com instituicoes internacionais de pesquisa ou ensino?':'projeto_parceria_internacional',
            'Qual o seu nivel de proficiencia em lingua inglesa?':'proficiencia_ingles',
            'Gostaria de adicionar algum comentario referente seu Programa de Pos-Graduacao?':'comentario_programa',
            'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?':'comentario_PRPPG'
        }, axis=1, inplace=True)
        return discentecurso # Ensure the modified DataFrame is returned

# Função para substituir valores de 'Sim' e 'Não' por 1 e 0
def substituir_sim_nao(valor):
    if isinstance(valor, str):
        valor = valor.strip().lower()
        if "sim" in valor:
            return 1
        elif "não" in valor or "nao" in valor:
            return 0
    return np.nan

# Limpeza de colunas com valores 'Sim'/'Não'
def limpar_e_converter_sim_nao(discentecurso, colunas):
    for col in colunas:
        if col in discentecurso.columns:
            discentecurso[col] = discentecurso[col].apply(substituir_sim_nao)
    return discentecurso


# Rota para importar o arquivo CSV
@discente_route.route('/importar_discente', methods=['GET', 'POST'])
def importar_discente():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash('Arquivo inválido. Por favor, envie um arquivo CSV.', 'danger')
            return redirect(request.url)

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        return redirect(url_for('discente.gerar_graficos', filename=file.filename))
    
    return render_template('importar_discente.html')


# Rota para gerar gráficos
@discente_route.route('/gerar_graficos')
def gerar_graficos():
    graficos = []
    filename = request.args.get('filename')
    
    if not filename:
        flash('Nenhum arquivo selecionado para gerar gráficos', 'danger')
        return redirect(url_for('discente.importar_discente'))
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        flash('Arquivo não encontrado', 'danger')
        return redirect(url_for('discente.importar_discente'))

    try:
        # Carregar e renomear colunas
        discentecurso = pd.read_csv(file_path, delimiter=';')
        discentecurso = renomear_colunas(discentecurso)

        # Limpeza e conversão de valores problemáticos
        discentecurso = limpar_dados(discentecurso)

        # Converter as colunas necessárias para numérico
        required_columns = ['Qualidade_aulas', 'Material_didatico', 'Infraestrutura_geral']
        discentecurso[required_columns] = discentecurso[required_columns].apply(pd.to_numeric, errors='coerce')

        # Verificar se as colunas necessárias para calcular a média estão presentes
        if all(col in discentecurso.columns for col in required_columns):
            discentecurso['Media_Qualidade_Aulas'] = discentecurso[required_columns].mean(axis=1)
        else:
            missing_cols = [col for col in required_columns if col not in discentecurso.columns]
            flash(f"As colunas necessárias para o cálculo da média estão ausentes: {missing_cols}", "danger")
            return redirect(url_for('discente.importar_discente'))
        
        # Estatísticas descritivas
           # Estatísticas descritivas
        estatisticas_html = gerar_estatisticas_descritivas(discentecurso)

        # Gerar gráfico - Exemplo: Distribuição de Nível de Proficiência em Inglês
        fig, ax = plt.subplots()
        ax.hist(discentecurso['proficiencia_ingles'].dropna(), bins=10, color='skyblue')
        ax.set_title('Distribuição de Nível de Proficiência em Inglês')
        ax.set_xlabel('Nível de Proficiência')
        ax.set_ylabel('Número de Alunos')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)

            # Gráfico de violino para a Média de Qualidade das Aulas
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.violinplot(y=discentecurso['Media_Qualidade_Aulas'], ax=ax, color='lightgreen')

        # Título e rótulos
        ax.set_title('Distribuição da Média de Qualidade das Aulas', fontsize=16)
        ax.set_ylabel('Média de Avaliação', fontsize=14)

        # Adicionar anotação com a média
        media_valor = discentecurso['Media_Qualidade_Aulas'].mean()
        ax.text(0.1, media_valor + 0.2, f'Média: {media_valor:.2f}', color='black', fontsize=12)

        # Ajustar layout e salvar o gráfico em buffer
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)
   

        # Histograma de Proficiência em Inglês
        fig2, ax2 = plt.subplots()
        ax2.hist(discentecurso['proficiencia_ingles'], bins=10, color='skyblue')
        ax2.set_title('Distribuição de Nível de Proficiência em Inglês')
        ax2.set_xlabel('Nível de Proficiência')
        ax2.set_ylabel('Número de Alunos')
        img2 = io.BytesIO()
        plt.savefig(img2, format='png')
        img2.seek(0)
        graficos.append(base64.b64encode(img2.getvalue()).decode('utf-8'))
        plt.close(fig2)

        # Boxplot de Formação vs Qualidade das Aulas
        fig3, ax3 = plt.subplots()
        sns.boxplot(x='formacao', y='Qualidade_aulas', data=discentecurso, ax=ax3)
        ax3.set_title('Nível de Formação vs Qualidade das Aulas')
        ax3.set_xlabel('Nível de Formação')
        ax3.set_ylabel('Qualidade das Aulas')
        plt.xticks(rotation=45)
        img3 = io.BytesIO()
        plt.savefig(img3, format='png')
        img3.seek(0)
        graficos.append(base64.b64encode(img3.getvalue()).decode('utf-8'))
        plt.close(fig3)

        # Gráfico de linha - Tendência da Qualidade das Aulas ao longo dos anos
        fig4, ax4 = plt.subplots()
        sns.lineplot(x='ingresso', y='Qualidade_aulas', data=discentecurso, ax=ax4)
        ax4.set_title('Tendência da Qualidade das Aulas ao Longo dos Anos')
        ax4.set_xlabel('Ano de Ingresso')
        ax4.set_ylabel('Qualidade das Aulas')
        img4 = io.BytesIO()
        plt.savefig(img4, format='png')
        img4.seek(0)
        graficos.append(base64.b64encode(img4.getvalue()).decode('utf-8'))
        plt.close(fig4)

        # Mapa de calor - Correlação entre variáveis
        fig5, ax5 = plt.subplots(figsize=(10, 7))
        sns.heatmap(discentecurso[['Qualidade_aulas', 'proficiencia_ingles']].corr(), 
                    annot=True, cmap='coolwarm', linewidths=0.4, ax=ax5)
        ax5.set_title('Mapa de Calor das Correlações')
        img5 = io.BytesIO()
        plt.savefig(img5, format='png')
        img5.seek(0)
        graficos.append(base64.b64encode(img5.getvalue()).decode('utf-8'))
        plt.close(fig5)

 
        # Gráfico de violino para a Média de Qualidade das Aulas
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.violinplot(y=discentecurso['Media_Qualidade_Aulas'], ax=ax, color='lightgreen')

        # Título e rótulos
        ax.set_title('Distribuição da Média de Qualidade das Aulas', fontsize=16)
        ax.set_ylabel('Média de Avaliação', fontsize=14)

        # Adicionar anotação com a média
        media_valor = discentecurso['Media_Qualidade_Aulas'].mean()
        ax.text(0.1, media_valor + 0.2, f'Média: {media_valor:.2f}', color='black', fontsize=12)

        # Ajustar layout e salvar o gráfico em buffer
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)


    except Exception as e:
        flash(f"Erro ao gerar recomendações: {str(e)}", 'danger')
        return redirect(url_for('discente.importar_discente'))

    return render_template('dashboard_discenteia.html', graficos=graficos, estatisticas=estatisticas_html)

# Função para processar o sentimento
def analisar_sentimento(texto):
    return sid.polarity_scores(texto)


# Inicializar o analisador de sentimento
nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

@discente_route.route('/analisar_sentimentos', methods=['GET'])
def analisar_sentimentos():
    try:
        # Definindo caminho do arquivo
        file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('discente.importar_discente'))

        # Carregar o arquivo CSV
        discentecurso = pd.read_csv(file_path, delimiter=';')
        
        # Renomear colunas para simplificar a análise
        discentecurso.rename({
            'Gostaria de adicionar algum comentario referente seu Programa de Pos-Graduacao?': 'Sentimento_Programa',
            'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?': 'Sentimento_Pro_Reitoria'
        }, axis=1, inplace=True)

        # Remover linhas sem comentários
        df_comentarios = discentecurso[['Sentimento_Programa', 'Sentimento_Pro_Reitoria']].dropna(how='all')

        if df_comentarios.empty:
            flash('Nenhum comentário suficiente disponível para análise de sentimento.', 'warning')
            return redirect(url_for('discente.importar_discente'))

        # Aplicar análise de sentimento em cada comentário
        df_comentarios['Sent_Programa_Score'] = df_comentarios['Sentimento_Programa'].apply(lambda x: sid.polarity_scores(str(x)) if pd.notna(x) else None)
        df_comentarios['Sent_Pro_Reitoria_Score'] = df_comentarios['Sentimento_Pro_Reitoria'].apply(lambda x: sid.polarity_scores(str(x)) if pd.notna(x) else None)

        # Expandir resultados do VADER em colunas separadas
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_Programa_Score']).add_prefix('Programa_'))
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_Pro_Reitoria_Score']).add_prefix('Pro_Reitoria_'))

        # Cálculo das médias de sentimento
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()
        media_sentimentos_prppg = df_comentarios['Pro_Reitoria_compound'].mean()

        # Contagem dos tipos de sentimento para o Programa
        total_negativos_programa = len(df_comentarios[df_comentarios['Programa_compound'] < 0])
        total_positivos_programa = len(df_comentarios[df_comentarios['Programa_compound'] > 0])
        total_neutros_programa = len(df_comentarios[df_comentarios['Programa_compound'] == 0])

        # Contagem dos tipos de sentimento para a PRPPG
        total_negativos_prppg = len(df_comentarios[df_comentarios['Pro_Reitoria_compound'] < 0])
        total_positivos_prppg = len(df_comentarios[df_comentarios['Pro_Reitoria_compound'] > 0])
        total_neutros_prppg = len(df_comentarios[df_comentarios['Pro_Reitoria_compound'] == 0])

        # Criar gráficos de barras para a distribuição de sentimentos
        # Gráfico para o Programa de Pós-Graduação
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        ax1.bar(['Negativos', 'Positivos', 'Neutros'], [total_negativos_programa, total_positivos_programa, total_neutros_programa], color=['red', 'green', 'gray'])
        ax1.set_title('Distribuição de Sentimentos sobre o Programa de Pós-Graduação')
        ax1.set_xlabel('Tipo de Sentimento')
        ax1.set_ylabel('Número de Comentários')

        # Salvar gráfico em buffer
        img1 = io.BytesIO()
        plt.savefig(img1, format='png')
        img1.seek(0)
        grafico_sentimentos_programa = base64.b64encode(img1.getvalue()).decode('utf-8')
        plt.close(fig1)

        # Gráfico para a PRPPG
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        ax2.bar(['Negativos', 'Positivos', 'Neutros'], [total_negativos_prppg, total_positivos_prppg, total_neutros_prppg], color=['red', 'green', 'gray'])
        ax2.set_title('Distribuição de Sentimentos sobre a Pró-Reitoria')
        ax2.set_xlabel('Tipo de Sentimento')
        ax2.set_ylabel('Número de Comentários')

        # Salvar gráfico em buffer
        img2 = io.BytesIO()
        plt.savefig(img2, format='png')
        img2.seek(0)
        grafico_sentimentos_prppg = base64.b64encode(img2.getvalue()).decode('utf-8')
        plt.close(fig2)

        return render_template('sentimentosdiscente.html', 
                               grafico_sentimentos_programa=grafico_sentimentos_programa,
                               grafico_sentimentos_prppg=grafico_sentimentos_prppg,
                               media_programa=media_sentimentos_programa, 
                               media_prppg=media_sentimentos_prppg)

    except Exception as e:
        flash(f"Erro ao gerar recomendações: {str(e)}", 'danger')
        return redirect(url_for('discente.importar_discente'))

# Função de normalização de nomes de colunas
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
        .replace('<', '')
        .replace('>', '')
        for col in df.columns
    ]
    return df

@discente_route.route('/visualizar_resultados', methods=['GET'])
def visualizar_resultados():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/discente.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('discente.importar_discente'))

        discentecurso = pd.read_csv(file_path, delimiter=';')

        # Verificar se os dados têm distribuição suficiente para treinamento
        print(discentecurso.describe())  # Verificar estatísticas gerais para cada coluna

        # Avaliar os sentimentos do Programa de Pós-Graduação
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()

        # Gráfico de barras de sentimentos por ano de ingresso
        # Ajustar o gráfico com rotação dos rótulos no eixo X
        # Aumentar o tamanho da imagem com figsize
      # Aumentar o tamanho da imagem com figsize
        fig, ax = plt.subplots(figsize=(14, 8))  # Ajuste os valores para o tamanho desejado
        discentecurso['Media_Qualidade_Aulas'].plot(kind='bar', ax=ax)
        plt.title('Média de Qualidade das Aulas')

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
        return render_template('resultadodiscente.html', 
                               grafico_sentimentos_ingresso=grafico_sentimentos_ingresso,
                               mse_otimizado=mse_otimizado,
                               media_programa=media_sentimentos_programa)

    except Exception as e:
        flash(f"Erro ao gerar recomendações: {str(e)}", 'danger')
        return redirect(url_for('discente.importar_discente'))






# Rota para análise de clustering
def aplicar_clustering(discentecurso, num_clusters=3):
    # Garantir que as colunas estejam livres de valores não numéricos
    discentecurso[['Qualidade_aulas', 'Infraestrutura_geral']] = discentecurso[['Qualidade_aulas', 'Infraestrutura_geral']].apply(pd.to_numeric, errors='coerce')
    discentecurso.dropna(subset=['Qualidade_aulas', 'Infraestrutura_geral'], inplace=True)

    # Aplicar KMeans
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    discentecurso['Cluster'] = kmeans.fit_predict(discentecurso[['Qualidade_aulas', 'Infraestrutura_geral']])
    
    # Gráfico de dispersão
    fig, ax = plt.subplots()
    sns.scatterplot(x='Qualidade_aulas', y='Infraestrutura_geral', hue='Cluster', data=discentecurso, palette='viridis', ax=ax)
    ax.set_title('Clusters de Alunos com Base nas Avaliações')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode('utf-8')

# Função para análise de regressão
def aplicar_regressao(discentecurso):
    # Garantir valores numéricos nas colunas usadas para regressão
    discentecurso[['Infraestrutura_geral', 'Relacionamento_coordenador', 'Qualidade_aulas']] = discentecurso[['Infraestrutura_geral', 'Relacionamento_coordenador', 'Qualidade_aulas']].apply(pd.to_numeric, errors='coerce')
    discentecurso.dropna(subset=['Infraestrutura_geral', 'Relacionamento_coordenador', 'Qualidade_aulas'], inplace=True)

    X = discentecurso[['Infraestrutura_geral', 'Relacionamento_coordenador']]
    y = discentecurso['Qualidade_aulas']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    mse = mean_squared_error(y_test, model.predict(X_test))
    return f'MSE da regressão: {mse}'

# Função para aplicar a análise de sentimento e retornar o gráfico como base64
def aplicar_analise_sentimentos(discentecurso):
    # Renomear colunas para aplicar a análise de sentimento
    discentecurso.rename({
        'comentario_programa': 'Sentimento_Programa',
        'comentario_PRPPG': 'Sentimento_Pro_Reitoria'
    }, axis=1, inplace=True)

    # Remover linhas vazias das colunas de comentários
    df_comentarios = discentecurso[['Sentimento_Programa', 'Sentimento_Pro_Reitoria']].dropna(how='all')

    # Aplicar a função de sentimento para cada comentário
    df_comentarios['Sent_Programa_Score'] = df_comentarios['Sentimento_Programa'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)
    df_comentarios['Sent_Pro_Reitoria_Score'] = df_comentarios['Sentimento_Pro_Reitoria'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)

    # Quebrar os resultados do VADER (dicionário) em colunas separadas
    df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_Programa_Score']).add_prefix('Programa_'))
    df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_Pro_Reitoria_Score']).add_prefix('Pro_Reitoria_'))

    # Calcular a média dos sentimentos
    media_sentimentos_programa = df_comentarios['Programa_compound'].mean()
    media_sentimentos_prppg = df_comentarios['Pro_Reitoria_compound'].mean()

    # Contar sentimentos negativos, positivos e neutros
    total_negativos_programa = len(df_comentarios[df_comentarios['Programa_compound'] < 0])
    total_positivos_programa = len(df_comentarios[df_comentarios['Programa_compound'] > 0])
    total_neutros_programa = len(df_comentarios[df_comentarios['Programa_compound'] == 0])

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

@discente_route.route('/executar_analise')
def executar_analise():
    tipo = request.args.get('tipo')
    discentecurso = pd.read_csv('uploads/discente.csv', delimiter=';')
    discentecurso = renomear_colunas(discentecurso)
    discentecurso = limpar_dados(discentecurso)

    graficos = []
    estatisticas_html = gerar_estatisticas_descritivas(discentecurso)

    # Variáveis padrão para o template
    media_programa = None
    grafico_sentimentos_ingresso = None
    mse_otimizado = None
    recomendacoes_por_programa = None

    # Análise de Sentimento
    if tipo == 'sentimento':
        grafico_sentimentos_ingresso = aplicar_analise_sentimentos(discentecurso)
        media_programa = discentecurso['Media_Qualidade_Aulas'].mean() if 'Media_Qualidade_Aulas' in discentecurso else None

    # Análise de Clustering
    elif tipo == 'clustering':
        grafico = aplicar_clustering(discentecurso)
        graficos.append(grafico)

    # Análise de Regressão
    elif tipo == 'regressao':
        mse_otimizado = aplicar_regressao(discentecurso)

    return render_template(
        'resultadodiscente.html', 
        media_programa=media_programa,
        grafico_sentimentos_ingresso=grafico_sentimentos_ingresso,
        mse_otimizado=mse_otimizado,
        recomendacoes_por_programa=recomendacoes_por_programa,
        estatisticas=estatisticas_html
    )
# Rota para análise de clustering
def aplicar_clustering(discentecurso, num_clusters=3):
    # Garantir que as colunas estejam livres de valores não numéricos
    discentecurso[['Qualidade_aulas', 'Infraestrutura_geral']] = discentecurso[['Qualidade_aulas', 'Infraestrutura_geral']].apply(pd.to_numeric, errors='coerce')
    discentecurso.dropna(subset=['Qualidade_aulas', 'Infraestrutura_geral'], inplace=True)

    # Aplicar KMeans
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    discentecurso['Cluster'] = kmeans.fit_predict(discentecurso[['Qualidade_aulas', 'Infraestrutura_geral']])
    
    # Gráfico de dispersão
    fig, ax = plt.subplots()
    sns.scatterplot(x='Qualidade_aulas', y='Infraestrutura_geral', hue='Cluster', data=discentecurso, palette='viridis', ax=ax)
    ax.set_title('Clusters de Alunos com Base nas Avaliações')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode('utf-8')


def gerar_estatisticas_descritivas(df):
    # Calcula as estatísticas descritivas e converte para HTML
    estatisticas = df.describe().transpose()
    estatisticas_html = estatisticas.to_html(classes="table table-striped")
    return estatisticas_html

def aplicar_regressao(discentecurso):
    # Garantir valores numéricos nas colunas adicionais
    discentecurso[['Infraestrutura_geral', 'Relacionamento_coordenador', 'Qualidade_aulas', 'Material_didatico']] = \
    discentecurso[['Infraestrutura_geral', 'Relacionamento_coordenador', 'Qualidade_aulas', 'Material_didatico']].apply(pd.to_numeric, errors='coerce')
    discentecurso.dropna(subset=['Infraestrutura_geral', 'Relacionamento_coordenador', 'Qualidade_aulas', 'Material_didatico'], inplace=True)

    X = discentecurso[['Infraestrutura_geral', 'Relacionamento_coordenador', 'Material_didatico']]
    y = discentecurso['Qualidade_aulas']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    mse = mean_squared_error(y_test, model.predict(X_test))
    return mse  # Retorna o valor numérico diretamente


# Função de recomendações estratégicas
def gerar_recomendacoes_estrategicas(df, media_sentimentos_programa, mse):
    recomendacoes = []

    if media_sentimentos_programa < -0.2:
        recomendacoes.append("Melhorar o relacionamento e comunicação no programa.")
    if mse > 1.0:
        recomendacoes.append("Reavaliar a qualidade das aulas e infraestrutura para melhorar a satisfação dos alunos.")
    
    if df['proficiencia_ingles'].mean() < 3:
        recomendacoes.append("Objetivo: Aumentar o suporte para proficiência em inglês dos alunos.")
    
    return recomendacoes

# Rota para exibir recomendações
@discente_route.route('/exibir_recomendacoes', methods=['GET'])
def exibir_recomendacoes():
    try:
        file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
        if not os.path.exists(file_path):
            flash('Arquivo "discente.csv" não encontrado na pasta uploads.', 'danger')
            return redirect(url_for('discente.importar_discente'))
        
        # Carregar, limpar e renomear colunas do CSV
        discentecurso = pd.read_csv(file_path, delimiter=';')
        discentecurso = renomear_colunas(discentecurso)
        discentecurso = limpar_dados(discentecurso)
        
        # Calcular a média das avaliações principais
        required_columns = ['Qualidade_aulas', 'Material_didatico', 'Infraestrutura_geral']
        if all(col in discentecurso.columns for col in required_columns):
            discentecurso['Media_Qualidade_Aulas'] = discentecurso[required_columns].mean(axis=1)
        else:
            missing_cols = [col for col in required_columns if col not in discentecurso.columns]
            flash(f"As colunas necessárias para o cálculo da média estão ausentes: {missing_cols}", "danger")
            return redirect(url_for('discente.importar_discente'))
        
        # Cálculo de métricas para recomendações
        media_sentimentos_programa = discentecurso['Media_Qualidade_Aulas'].mean()
        mse = 1.2  # Substitua este valor pelo cálculo real de MSE se necessário
        
        # Geração de recomendações
        recomendacoes = gerar_recomendacoes_estrategicas(discentecurso, media_sentimentos_programa, mse)
        
        return render_template('recomendacaodiscente.html', recomendacoes=recomendacoes)

    except Exception as e:
        flash(f"Erro ao gerar recomendações: {str(e)}", 'danger')
        return redirect(url_for('discente.importar_discente'))

# Função para limpar dados problemáticos
def limpar_dados(df):
    df.replace({
        "Sem condições de avaliar": np.nan,
        "Sem condiÃ§Ãµes de avaliar": np.nan,
        "Sem condicoes de avaliar": np.nan,
        "Não se aplica": np.nan
    }, inplace=True)
    return df


# Função de recomendações estratégicas
def gerar_recomendacoes_estrategicas(df, media_sentimentos_programa, mse):
    recomendacoes = []

    if media_sentimentos_programa < -0.2:  # Média de sentimentos negativa
        recomendacoes.append("Melhorar o relacionamento e comunicação no programa.")
    if mse > 1.0:  # MSE alto indicando áreas para melhoria
        recomendacoes.append("Reavaliar a qualidade das aulas e infraestrutura para melhorar a satisfação dos alunos.")
    
    # Exemplo de ação para melhoria contínua
    recomendacoes.append("Definir metas de curto prazo para melhoria das avaliações negativas.")
    
    # Exemplo de objetivo estratégico
    if df['proficiencia_ingles'].mean() < 3:
        recomendacoes.append("Objetivo: Aumentar o suporte para proficiência em inglês dos alunos.")
    
    return recomendacoes




def gerar_recomendacoes_comuns(media_sentimentos, mse):
    recomendacoes = []
    if media_sentimentos < -0.2:
        recomendacoes.append("Melhorar o relacionamento e comunicação no programa.")
    if mse > 1.0:
        recomendacoes.append("Reavaliar a qualidade das aulas e infraestrutura.")
    return recomendacoes

@discente_route.route('/exibir_recomendacoes_programa', methods=['GET'])
def exibir_recomendacoes_programa():
   
    try:
        file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
        if not os.path.exists(file_path):
            flash('Arquivo "discente.csv" não encontrado na pasta uploads.', 'danger')
            return redirect(url_for('discente.importar_discente'))
        
        # Carregar, limpar e renomear colunas do CSV
        discentecurso = pd.read_csv(file_path, delimiter=';')
        discentecurso = renomear_colunas(discentecurso)
        discentecurso = limpar_dados(discentecurso)
            
        # Garantir que as colunas relevantes são numéricas
        colunas_qualidade = ['Qualidade_aulas', 'Material_didatico', 'Acervo_disponivel']
        colunas_organizacao = ['organizacao_programa','Seu_conhecimento','regimento_interno','regimento_geral', 'normas_CAPES', 'processo_CAPES']
        colunas_infraestrutura = ['insumos_pesquisa', 'Infraestrutura_geral', 'laboratorio_sala']
        colunas_relacionamentos = ['Relacionamento_orientador', 'Relacionamento_coordenador',
                                   'Relacionamento_secretaria', 'Relacionamento_colegas']
        colunas_internacionalizacao = ['proficiencia_ingles','preparado_internacionalizacao',
                                       'interesse_internacionalizacao', 'projeto_parceria_internacional','PRPPG_preparado_internacionalizacao']
        colunas_pesquisa = ['projeto pesquisa','producao cientifica','pesquisa_relevancia_social','pesquisa relevancia economica','pesquisa relevancia ambiental','pesquisa avanço cientifico']

         # Converter as colunas para numérico e tratar valores ausentes
        def converter_para_numerico(df, colunas):
            for coluna in colunas:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
            return df

        discentecurso = converter_para_numerico(discentecurso, 
                                                 colunas_qualidade + colunas_organizacao + 
                                                 colunas_infraestrutura + colunas_relacionamentos + 
                                                 colunas_internacionalizacao+colunas_pesquisa)

        # Calcular médias por grupo
        discentecurso['Media_Qualidade'] = discentecurso[colunas_qualidade].mean(axis=1)
        discentecurso['Media_Organizacao'] = discentecurso[colunas_organizacao].mean(axis=1)
        discentecurso['Media_Infraestrutura'] = discentecurso[colunas_infraestrutura].mean(axis=1)
        discentecurso['Media_Relacionamentos'] = discentecurso[colunas_relacionamentos].mean(axis=1)
        discentecurso['Media_Internacionalizacao'] = discentecurso[colunas_internacionalizacao].mean(axis=1)
        discentecurso['Media_pesquisa'] = discentecurso[colunas_pesquisa].mean(axis=1)

        # Agrupar por programa e calcular médias
        df_por_programa = discentecurso.groupby('programa').agg({
            'Media_Qualidade': 'mean',
            'Media_Organizacao': 'mean',
            'Media_Infraestrutura': 'mean',
            'Media_Relacionamentos': 'mean',
            'Media_Internacionalizacao': 'mean',
            'Media_pesquisa':'mean'

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
                
                if row['Media_Organizacao'] < 3:
                    recomendacoes.append("Reavaliar a organização do programa e o conhecimento dos alunos sobre as normas.")
                
                if row['Media_Infraestrutura'] < 3:
                    recomendacoes.append("Investir em infraestrutura, incluindo laboratórios e insumos de pesquisa.")
                
                if row['Media_Relacionamentos'] < 3:
                    recomendacoes.append("Aprimorar o relacionamento entre alunos, orientadores e coordenação.")
                
                if row['Media_Internacionalizacao'] < 3:
                    recomendacoes.append("Incentivar a internacionalização e aumentar a proficiência em inglês dos alunos.")

                if row['Media_pesquisa'] < 3:
                    recomendacoes.append("Incentivar a inovação na pesquisa cientifica.")
                # Armazena as recomendações para cada programa
                recomendacoes_por_programa[programa] = recomendacoes

            return recomendacoes_por_programa

        # Gerar recomendações para cada programa
        recomendacoes_programa = gerar_recomendacoes_programa(df_por_programa)

        # Passar recomendações para o template
        print(recomendacoes_programa)  # Verificar o conteúdo no console
        return render_template('recomendacao_programa.html', recomendacoes=recomendacoes_programa)
    except Exception as e:
        flash(f"Erro ao gerar recomendações: {e}", 'danger')
        return redirect(url_for('discente.importar_discente'))


def gerar_recomendacoes_programa(df_agrupado):
    recomendacoes_por_programa = {}

    for _, row in df_agrupado.iterrows():
        programa = row['programa']
        recomendacoes = []

        # Regras de recomendações para diferentes categorias
        if row['Media_Qualidade'] < 3:
            recomendacoes.append({
                "objetivo": "Melhorar a qualidade das aulas e do material didático",
                "meta": "Aumentar a média de satisfação para pelo menos 4.0 nos próximos 6 meses",
                "indicador": "Média de avaliações sobre qualidade de aulas e materiais"
            })
        
        if row['Media_Organizacao'] < 3:
            recomendacoes.append({
                "objetivo": "Reavaliar e aprimorar a organização do programa",
                "meta": "Garantir que 80% dos alunos entendam as normas e o funcionamento do programa",
                "indicador": "Percentual de alunos que avaliam positivamente o entendimento sobre normas"
            })
        
        if row['Media_Infraestrutura'] < 3:
            recomendacoes.append({
                "objetivo": "Investir em infraestrutura para apoio acadêmico",
                "meta": "Alocar recursos para melhorar laboratórios e insumos de pesquisa até o próximo semestre",
                "indicador": "Nível de satisfação com infraestrutura e laboratórios"
            })
        
        if row['Media_Relacionamentos'] < 3:
            recomendacoes.append({
                "objetivo": "Fortalecer o relacionamento entre alunos e equipe acadêmica",
                "meta": "Aumentar a média de satisfação para 4.0 na área de relacionamentos",
                "indicador": "Média de avaliações sobre relacionamentos com orientadores, coordenadores e colegas"
            })
        
        if row['Media_Internacionalizacao'] < 3:
            recomendacoes.append({
                "objetivo": "Promover a internacionalização do programa",
                "meta": "Aumentar a média de proficiência em inglês para 4.0 e criar 2 novas parcerias internacionais",
                "indicador": "Média de proficiência em inglês e número de parcerias internacionais"
            })

        if row['Media_pesquisa'] < 3:
            recomendacoes.append({
                "objetivo": "Incentivar a inovação na pesquisa científica",
                "meta": "Aumentar a produção de publicações científicas e inovação tecnológica",
                "indicador": "Número de publicações científicas e inovações tecnológicas registradas"
            })
        
        # Adiciona as recomendações para cada programa, mesmo que estejam vazias, para garantir consistência no template
        if not recomendacoes:
            recomendacoes.append("Sem recomendações específicas.")
        
        recomendacoes_por_programa[programa] = recomendacoes

    return recomendacoes_por_programa
