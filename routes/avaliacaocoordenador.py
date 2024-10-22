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
avaliacaocoordenador_route = Blueprint('avaliacaocoordenador', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Verificar se o diretório de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Verifica se o arquivo tem uma extensão permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@avaliacaocoordenador_route.route('/importar_planilhacoordenador', methods=['GET', 'POST'])
def importar_planilhacoordenador():
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
            return redirect(url_for('avaliacaocoordenador.gerar_graficos_completos_coordenador', filename=filename))

    return render_template('importar_planilhacoordenador.html')

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
    df.replace({'Sim': 1, 'NÃO': 0, 'Não': 0,'Nao':0}, inplace=True)
    
    for col in colunas:
        df[col] = df[col].apply(calcular_media_digitos)  # Aplicar a função de média dos dígitos
    return df



@avaliacaocoordenador_route.route('/gerar_graficos_completos_coordenador')
def gerar_graficos_completos_coordenador():
    graficos = []

    # Receber o nome do arquivo da URL
    filename = request.args.get('filename')
    
    if not filename:
        flash('Nenhum arquivo selecionado para gerar gráficos', 'danger')
        return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        flash('Arquivo não encontrado', 'danger')
        return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))

    try:
        # Tentar ler o arquivo CSV e remover o BOM
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            coordenador = pd.read_csv(f, delimiter=';')

        # Renomear as colunas como no seu Colab
        coordenador.rename({
       
            'Voce e coordenador(a) de qual Programa?':'programa',
            'Ha quanto tempo esta na coordenacao do programa?':'tempo_coordenacao',
            'Como voce avalia a qualidade das aulas e do material utilizado no Programa?  [Qualidade das aulas]':'Qualidade_aulas',
            'Como voce avalia a qualidade das aulas e do material utilizado no Programa?  [Material didatico utilizado nas disciplinas]':'Material_didatico',
            'Como voce avalia a qualidade das aulas e do material utilizado no Programa?  [Acervo disponivel para consulta]':'Acervo_disponivel',
            'Como voce avalia a  infraestrutura do programa? [Infraestrutura geral]':'Infraestrutura_geral',
            'Como voce avalia a  infraestrutura do programa? [Laboratarios de pesquisa/Salas de estudo]':'Laboratorios_ pesquisa',
            'Como voce avalia a  infraestrutura do programa? [Insumos para pesquisa]':'Insumos_pesquisa',
            'Como voce avalia o relacionamento entre voce e: [os discentes]':'Relacionamento_discentes',
            'Como voce avalia o relacionamento entre voce e: [os docentes]':'Relacionamento_docentes',
            'Como voce avalia o relacionamento entre voce e: [os funcionarios]':'Relacionamento_funcionarios',
            'Como voce avalia o relacionamento entre voce e: [a coordenacao do programa]':'Relacionamento_coordenacao',
            'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'Relacionamento_secretaria',
            'Como voce avalia a gestao do programa? [Processo de gestao/Administrativo do Programa]':'processo_gestao_administrativa',
            'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizaçao_programa',
            'Como voce avalia o seu conhecimento acerca do/das: [seu papel enquanto coordenador(a)]':'papel_coordenador',
            'Como voce avalia o seu conhecimento acerca do/das: [Regimento Interno do Programa]':'regimento_interno',
            'Como voce avalia o seu conhecimento acerca do/das: [Regimento Geral da Pos-Graduacao]':'regimento_geral',
            'Como voce avalia o seu conhecimento acerca do/das: [normas Capes]':'normas_capes',
            'Como voce avalia o seu conhecimento acerca do/das: [processo de avaliacao da Capes]':'avaliacao_capes',
            'Em relacao a  TEMaTICA dos PROJETOS DE PESQUISA desenvolvidos pelo programa, voce esta:':'tematica_projetos_pesquisa',
            'Em relacao ao TEMPO DE EXECUcao dos PROJETOS DE PESQUISA desenvolvidos pelo programa, voce esta:':'execucao_projetos_pesquisa',
            'Em relacao ao RESULTADOS ALCANcADOS pelos PROJETOS DE PESQUISA desenvolvidos pelo programa, voce esta:':'resultado_projeto_pesquisa',
            'Em relacao a  PRODUcao CIENTiFICA do Programa, voce esta:':'producao_cientifica',
            'Voce acredita que os projetos de pesquisa em andamento no Programa possuem relevancia e pertinencia social?':'projeto_relevancia_social',
            'Voce acredita que os projetos de pesquisa em andamento no Programa possuem relevancia e pertinencia economica?':'projeto_relevancia_economica',
            'Voce acredita que os projetos de pesquisa em andamento no Programa possuem relevancia e pertinencia ambiental?':'projeto_relevancia_ambiental',
            'Voce acredita que os projetos de pesquisa em andamento no Programa promovem o avanÃ§o cientifico?':'projeto_avanco_cientifico',
            'O seu Programa possui visao, missao e objetivos claros?':'visao-missao-objetivos',
            'Voce acredita que os projetos de pesquisa em andamento estao alinhados com a visao, missao e objetivos de seu Programa?':'projetos_visao_missao_objetivos',
            'O programa discute seu planejamento estrategico entre os docentes, tecnicos, discentes e egressos do programa?':'planejamento_estrategico',
            'Quais sao os principais atores que podem ser impactados pelas pesquisas em andamento no Programa e pelas producoes cientificas deles decorrentes? (Marque todas que se aplicam).':'atores_impactados',
            'Voce possui iniciativas de captacao de recurso externo para o Programa (exceto bolsa)?':'captacao de recurso sem ser bolsa',
            'Na sua opiniao, o que e preciso para que o seu Programa tenha producao de conhecimento cientifico e tecnologico qualificado, reconhecido pela comunidade cientifica internacional da area?':'producao_internacional',
            'Producao de inovacao tecnologica e uma prioridade em seu programa de pos-graduacao?':'producao_inovacao_tecnologica',
            'Dentre as linhas de pesquisa do programa, ha alguma que se destaca na producao de inovacao tecnologica? Se sim, gentileza especificar qual ou quais?':'linhaspesquisa_inovacaotecnologica',
            'Com que frequencia sÃ£o depositadas patentes pelo programa?':'frequencia_patentes',
            'O programa ja criou outros produtos registrados como desenhos industriais, marca, indicacao geografica ou topografia de circuitos integrados, softwares e aplicativos, cultivar, etc?':'produtos_programas',
            'Qual a quantidade de patentes depositadas entre 2018, 2019 e 2020?':'quantidade_patentes',
            'Producao de tecnologias de APLICAcao SOCIAL e uma prioridade em seu programa de pos-graduacao?':'producao_aplicacao_social',
            'Ha alguma linha de pesquisa com o objetivo de produzir tecnologia de APLICAcao SOCIAL? Se sim, qual ou quais?':'linhaspesquisa_aplicacaosocial',
            'Alguma tecnologia de APLICAcao SOCIAL foi criada nos ultimos anos pelo programa?':'tecnologia_aplicacaosocial',
            'Algum discente ou egresso do programa participou da criacao de empresa ou organizacao social inovadora?':'criacao_empresa',
            'O Programa possui disciplinas que orientam os discentes em relacao a criacao de empresas ou organizacoes sociais de base tecnologica e inovadora?':'disciplinas_criacaoempresa',
            'O programa possui relacao com empresas, outros centros de pesquisa ou com o Centev?':'relacao_empresas',
            'O programa organizou eventos voltados para a COMUNIDADE nos ultimos tres anos?':'eventos_comunidade',
            'O programa organizou eventos CIENTiFICOS nos ultimos tres anos?':'eventos_tresanos',
            'O programa organizou eventos TECNOLoGICOS nos ultimos tres anos?':'eventos_tecnologicos',
            'Os projetos de pesquisa desenvolvidos no Programa poderao gerar solucoes para os problemas que a sociedade enfrenta ou vira a enfrentar?':'solucoes_sociedade',
            'Quais os principais impactos sociais a serem promovidos pelos projetos de pesquisa em andamento no Programa? (Marque todas aplicÃ¡veis)':'impactossociais_projeto',
            'No momento, ha interesse por parte do seu Programa de Pos-Graduacao em iniciar um processo de InternacionalizaÃ§Ã£o?':'interesse_internacionalizacao',
            'Seu programa esta preparado para a internacionalizacao?':'preparado_internacionalizacao',
            'Os DOCENTES do seu Programa de Pos-Graduacao estao preparados para a internacionalizacao?':'docentes_internacionalizacao',
            'Os DISCENTES do seu Programa de Pos-Graduacao estao preparados para a internacionalizacao?':'discentes_internacionalizacao',
            'Quantas disciplinas em lingua inglesa sao oferecidas em seu Programa?':'disciplinas_ingles',
            'O Programa possui projetos de pesquisa em parceria com instituicoes internacionais de pesquisa ou ensino?':'projetos_ parceriainternacional',
            'O programa mantem algum tipo de contato com seus egressos?':'contato_egressos',
            'Se afirmativo, quais as praticas de acompanhamento de egressos efetuadas pelo Programa e qual o canal de comunicacao utilizado?':'comunicacao_egressos',
            'Quais informacoes consideram importantes sobre os egressos?':'informacoes_egressos',
            'O programa acredita ser necessario um sistema institucional de acompanhamento de egressos? Por que?':'necessario acompanhamento_egresso',
            'Quais indicadores de desempenho considera importante para auxiliar o Programa no processo de avaliacao quadrienal?':'indicadores_importantes',
            'O programa tem dificuldades no processo de avaliacao da Capes? Se afirmativo, gentileza descreve-las.':'dificuldades_avaliacaocapes',
            'Gostaria de adicionar algum comentario referente ao Programa de Pos-Graduacao que coordena?':'comentarios_programa',
            'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?':'comentarios_PRPPG'
        }, axis=1, inplace=True)

       # Verificar se as colunas necessárias estão presentes
        required_columns = ['Qualidade_aulas', 'Material_didatico', 'Acervo_disponivel']
        
        # Aplicar a função de cálculo da média dos dígitos
        coordenador = limpar_e_converter_para_numeric(coordenador, required_columns)
        print(coordenador.columns)

        # Criar novas colunas calculadas (médias)
        coordenador['Media_Qualidade_Aulas'] = coordenador[['Qualidade_aulas', 'Material_didatico', 'Acervo_disponivel']].mean(axis=1)

        # Gráfico de barras - Avaliação da qualidade das aulas
       
       
    # Gerar gráfico de barras utilizando Pandas para simplificação
        fig1, ax1 = plt.subplots()

        # Gerar gráfico diretamente da série de valor
        coordenador['Qualidade_aulas'].value_counts().plot(kind='bar', ax=ax1)

        # Configurações do gráfico
        ax1.set_title('Distribuição da Qualidade das Aulas')
        ax1.set_xlabel('Qualidade_aulas')
        ax1.set_ylabel('Número de Coordenadores')

        # Salvar o gráfico em um buffer de memória
        img1 = io.BytesIO()
        plt.savefig(img1, format='png')
        img1.seek(0)

        # Adicionar o gráfico codificado em base64 na lista de gráficos
        graficos.append(base64.b64encode(img1.getvalue()).decode('utf-8'))

        # Fechar o gráfico para liberar memória
        plt.close(fig1)

        # Histograma de Proficiência em Inglês
        fig2, ax2 = plt.subplots()
        ax2.hist(coordenador['preparado_internacionalizacao'], bins=10, color='skyblue')
        ax2.set_title('Distribuição do curso - Preparado Internacionalização')
        ax2.set_xlabel('Nível de internacionalização')
        ax2.set_ylabel('Número de Coordenadores')
        img2 = io.BytesIO()
        plt.savefig(img2, format='png')
        img2.seek(0)
        graficos.append(base64.b64encode(img2.getvalue()).decode('utf-8'))
        plt.close(fig2)

        # Boxplot de Formação vs Qualidade das Aulas
        fig3, ax3 = plt.subplots()
        sns.boxplot(x='tempo_coordenacao', y='Qualidade_aulas', data=coordenador, ax=ax3)
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
        sns.lineplot(x='tempo_coordenacao', y='Qualidade_aulas', data=coordenador, ax=ax4)
        ax4.set_title('Tendência da Qualidade das Aulas ao Longo dos Anos')
        ax4.set_xlabel('tempo_coordenacao')
        ax4.set_ylabel('Qualidade das Aulas')
        img4 = io.BytesIO()
        plt.savefig(img4, format='png')
        img4.seek(0)
        graficos.append(base64.b64encode(img4.getvalue()).decode('utf-8'))
        plt.close(fig4)

        # Mapa de calor - Correlação entre variáveis
        fig5, ax5 = plt.subplots(figsize=(10, 7))
        sns.heatmap(coordenador[['Qualidade_aulas', 'preparado_internacionalizacao']].corr(), 
                    annot=True, cmap='coolwarm', linewidths=0.4, ax=ax5)
        ax5.set_title('Mapa de Calor das Correlações')
        img5 = io.BytesIO()
        plt.savefig(img5, format='png')
        img5.seek(0)
        graficos.append(base64.b64encode(img5.getvalue()).decode('utf-8'))
        plt.close(fig5)

        # Gráfico de violino para a Média de Qualidade das Aulas
        fig6, ax6 = plt.subplots(figsize=(10, 6))  # Definir o tamanho do gráfico
        sns.violinplot(y=coordenador['Media_Qualidade_Aulas'], ax=ax6, color='lightgreen')

        # Título e rótulos
        ax6.set_title('Distribuição da Média de Qualidade das Aulas', fontsize=16)
        ax6.set_ylabel('Média de Avaliação', fontsize=14)

        # Adicionar anotação com a média
        media_valor = coordenador['Media_Qualidade_Aulas'].mean()
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
        return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))

    # Retornar o template com os gráficos gerados
    return render_template('dashboard_coordenador.html', graficos=graficos)

