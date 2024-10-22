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
from xgboost import XGBRegressor

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

    for col in colunas:
        df[col] = df[col].apply(calcular_media_digitos)  # Aplicar a função de média dos dígitos
    return df

# Definir o blueprint
avaliacaodiscente_route = Blueprint('avaliacaodiscente', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Verificar se o diretório de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Verifica se o arquivo tem uma extensão permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@avaliacaodiscente_route.route('/importar_planilhadiscente', methods=['GET', 'POST'])
def importar_planilhadiscente():
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
            return redirect(url_for('avaliacaodiscente.gerar_graficos_completos', filename=filename))

    return render_template('importar_planilhadiscente.html')

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
    df.replace({'Sim': 1, 'NÃO': 0, 'Não': 0}, inplace=True)
    
    for col in colunas:
        df[col] = df[col].apply(calcular_media_digitos)  # Aplicar a função de média dos dígitos
    return df

#@avaliacaodiscente_route.route('/importar_planilhadiscente', methods=['GET', 'POST'])
def importar_planilhadiscente():
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
            return redirect(url_for('avaliacaodiscente.gerar_graficos_completos', filename=filename))

    return render_template('importar_planilhadiscente.html')


@avaliacaodiscente_route.route('/gerar_graficos_completos')
def gerar_graficos_completos():
    graficos = []

    # Receber o nome do arquivo da URL
    filename = request.args.get('filename')
    
    if not filename:
        flash('Nenhum arquivo selecionado para gerar gráficos', 'danger')
        return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        flash('Arquivo não encontrado', 'danger')
        return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

    try:
        # Tentar ler o arquivo CSV e remover o BOM
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            discentecurso = pd.read_csv(f, delimiter=';')

        # Renomear as colunas como no seu Colab
        discentecurso.rename({
            '1. Qual o seu nivel de formacao?':'formacao',
            '2. Qual o seu ano de ingresso?': 'ingresso',
            '3. A qual programa esta vinculado?': 'programa',
            'como voce avalia a qualidade das aulas e do material utilizado?  [Qualidade das aulas]':'Qualidade das aulas',
            'Como voce avalia a qualidade das aulas e do material utilizado?  [Material didatico utilizado nas disciplinas]':'Material didatico',
            'Como voce avalia a qualidade das aulas e do material utilizado?  [Acervo disponivel para consulta]':'Acervo disponivel',
            'Como voce avalia a  infraestrutura do programa?  [Infraestrutura geral]':'Infraestrutura geral',
            'Como voce avalia a  infraestrutura do programa?  [Laboratorios de pesquisa/Salas de estudo]':'laboratorio sala',
            'Como voce avalia a  infraestrutura do programa?  [Insumos para pesquisa]':'insumos pesquisa',
            'Como voce avalia o relacionamento entre voce e: [os colegas]':'Relacionamento com os colegas',
            'Como voce avalia o relacionamento entre voce e: [a comissao orientadora]':'Relacionamento com orientador',
            'Como voce avalia o relacionamento entre voce e: [a comissao coordenadora]':'Relacionamento com coordenador',
            'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'Relacionamento com secretaria',
            'Como voce avalia a gestão do programa? [Processo de gestao/Administrativo do Programa]':'processo gestao programa',
            'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizacao programa',
            'Como voce avalia o seu conhecimento acerca: [do seu papel enquanto aluno]':'Seu conhecimento',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Interno do Programa]':'regimento interno programa',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Geral da Pos-Graduacao]':'regimento geral pos-graduacao',
            'Como voce avalia o seu conhecimento acerca: [das normas da Capes]':'normas CAPES',
            'Como voce avalia o seu conhecimento acerca: [do processo de avaliacao da Capes]':'processo avaliacao CAPES',
            'Em relacao ao seu PROJETO DE PESQUISA, voce esta:':'projeto pesquisa',
            'Em relacao a sua PRODUcaO CIENTiFICA, voce esta:':'producao cientifica',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia social?':'pesquisa relevancia social',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia economica?':'pesquisa relevancia economica',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia ambiental?':'pesquisa relevancia ambiental',
            'Voce acredita que sua pesquisa promove avanço cientifico?':'pesquisa avanço cientifico',
            'O seu Programa possui visao, missao e objetivos claros?':'visao-missao-objetivos',
            'Voce acredita que sua pesquisa esta alinhada com o objetivo e missao de seu Programa?':'pesquisa alinhada visao-missao-objetivos',
            'Quais sao os principais atores que podem ser impactados por sua pesquisa e produção cientifica dela decorrente? (Marque todas que se aplicam).':'atores impacto pesquisa',
            'Voce recebe bolsa de pos-graduacao?':'possui bolsa',
            'Para a realizacao de seu projeto de pesquisa houve algum tipo de captacao de recurso externo (exceto bolsa)? ':'pesquisa captacao de recurso',
            'Na sua opiniao, o que e preciso para que o seu Programa tenha producao de conhecimento cientifico e tecnologico qualificado, reconhecido pela comunidade cientifica internacional da area em que atua?':'reconhecimento programa internacional',
            'Producao de inovacao tecnologica e uma prioridade em seu programa de pos-graduacao?':'producao inovacao tecnologica',
            'Voce acredita que sua linha de pesquisa se destaca pela producao de inovacao tecnologica?':'linha pesquisa inovacao tecnologica',
            'Voce ja depositou alguma patente proveniente de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?':'patente linha pesquisa',
            'Produção de tecnologias de APLICAcaO SOCIAL e uma prioridade em seu programa de pos-graduacao?':'tecnologia de aplicacao social',
            'Alguma tecnologia de aplicacao social ja foi criada como resultado de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?':'projeto de pesquisa tecnologia aplicacao social',
            'Voce ja apresentou algum resultado de sua pesquisa em algum evento CIENTiFICO, ou pretende apresentar?':'resultado da pesquisa em evento cientifico',
            'Sua pesquisa podera gerar solucoes para os problemas que a sociedade enfrenta ou vira a enfrentar?':'pesquisa solucoes sociedade',
            'Qual o principal impacto social a ser promovido por seu projeto de pesquisa? (Marque todas aplicaveis)':'impacto projeto pesquisa',
            'No momento, ha interesse por parte do seu Programa de Pos-Graduacao em iniciar um processo de Internacionalizacao?':'interesse programa em internacionalizacao',
            'Voce se sente preparado para a internacionalizacao do seu Programa de Pos-Graduacao? ':'esta preparado internacionalizacao',
            'Voce entende que o seu Programa de Pos-Graduacao esta preparado para a internacionalizacao?':'PRPPG esta preparado internacionalizacao',
            'Seu projeto de pesquisa possui parcerias com instituicoes internacionais de pesquisa ou ensino?':'projeto parceria internacional',
            'Qual o seu nivel de proficiencia em lingua inglesa?':'proficiencia ingles',
            'Gostaria de adicionar algum comentario referente seu Programa de Pos-Graduacao?':'comentario programa',
            'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?':'comentario PRPPG'
        }, axis=1, inplace=True)

       # Verificar se as colunas necessárias estão presentes
        required_columns = ['Qualidade das aulas', 'Material didatico', 'Infraestrutura geral']
        
        # Aplicar a função de cálculo da média dos dígitos
        discentecurso = limpar_e_converter_para_numeric(discentecurso, required_columns)
        print(discentecurso.columns)

        # Criar novas colunas calculadas (médias)
        discentecurso['Media_Qualidade_Aulas'] = discentecurso[['Qualidade das aulas', 'Material didatico', 'Infraestrutura geral']].mean(axis=1)

        # Gráfico de barras - Avaliação da qualidade das aulas
        fig1, ax1 = plt.subplots()
        ax1.bar(discentecurso['Qualidade das aulas'].value_counts().index, 
                discentecurso['Qualidade das aulas'].value_counts())
        ax1.set_title('Distribuição da Qualidade das Aulas')
        ax1.set_xlabel('Qualidade das Aulas')
        ax1.set_ylabel('Número de Alunos')
        img1 = io.BytesIO()
        plt.savefig(img1, format='png')
        img1.seek(0)
        graficos.append(base64.b64encode(img1.getvalue()).decode('utf-8'))
        plt.close(fig1)

        # Histograma de Proficiência em Inglês
        fig2, ax2 = plt.subplots()
        ax2.hist(discentecurso['proficiencia ingles'], bins=10, color='skyblue')
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
        sns.boxplot(x='formacao', y='Qualidade das aulas', data=discentecurso, ax=ax3)
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
        sns.lineplot(x='ingresso', y='Qualidade das aulas', data=discentecurso, ax=ax4)
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
        sns.heatmap(discentecurso[['Qualidade das aulas', 'proficiencia ingles']].corr(), 
                    annot=True, cmap='coolwarm', linewidths=0.4, ax=ax5)
        ax5.set_title('Mapa de Calor das Correlações')
        img5 = io.BytesIO()
        plt.savefig(img5, format='png')
        img5.seek(0)
        graficos.append(base64.b64encode(img5.getvalue()).decode('utf-8'))
        plt.close(fig5)

        # Gráfico de violino para a Média de Qualidade das Aulas
        fig6, ax6 = plt.subplots(figsize=(10, 6))  # Definir o tamanho do gráfico
        sns.violinplot(y=discentecurso['Media_Qualidade_Aulas'], ax=ax6, color='lightgreen')

        # Título e rótulos
        ax6.set_title('Distribuição da Média de Qualidade das Aulas', fontsize=16)
        ax6.set_ylabel('Média de Avaliação', fontsize=14)

        # Adicionar anotação com a média
        media_valor = discentecurso['Media_Qualidade_Aulas'].mean()
        ax6.text(0.1, media_valor + 0.2, f'Média: {media_valor:.2f}', color='black', fontsize=12)

        plt.tight_layout()

        # Salvar o gráfico em buffer
        img6 = io.BytesIO()
        plt.savefig(img6, format='png')
        img6.seek(0)
        graficos.append(base64.b64encode(img6.getvalue()).decode('utf-8'))
        plt.close(fig6)

    except Exception as e:
        flash(f"Erro ao processar o arquivo: {e}", "danger")
        return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

    # Retornar o template com os gráficos gerados
    return render_template('dashboard_discente.html', graficos=graficos)