# Inicializar o analisador de sentimentos
nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Função para processar o sentimento
def analisar_sentimento(texto):
    return sid.polarity_scores(texto)


@avaliacaocoordenador_route.route('/analisar_sentimentos_coordenador', methods=['GET'])
def analisar_sentimentos_coordenador():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/coordenador.csv'  # Altere para o caminho correto do arquivo
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))

        coordenador = pd.read_csv(file_path, delimiter=';')

        

        # Exibir as colunas do arquivo CSV para depuração
        print(f"Colunas do CSV carregado: {coordenador.columns}")

        # Verificar se as colunas de comentários estão presentes antes de renomeá-las
        if 'comentarios_programa' not in coordenador.columns or \
           'comentarios_PRPPG' not in coordenador.columns:
            print("Colunas de comentários não encontradas:")
            flash('Colunas de comentários não encontradas no arquivo.', 'danger')
            return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))

        # Renomear colunas para aplicar a análise de sentimento
        coordenador.rename({
            'comentarios_programa': 'Sentimento_Programa',
            'comentarios_PRPPG': 'Sentimento_Pro_Reitoria'
        }, axis=1, inplace=True)

        # Remover linhas vazias das colunas de comentários
        df_comentarios = coordenador[['Sentimento_Programa', 'Sentimento_Pro_Reitoria']].dropna(how='all')

        if df_comentarios.empty or (df_comentarios['Sentimento_Programa'].isnull().all() and df_comentarios['Sentimento_Pro_Reitoria'].isnull().all()):
            flash('Nenhum comentário suficiente disponível para análise de sentimento.', 'warning')
            return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))

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

        return render_template('sentimentocoordenador.html', grafico_sentimentos=grafico_sentimentos,
                               media_programa=media_sentimentos_programa, media_prppg=media_sentimentos_prppg)

    except Exception as e:
        flash(f"Erro ao processar os sentimentos: {e}", 'danger')
        return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))

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