# Inicializar o analisador de sentimentos
nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Função para processar o sentimento
def analisar_sentimento(texto):
    return sid.polarity_scores(texto)


@avaliacaodiscente_route.route('/analisar_sentimentos', methods=['GET'])
def analisar_sentimentos():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/discente.csv'  # Altere para o caminho correto do arquivo
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

        discentecurso = pd.read_csv(file_path, delimiter=';')

        

        # Exibir as colunas do arquivo CSV para depuração
        print(f"Colunas do CSV carregado: {discentecurso.columns}")

        # Verificar se as colunas de comentários estão presentes antes de renomeá-las
        if 'Gostaria de adicionar algum comentario referente seu Programa de Pos-Graduacao?' not in discentecurso.columns or \
           'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?' not in discentecurso.columns:
            print("Colunas de comentários não encontradas:")
            flash('Colunas de comentários não encontradas no arquivo.', 'danger')
            return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

        # Renomear colunas para aplicar a análise de sentimento
        discentecurso.rename({
            'Gostaria de adicionar algum comentario referente seu Programa de Pos-Graduacao?': 'Sentimento_Programa',
            'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?': 'Sentimento_Pro_Reitoria'
        }, axis=1, inplace=True)

        # Remover linhas vazias das colunas de comentários
        df_comentarios = discentecurso[['Sentimento_Programa', 'Sentimento_Pro_Reitoria']].dropna(how='all')

        if df_comentarios.empty or (df_comentarios['Sentimento_Programa'].isnull().all() and df_comentarios['Sentimento_Pro_Reitoria'].isnull().all()):
            flash('Nenhum comentário suficiente disponível para análise de sentimento.', 'warning')
            return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

        # Aplicar a função de sentimento para cada comentário
        df_comentarios['Sent_Programa_Score'] = df_comentarios['Sentimento_Programa'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)
        df_comentarios['Sent_Pro_Reitoria_Score'] = df_comentarios['Sentimento_Pro_Reitoria'].apply(lambda x: analisar_sentimento(str(x)) if pd.notna(x) else None)

        # Quebrar os resultados do VADER (dicionário) em colunas separadas
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_Programa_Score']).add_prefix('Programa_'))
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_Pro_Reitoria_Score']).add_prefix('Pro_Reitoria_'))

        # Exibir a média dos sentimentos para as duas áreas
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()
        media_sentimentos_prppg = df_comentarios['Pro_Reitoria_compound'].mean()

        # Filtrar comentários negativos e positivos para o Programa de Pós-Graduação
        total_negativos_programa = len(df_comentarios[df_comentarios['Programa_compound'] < 0])
        total_positivos_programa = len(df_comentarios[df_comentarios['Programa_compound'] > 0])
        total_neutros_programa = len(df_comentarios[df_comentarios['Programa_compound'] == 0])

        # Criar gráficos de barras para a distribuição de sentimentos
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

        # Codificar a imagem em base64 para renderizar no HTML
        grafico_sentimentos = base64.b64encode(img.getvalue()).decode('utf-8')

        return render_template('sentimentosdiscente.html', grafico_sentimentos=grafico_sentimentos,
                               media_programa=media_sentimentos_programa, media_prppg=media_sentimentos_prppg)

    except Exception as e:
        flash(f"Erro ao processar os sentimentos: {e}", 'danger')
        return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

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