@avaliacaocoordenador_route.route('/visualizar_resultados', methods=['GET'])
def visualizar_resultados():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/coordenador.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))

        coordenador = pd.read_csv(file_path, delimiter=';')

        # Verificar se os dados têm distribuição suficiente para treinamento
        print(coordenador.describe())  # Verificar estatísticas gerais para cada coluna

        # Avaliar os sentimentos do Programa de Pós-Graduação
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()

        # Gráfico de barras de sentimentos tempo_coordenacao
        # Ajustar o gráfico com rotação dos rótulos no eixo X
        # Aumentar o tamanho da imagem com figsize
      # Aumentar o tamanho da imagem com figsize
        fig, ax = plt.subplots(figsize=(14, 8))  # Ajuste os valores para o tamanho desejado
        coordenador['Media_Qualidade_Aulas'].plot(kind='bar', ax=ax)
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
        return render_template('resultadocoordenador.html', 
                               grafico_sentimentos_tempo_coordenacao=grafico_sentimentos_tempo_coordenacao,
                               mse_otimizado=mse_otimizado,
                               media_programa=media_sentimentos_programa)

    except Exception as e:
        flash(f"Erro ao processar os resultados: {e}", 'danger')
        return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))


################################################################################################
@avaliacaocoordenador_route.route('/analisar_dados_ia', methods=['GET'])
def analisar_dados_ia():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/coordenador.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))

        # Carregar os dados do CSV
        coordenador = pd.read_csv(file_path, delimiter=';')

        coordenador.rename({
       
            'Voce e coordenador(a) de qual Programa?':'programa',
            'Ha quanto tempo esta na coordenacao do programa?':'tempo_coordenacao',
            'Como voce avalia a qualidade das aulas e do material utilizado no Programa?  [Qualidade das aulas]':'Qualidade_aulas',
            'Como voce avalia a qualidade das aulas e do material utilizado no Programa?  [Material didatico utilizado nas disciplinas]':'Material_didatico',
            'Como voce avalia a qualidade das aulas e do material utilizado no Programa?  [Acervo disponivel para consulta]':'Acervo_disponivel',
            'Como voce avalia a  infraestrutura do programa? [Infraestrutura geral]':'Infraestrutura_geral',
            'Como voce avalia a  infraestrutura do programa? [Laboratarios de pesquisa/Salas de estudo]':'Laboratorios_ pesquisa',
            'Como voce avalia a  infraestrutura do programa? [Insumos para pesquisa]':'Insumos_pesquisa',
            'Como voce avalia o relacionamento entre voce e: [os discentes]':'Relacionamento_discentes',
            'Como voce avalia o relacionamento entre voce e: [os docentes]':'Relacionamento_docentes',
            'Como voce avalia o relacionamento entre voce e: [os funcionarios]':'Relacionamento_funcionarios',
            'Como voce avalia o relacionamento entre voce e: [a coordenacao do programa]':'Relacionamento_coordenacao',
            'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'Relacionamento_secretaria',
            'Como voce avalia a gestao do programa? [Processo de gestao/Administrativo do Programa]':'processo_gestao_administrativa',
            'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizaçao_programa',
            'Como voce avalia o seu conhecimento acerca do/das: [seu papel enquanto coordenador(a)]':'papel_coordenador',
            'Como voce avalia o seu conhecimento acerca do/das: [Regimento Interno do Programa]':'regimento_interno',
            'Como voce avalia o seu conhecimento acerca do/das: [Regimento Geral da Pos-Graduacao]':'regimento_geral',
            'Como voce avalia o seu conhecimento acerca do/das: [normas Capes]':'normas_capes',
            'Como voce avalia o seu conhecimento acerca do/das: [processo de avaliacao da Capes]':'avaliacao_capes',
            'Em relacao a  TEMaTICA dos PROJETOS DE PESQUISA desenvolvidos pelo programa, voce esta:':'tematica_projetos_pesquisa',
            'Em relacao ao TEMPO DE EXECUcao dos PROJETOS DE PESQUISA desenvolvidos pelo programa, voce esta:':'execucao_projetos_pesquisa',
            'Em relacao ao RESULTADOS ALCANcADOS pelos PROJETOS DE PESQUISA desenvolvidos pelo programa, voce esta:':'resultado_projeto_pesquisa',
            'Em relacao a  PRODUcao CIENTiFICA do Programa, voce esta:':'producao_cientifica',
            'Voce acredita que os projetos de pesquisa em andamento no Programa possuem relevancia e pertinencia social?':'projeto_relevancia_social',
            'Voce acredita que os projetos de pesquisa em andamento no Programa possuem relevancia e pertinencia economica?':'projeto_relevancia_economica',
            'Voce acredita que os projetos de pesquisa em andamento no Programa possuem relevancia e pertinencia ambiental?':'projeto_relevancia_ambiental',
            'Voce acredita que os projetos de pesquisa em andamento no Programa promovem o avanÃ§o cientifico?':'projeto_avanco_cientifico',
            'O seu Programa possui visao, missao e objetivos claros?':'visao-missao-objetivos',
            'Voce acredita que os projetos de pesquisa em andamento estao alinhados com a visao, missao e objetivos de seu Programa?':'projetos_visao_missao_objetivos',
            'O programa discute seu planejamento estrategico entre os docentes, tecnicos, discentes e egressos do programa?':'planejamento_estrategico',
            'Quais sao os principais atores que podem ser impactados pelas pesquisas em andamento no Programa e pelas producoes cientificas deles decorrentes? (Marque todas que se aplicam).':'atores_impactados',
            'Voce possui iniciativas de captacao de recurso externo para o Programa (exceto bolsa)?':'captacao de recurso sem ser bolsa',
            'Na sua opiniao, o que e preciso para que o seu Programa tenha producao de conhecimento cientifico e tecnologico qualificado, reconhecido pela comunidade cientifica internacional da area?':'producao_internacional',
            'Producao de inovacao tecnologica e uma prioridade em seu programa de pos-graduacao?':'producao_inovacao_tecnologica',
            'Dentre as linhas de pesquisa do programa, ha alguma que se destaca na producao de inovacao tecnologica? Se sim, gentileza especificar qual ou quais?':'linhaspesquisa_inovacaotecnologica',
            'Com que frequencia sÃ£o depositadas patentes pelo programa?':'frequencia_patentes',
            'O programa ja criou outros produtos registrados como desenhos industriais, marca, indicacao geografica ou topografia de circuitos integrados, softwares e aplicativos, cultivar, etc?':'produtos_programas',
            'Qual a quantidade de patentes depositadas entre 2018, 2019 e 2020?':'quantidade_patentes',
            'Producao de tecnologias de APLICAcao SOCIAL e uma prioridade em seu programa de pos-graduacao?':'producao_aplicacao_social',
            'Ha alguma linha de pesquisa com o objetivo de produzir tecnologia de APLICAcao SOCIAL? Se sim, qual ou quais?':'linhaspesquisa_aplicacaosocial',
            'Alguma tecnologia de APLICAcao SOCIAL foi criada nos ultimos anos pelo programa?':'tecnologia_aplicacaosocial',
            'Algum discente ou egresso do programa participou da criacao de empresa ou organizacao social inovadora?':'criacao_empresa',
            'O Programa possui disciplinas que orientam os discentes em relacao a criacao de empresas ou organizacoes sociais de base tecnologica e inovadora?':'disciplinas_criacaoempresa',
            'O programa possui relacao com empresas, outros centros de pesquisa ou com o Centev?':'relacao_empresas',
            'O programa organizou eventos voltados para a COMUNIDADE nos ultimos tres anos?':'eventos_comunidade',
            'O programa organizou eventos CIENTiFICOS nos ultimos tres anos?':'eventos_tresanos',
            'O programa organizou eventos TECNOLoGICOS nos ultimos tres anos?':'eventos_tecnologicos',
            'Os projetos de pesquisa desenvolvidos no Programa poderao gerar solucoes para os problemas que a sociedade enfrenta ou vira a enfrentar?':'solucoes_sociedade',
            'Quais os principais impactos sociais a serem promovidos pelos projetos de pesquisa em andamento no Programa? (Marque todas aplicÃ¡veis)':'impactossociais_projeto',
            'No momento, ha interesse por parte do seu Programa de Pos-Graduacao em iniciar um processo de InternacionalizaÃ§Ã£o?':'interesse_internacionalizacao',
            'Seu programa esta preparado para a internacionalizacao?':'preparado_internacionalizacao',
            'Os DOCENTES do seu Programa de Pos-Graduacao estao preparados para a internacionalizacao?':'docentes_internacionalizacao',
            'Os DISCENTES do seu Programa de Pos-Graduacao estao preparados para a internacionalizacao?':'discentes_internacionalizacao',
            'Quantas disciplinas em lingua inglesa sao oferecidas em seu Programa?':'disciplinas_ingles',
            'O Programa possui projetos de pesquisa em parceria com instituicoes internacionais de pesquisa ou ensino?':'projetos_ parceriainternacional',
            'O programa mantem algum tipo de contato com seus egressos?':'contato_egressos',
            'Se afirmativo, quais as praticas de acompanhamento de egressos efetuadas pelo Programa e qual o canal de comunicacao utilizado?':'comunicacao_egressos',
            'Quais informacoes consideram importantes sobre os egressos?':'informacoes_egressos',
            'O programa acredita ser necessario um sistema institucional de acompanhamento de egressos? Por que?':'necessario acompanhamento_egresso',
            'Quais indicadores de desempenho considera importante para auxiliar o Programa no processo de avaliacao quadrienal?':'indicadores_importantes',
            'O programa tem dificuldades no processo de avaliacao da Capes? Se afirmativo, gentileza descreve-las.':'dificuldades_avaliacaocapes',
            'Gostaria de adicionar algum comentario referente ao Programa de Pos-Graduacao que coordena?':'comentarios_programa',
            'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?':'comentario_PRPPG'
        }, axis=1, inplace=True)

        # 1. Garantir que todas as colunas são numéricas
        colunas_qualidade = ['Qualidade_aulas', 'Material_didatico', 'Acervo_disponivel']
        colunas_conehcimento_orientador = ['papel_coordenador', 'regimento_geral', 'regimento_geral',
                               'normas_capes', 'avaliacao_capes']
        colunas_infraestrutura = ['Insumos_pesquisa','Infraestrutura_geral','Laboratorios_ pesquisa']
        colunas_relacionamentos = ['Relacionamento_discentes', 'Relacionamento_docentes',
                                   'Relacionamento_funcionarios', 'Relacionamento_coordenacao','Relacionamento_secretaria']
        colunas_internacionalizacao = ['interesse_internacionalizacao', 'preparado_internacionalizacao',
                                       'docentes_internacionalizacao', 'discentes_internacionalizacao','disciplinas_ingles','projetos_ parceriainternacional']

       # Converter as colunas para numéricas
        def converter_para_numerico(df, colunas):
            for coluna in colunas:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
            return df

        coordenador = converter_para_numerico(coordenador, colunas_qualidade + colunas_conehcimento_orientador + colunas_infraestrutura + colunas_relacionamentos + colunas_internacionalizacao)

        # Agrupar os dados por programa
        agrupado_por_programa = coordenador.groupby('programa')

        # Variáveis para armazenar as recomendações por programa
        recomendacoes_por_programa = {}

        for programa, dados_programa in agrupado_por_programa:
            if len(dados_programa) < 2:
                continue  # Pular grupos com poucos dados para evitar erro no treino/teste

            # 2. Criar as médias por grupo de avaliação
            media_qualidade = dados_programa['Qualidade_aulas'].mean()
            media_infraestrutura = dados_programa['Infraestrutura_geral'].mean()

            # Verificar sentimentos nos comentários (se disponíveis)
            df_comentarios = dados_programa[['comentario_programa']].dropna()
            media_sentimentos_programa = None  # valor padrão se não houver comentários

            if not df_comentarios.empty:
                df_comentarios['Sentimento_Programa_Score'] = df_comentarios['comentario_programa'].apply(lambda x: analisar_sentimento(str(x))['compound'])
                media_sentimentos_programa = df_comentarios['Sentimento_Programa_Score'].mean()

            # 3. RandomForest e XGBoost para prever a qualidade das aulas
            X = dados_programa.drop(['Qualidade_aulas'], axis=1)  # Variáveis independentes
            y = dados_programa['Qualidade_aulas']  # Variável dependente

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
        return render_template('recomendacaocoordenador.html', recomendacoes_por_programa=recomendacoes_por_programa)

    except Exception as e:
        flash(f"Erro ao processar os dados: {e}", 'danger')
        return redirect(url_for('avaliacaocoordenador.importar_planilhacoordenador'))
    