@avaliacaodiscente_route.route('/visualizar_resultados', methods=['GET'])
def visualizar_resultados():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/discente.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

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
        flash(f"Erro ao processar os resultados: {e}", 'danger')
        return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))


################################################################################################
@avaliacaodiscente_route.route('/analisar_dados_ia', methods=['GET'])
def analisar_dados_ia():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/discente.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

        # Carregar os dados do CSV
        discentecurso = pd.read_csv(file_path, delimiter=';')

        # Renomear as colunas como no seu Colab
        discentecurso.rename({
            '1. Qual o seu nivel de formacao?':'formacao',
            '2. Qual o seu ano de ingresso?': 'ingresso',
            '3. A qual programa esta vinculado?': 'programa',
            'como voce avalia a qualidade das aulas e do material utilizado?  [Qualidade das aulas]':'Qualidade das aulas',
            'Como voce avalia a qualidade das aulas e do material utilizado?  [Material didatico utilizado nas disciplinas]':'Material didatico',
            'Como voce avalia a qualidade das aulas e do material utilizado?  [Acervo disponivel para consulta]':'Acervo disponivel',
            'Como voce avalia a  infraestrutura do programa?  [Infraestrutura geral]':'Infraestrutura geral',
            'Como voce avalia a  infraestrutura do programa?  [Laboratorios de pesquisa/Salas de estudo]':'laboratorio sala',
            'Como voce avalia a  infraestrutura do programa?  [Insumos para pesquisa]':'insumos pesquisa',
            'Como voce avalia o relacionamento entre voce e: [os colegas]':'Relacionamento com os colegas',
            'Como voce avalia o relacionamento entre voce e: [a comissao orientadora]':'Relacionamento com orientador',
            'Como voce avalia o relacionamento entre voce e: [a comissao coordenadora]':'Relacionamento com coordenador',
            'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'Relacionamento com secretaria',
            'Como voce avalia a gestão do programa? [Processo de gestao/Administrativo do Programa]':'processo gestao programa',
            'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizacao programa',
            'Como voce avalia o seu conhecimento acerca: [do seu papel enquanto aluno]':'Seu conhecimento',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Interno do Programa]':'regimento interno programa',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Geral da Pos-Graduacao]':'regimento geral pos-graduacao',
            'Como voce avalia o seu conhecimento acerca: [das normas da Capes]':'normas CAPES',
            'Como voce avalia o seu conhecimento acerca: [do processo de avaliacao da Capes]':'processo avaliacao CAPES',
            'Em relacao ao seu PROJETO DE PESQUISA, voce esta:':'projeto pesquisa',
            'Em relacao a sua PRODUcaO CIENTiFICA, voce esta:':'producao cientifica',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia social?':'pesquisa relevancia social',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia economica?':'pesquisa relevancia economica',
            'Voce acredita que sua pesquisa possui relevancia e pertinencia ambiental?':'pesquisa relevancia ambiental',
            'Voce acredita que sua pesquisa promove avanço cientifico?':'pesquisa avanço cientifico',
            'O seu Programa possui visao, missao e objetivos claros?':'visao-missao-objetivos',
            'Voce acredita que sua pesquisa esta alinhada com o objetivo e missao de seu Programa?':'pesquisa alinhada visao-missao-objetivos',
            'Quais sao os principais atores que podem ser impactados por sua pesquisa e produção cientifica dela decorrente? (Marque todas que se aplicam).':'atores impacto pesquisa',
            'Voce recebe bolsa de pos-graduacao?':'possui bolsa',
            'Para a realizacao de seu projeto de pesquisa houve algum tipo de captacao de recurso externo (exceto bolsa)? ':'pesquisa captacao de recurso',
            'Na sua opiniao, o que e preciso para que o seu Programa tenha producao de conhecimento cientifico e tecnologico qualificado, reconhecido pela comunidade cientifica internacional da area em que atua?':'reconhecimento programa internacional',
            'Producao de inovacao tecnologica e uma prioridade em seu programa de pos-graduacao?':'producao inovacao tecnologica',
            'Voce acredita que sua linha de pesquisa se destaca pela producao de inovacao tecnologica?':'linha pesquisa inovacao tecnologica',
            'Voce ja depositou alguma patente proveniente de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?':'patente linha pesquisa',
            'Produção de tecnologias de APLICAcaO SOCIAL e uma prioridade em seu programa de pos-graduacao?':'tecnologia de aplicacao social',
            'Alguma tecnologia de aplicacao social ja foi criada como resultado de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?':'projeto de pesquisa tecnologia aplicacao social',
            'Voce ja apresentou algum resultado de sua pesquisa em algum evento CIENTiFICO, ou pretende apresentar?':'resultado da pesquisa em evento cientifico',
            'Sua pesquisa podera gerar solucoes para os problemas que a sociedade enfrenta ou vira a enfrentar?':'pesquisa solucoes sociedade',
            'Qual o principal impacto social a ser promovido por seu projeto de pesquisa? (Marque todas aplicaveis)':'impacto projeto pesquisa',
            'No momento, ha interesse por parte do seu Programa de Pos-Graduacao em iniciar um processo de Internacionalizacao?':'interesse programa em internacionalizacao',
            'Voce se sente preparado para a internacionalizacao do seu Programa de Pos-Graduacao? ':'esta preparado internacionalizacao',
            'Voce entende que o seu Programa de Pos-Graduacao esta preparado para a internacionalizacao?':'PRPPG esta preparado internacionalizacao',
            'Seu projeto de pesquisa possui parcerias com instituicoes internacionais de pesquisa ou ensino?':'projeto parceria internacional',
            'Qual o seu nivel de proficiencia em lingua inglesa?':'proficiencia ingles',
            'Gostaria de adicionar algum comentario referente seu Programa de Pos-Graduacao?':'comentario programa',
            'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?':'comentario PRPPG'
        }, axis=1, inplace=True)

        # 1. Garantir que todas as colunas são numéricas
        colunas_qualidade = ['Qualidade das aulas', 'Material didatico', 'Acervo disponivel']
        colunas_organizacao = ['organizacao programa', 'Seu conhecimento', 'regimento interno programa',
                               'regimento geral pos-graduacao', 'normas CAPES', 'processo avaliacao CAPES']
        colunas_infraestrutura = ['insumos pesquisa','Infraestrutura geral', 'laboratorio sala']
        colunas_relacionamentos = ['Relacionamento com orientador', 'Relacionamento com coordenador',
                                   'Relacionamento com secretaria', 'Relacionamento com os colegas']
        colunas_internacionalizacao = ['Qual o nivel de internacionalizacao do seu programa?', 'interesse programa em internacionalizacao',
                                       'esta preparado internacionalizacao', 'proficiencia ingles']

       # Converter as colunas para numéricas
        def converter_para_numerico(df, colunas):
            for coluna in colunas:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
            return df

        discentecurso = converter_para_numerico(discentecurso, colunas_qualidade + colunas_organizacao + colunas_infraestrutura + colunas_relacionamentos+ colunas_internacionalizacao)

        # Agrupar os dados por programa
        agrupado_por_programa = discentecurso.groupby('programa')

        # Variáveis para armazenar as recomendações por programa
        recomendacoes_por_programa = {}

        for programa, dados_programa in agrupado_por_programa:
            if len(dados_programa) < 2:
                continue  # Pular grupos com poucos dados para evitar erro no treino/teste

            # 2. Criar as médias por grupo de avaliação
            media_qualidade = dados_programa['Qualidade das aulas'].mean()
            media_infraestrutura = dados_programa['Infraestrutura geral'].mean()

            # Verificar sentimentos nos comentários (se disponíveis)
            df_comentarios = dados_programa[['comentario programa']].dropna()
            media_sentimentos_programa = None  # valor padrão se não houver comentários

            if not df_comentarios.empty:
                df_comentarios['Sentimento_Programa_Score'] = df_comentarios['comentario programa'].apply(lambda x: analisar_sentimento(str(x))['compound'])
                media_sentimentos_programa = df_comentarios['Sentimento_Programa_Score'].mean()

            # 3. RandomForest e XGBoost para prever a qualidade das aulas
            X = dados_programa.drop(['Qualidade das aulas'], axis=1)  # Variáveis independentes
            y = dados_programa['Qualidade das aulas']  # Variável dependente

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
                rf_model = RandomForestRegressor(random_state=42)
                rf_model.fit(X_train, y_train)
                y_pred_rf = rf_model.predict(X_test)
                mse_rf = mean_squared_error(y_test, y_pred_rf)

                # Treinar o modelo XGBoost
                xgb_model = XGBRegressor(random_state=42)
                xgb_model.fit(X_train, y_train)
                y_pred_xgb = xgb_model.predict(X_test)
                mse_xgb = mean_squared_error(y_test, y_pred_xgb)

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
        return render_template('recomendacaodiscente.html', recomendacoes_por_programa=recomendacoes_por_programa)

    except Exception as e:
        flash(f"Erro ao processar os dados: {e}", 'danger')
        return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))