# Função para gerar gráficos e retornar como base64
def gerar_grafico_base64(fig):
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')

# Certifique-se de que o arquivo CSV foi carregado corretamente
@avaliacaocoordenador_route.route('/avaliacao_coordenador')
def avaliacao_coordenador():
    file_path = 'uploads/coordenador.csv'  # Certifique-se de que o caminho está correto
    
    if not os.path.exists(file_path):
        flash('Arquivo não encontrado.', 'danger')
        return redirect(url_for('index'))  # Redireciona para a rota apropriada

    coordenador = pd.read_csv(file_path, delimiter=';')  # Carregar o arquivo CSV

    # Processar os dados agora que o CSV está carregado
    coordenador['Qualidade_aulas'] = pd.to_numeric(coordenador['Qualidade_aulas'], errors='coerce')
    coordenador['Material_didatico'] = pd.to_numeric(coordenador['Material_didatico'], errors='coerce')

    # O restante do código continua com `coordenador` sendo usado
    media_qualidade_aulas = coordenador['Qualidade_aulas'].mean()
    melhor_programa = coordenador.loc[coordenador['Qualidade_aulas'].idxmax(), 'programa']
    pior_programa = coordenador.loc[coordenador['Qualidade_aulas'].idxmin(), 'programa']

    # 2. Infraestrutura
    coordenador['Infraestrutura_geral'] = pd.to_numeric(coordenador['Infraestrutura_geral'], errors='coerce')
    media_infraestrutura = coordenador['Infraestrutura_geral'].mean()

    # 3. Relacionamento com Discentes, Docentes e Funcionários
    coordenador['Relacionamento_discentes'] = pd.to_numeric(coordenador['Relacionamento_discentes'], errors='coerce')
    media_relacionamento_discentes = coordenador['Relacionamento_discentes'].mean()

    # 4. Conhecimento e Gestão do Programa
    coordenador['conhecimento_regimento_interno'] = pd.to_numeric(coordenador['regimento_interno'], errors='coerce')
    media_conhecimento_regimento = coordenador['conhecimento_regimento_interno'].mean()

    # 5. Internacionalização e Produção Científica
    coordenador['internacionalizacao'] = pd.to_numeric(coordenador['disciplinas_ingles'], errors='coerce')
    media_internacionalizacao = coordenador['internacionalizacao'].mean()

    # 6. Impacto Social e Relevância Econômica
    coordenador['projeto_relevancia_social'] = pd.to_numeric(coordenador['projeto_relevancia_social'], errors='coerce')
    media_relevancia_social = coordenador['projeto_relevancia_social'].mean()

    # 7. Dificuldades com a Avaliação da CAPES
    dificuldades_capes = coordenador['dificuldades_avaliacaocapes'].value_counts()

    # 8. Análise de Sentimentos nos Comentários
    coordenador['comentario_programa'] = coordenador['comentarios_programa'].fillna('')
    coordenador['sentimento_programa'] = coordenador['comentarios_programa'].apply(lambda x: sid.polarity_scores(x)['compound'])

    # Média dos sentimentos
    media_sentimento_programa = coordenador['sentimento_programa'].mean()

    # 9. Gráficos - Exemplo para Qualidade das Aulas
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='programa', y='qualidade_aulas', data=df, ax=ax)
    ax.set_title('Qualidade das Aulas por Programa')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    grafico_qualidade_aulas = gerar_grafico_base64(fig)
    plt.close(fig)

    # 10. Recomendações
    recomendacoes = []
    if media_qualidade_aulas < 3:
        recomendacoes.append("Investir na melhoria da qualidade das aulas.")
    if media_internacionalizacao < 1:
        recomendacoes.append("Aumentar os esforços de internacionalização.")
    if media_relevancia_social < 3:
        recomendacoes.append("Focar em projetos com maior impacto social.")

    # Preparar os resultados para exibição
    resultados = {
        'media_qualidade_aulas': media_qualidade_aulas,
        'melhor_programa': melhor_programa,
        'pior_programa': pior_programa,
        'media_infraestrutura': media_infraestrutura,
        'media_relacionamento_discentes': media_relacionamento_discentes,
        'media_conhecimento_regimento': media_conhecimento_regimento,
        'media_internacionalizacao': media_internacionalizacao,
        'media_relevancia_social': media_relevancia_social,
        'dificuldades_capes': dificuldades_capes.to_dict(),
        'media_sentimento_programa': media_sentimento_programa,
        'grafico_qualidade_aulas': grafico_qualidade_aulas,
        'recomendacoes': recomendacoes
    }

    import ace_tools as tools; tools.display_dataframe_to_user(name="Simulação de Análise Coordenadores", dataframe=pd.DataFrame([resultados]))