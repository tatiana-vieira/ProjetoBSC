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
avaliacaodocente_route = Blueprint('avaliacaodocente', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Verificar se o diretório de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Verifica se o arquivo tem uma extensão permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@avaliacaodocente_route.route('/importar_planilhadocente', methods=['GET', 'POST'])
def importar_planilhadocente():
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
            return redirect(url_for('avaliacaodocente.gerar_graficos_completos_docentes', filename=filename))

    return render_template('importar_planilhadocente.html')


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

    df.replace({'Sim': 1, 'NÃO': 0, 'Não': 0, 'Nao': 0}, inplace=True)
    
    for col in colunas:
        df[col] = df[col].apply(calcular_media_digitos)  # Aplicar a função de média dos dígitos
    return df



@avaliacaodocente_route.route('/gerar_graficos_completos_docentes')
def gerar_graficos_completos_docentes():
    graficos = []

    # Receber o nome do arquivo da URL
    filename = request.args.get('filename')
    
    if not filename:
        flash('Nenhum arquivo selecionado para gerar gráficos', 'danger')
        return redirect(url_for('avaliacaodocente.importar_planilhadocente'))
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        flash('Arquivo não encontrado', 'danger')
        return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

    try:
        # Tentar ler o arquivo CSV e remover o BOM
        with open(file_path, 'r', encoding='utf-8-sig') as f:
           docente = pd.read_csv(f, delimiter=';')
           print(f"Colunas no arquivo CSV: {docente.columns}")

        # Renomear as colunas como no seu Colab
        docente.rename({
            'A qual  programa esta vinculado?':'programa',
            'Ha quanto tempo esta vinculado ao referido Programas de Pos-Graduacao?':'tempo_programa',
            'Como voce avalia a qualidade das aulas e do material utilizado?[Qualidade das aulas]':'Qualidade_aulas',
            'Como voce avalia a qualidade das aulas e do material utilizado? [Material didatico utilizado nas disciplinas]':'Material_didatico',
            'Como voce avalia a qualidade das aulas e do material utilizado? [Acervo disponivel para consulta]':'Acervo_disponivel',
            'Como voce avalia a infraestrutura do programa? [Infraestrutura geral]':'Infraestrutura_geral',
            'Como voce avalia a infraestrutura do programa? [Laboratorios de pesquisa/Salas de estudo]':'Laboratorio_Salas',
            'Como voce avalia a infraestrutura do programa? [Insumos para pesquisa]':'Insumos_ pesquisa',
            'Como voce avalia o relacionamento entre voce e: [os discentes]':'relacionamento_discentes',
            'Como voce avalia o relacionamento entre voce e: [os demais professores do programa]':'relacionamento_ professores',
            'Como voce avalia o relacionamento entre voce e: [a comissao coordenadora]':'relacionamento_coordenador',
            'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'relacionamento_secretaria',
            'Como voce avalia a gestao do programa? [Processo de gestao/Administrativo do Programa]':'gestao_administrativa',
            'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizacao_ programa',
            'Como voce avalia o seu conhecimento acerca: [do seu papel enquanto orientador]':'papel_orientador',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Interno do Programa]':'regimento_interno',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Geral da Pos-Graduacao]':'regimento_geral',
            'Como voce avalia o seu conhecimento acerca: [normas Capes]':'normas_capes',
            'Como voce avalia o seu conhecimento acerca: [processo de avaliacao da Capes]':'avaliacao_capes',
            'Em relacao aos PROJETOS DE PESQUISA orientados por voce nesse Programa, voce esta:':'orientados_voce',
            'Em relacao a sua PRODUcaO CIENTiFICA relacionada a esse Programa, voce esta:':'producao_cientifica',
            'Voce acredita que os projetos de pesquisa orientados por voce nesse Programa possuem relevancia e pertinencia social?':'orientados_relevancia_social',
            'Voce acredita que os projetos de pesquisa orientados por voce nesse Programa possuem relevancia e pertinencia econômica?':'orientados_ relevancia_economica',
            'Voce acredita que os projetos de pesquisa orientados por voce nesse Programa promovem avanco cientifico?':'orientados_avanco_cientifico',
            'O seu Programa possui visao, missao e objetivos claros?':'visao-missao-objetivos',
            'Voce acredita que os projetos de pesquisa orientados por você nesse programa estão alinhados com o objetivo e missao de seu Programa?':'projetos_objetivo-missao',
            'Quais são os principais atores que podem ser impactados pelas pesquisas sob sua orientacao nesse Programa e das producoes cientificas delas decorrentes? (Marque todas que se aplicam).':'ator_producao cientifica',
            'Voce tem iniciativa de prover captação de recurso externo para o desenvolvimento de seus projetos de pesquisa (exceto bolsa)?':'recurso_externo',
            'Na sua opiniao, o que e preciso para que o seu Programa tenha producao de conhecimento cientifico e tecnologico qualificado, reconhecido pela comunidade científica internacional da área em que atua?':'producao_internacional',
            'Produção de inovacaão tecnologica e uma prioridade em seu programa de pos-graduacao?':'inovacao_tecnologica_programa',
            'Voce acredita que a linha de pesquisa em que atua nesse Programa se destaca pela producao de inovacao tecnologica?':'linha_inovacao_tecnologica',
            'Voce ja depositou alguma patente proveniente dos resultados das pesquisas por você orientadas nesse Programa, ou possui isso como um dos objetivos de algum desses projetos de pesquisa?':'patente',
            'Alguma tecnologia de APLICAcaO SOCIAL ja foi criada como resultado das pesquisas por voce orientadas nesse Programa, ou possui isso como um dos objetivos de algum desses projetos de pesquisa?':'tecnologia_social_orientada',
            'Os resultados das pesquisas por você orientadas ja foram apresentados em algum evento voltado para a COMUNIDADE, ou pretende apresentar?':'projetos_orientados_sociedade',
            'Os resultados das pesquisas por você orientadas ja foram apresentados em algum evento CIENTiFICO, ou pretende apresentar?':'projetos_orientados_evento_cientifico',
            'Os projetos de pesquisa sob sua orientação poderao gerar solucoes para os problemas que a sociedade enfrenta ou vira a enfrentar?':'projetos_orientados_solucoes_sociedade',
            'Quais os principais impactos sociais a serem promovidos por seus projetos de pesquisa? (Marque todas aplicaveis)':'impactos_sociais',
            'Qual o nivel de internacionalização do seu programa?':'nivel_internacionalizacao',
            'No momento, ha interesse por parte do seu Programa de Pos-Graduacao em iniciar um processo de Internacionalizacao?':'interesse_ programa_internacionalizacao',
            'Voce se sente preparado para a internacionalizacao do seu Programa de Pos-Graduacao?':'voce_preparado_internacionalizacao',
            'Voce entende que o seu Programa de Pos-Graduacao esta preparado para a internacionalizacao?':'programa_ preparado_internacionalizacao',
            'Voce possui projetos de pesquisa em parceria com instituicoes internacionais de pesquisa ou ensino?':'projetos_instituicoes_internacionais',
            'Qual o seu nivel de proficiencia em lingua inglesa?':'proficiencia_ingles',
            'Sinto-me capacitado para oferecer disciplinas em lingua inglesa:':'ministrar_ingles',
            'Qual o seu programa de pos-graduacao?':'programa',
            'Gostaria de adicionar algum comentario referente ao Programa de Pos-Graduacao em questao?':'comentario_programa',
            'Gostaria de adicionar algum comentario referente a Pró-Reitoria de Pesquisa e Pos-Graduacao?':'comentario_PRPPG'
            }, axis=1, inplace=True)

       # Verificar se as colunas necessárias estão presentes
        required_columns = ['Qualidade_aulas', 'Material_didatico', 'Infraestrutura_geral']
       
        # Aplicar a função de cálculo da média dos dígitos
        docente= limpar_e_converter_para_numeric(docente, required_columns)
        print(docente.head(), flush=True)

        # Create a dictionary to map the text to numeric values
        mapping = {
            'Menos de 4 anos': 2,  # Midpoint of less than 4 years
            'Entre 4 e 12 anos': 8,  # Midpoint of 4 to 12 years
            'Mais de 12 anos': 15  # Arbitrary value for more than 12 years
        }

        # Apply the mapping to the 'tempo_programa' column
        docente['tempo_programa_numeric'] = docente['tempo_programa'].map(mapping)

        # Now the 'tempo_programa_numeric' column will have the numeric values
        print(docente[['tempo_programa', 'tempo_programa_numeric']].head())

        # Criar novas colunas calculadas (médias)
        docente['Media_Qualidade_Aulas'] = docente[['Qualidade_aulas', 'Material_didatico', 'Infraestrutura_geral']].mean(axis=1)

        # Gráfico de barras - Avaliação da qualidade das aulas
        fig1, ax1 = plt.subplots()
        ax1.bar(docente['Qualidade_aulas'].value_counts().index, 
                docente['Qualidade_aulas'].value_counts())
        ax1.set_title('Distribuição da Qualidade das Aulas')
        ax1.set_xlabel('Qualidade das Aulas')
        ax1.set_ylabel('Número de docentes')
        img1 = io.BytesIO()
        plt.savefig(img1, format='png')
        img1.seek(0)
        graficos.append(base64.b64encode(img1.getvalue()).decode('utf-8'))
        plt.close(fig1)

        # Histograma de Proficiência em Inglês
        fig2, ax2 = plt.subplots()
        ax2.hist(docente['proficiencia_ingles'], bins=10, color='skyblue')
        ax2.set_title('Distribuição de Nível de Proficiência em Inglês')
        ax2.set_xlabel('Nível de Proficiência')
        ax2.set_ylabel('Número de Docente')
        img2 = io.BytesIO()
        plt.savefig(img2, format='png')
        img2.seek(0)
        graficos.append(base64.b64encode(img2.getvalue()).decode('utf-8'))
        plt.close(fig2)

        # Boxplot de Formação vs Qualidade das Aulas
        fig3, ax3 = plt.subplots()
        sns.boxplot(x='proficiencia_ingles', y='Qualidade_aulas', data=docente, ax=ax3)
        ax3.set_title('Nível de Proficiencia vs Qualidade das Aulas')
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
        sns.lineplot(x='tempo_programa', y='Qualidade_aulas', data=docente, ax=ax4)
        ax4.set_title('Tendência da Qualidade das Aulas ao Longo dos Anos')
        ax4.set_xlabel('Tempo de programa')
        ax4.set_ylabel('Qualidade das Aulas')
        img4 = io.BytesIO()
        plt.savefig(img4, format='png')
        img4.seek(0)
        graficos.append(base64.b64encode(img4.getvalue()).decode('utf-8'))
        plt.close(fig4)

        # Mapa de calor - Correlação entre variáveis
        fig5, ax5 = plt.subplots(figsize=(10, 7))
        sns.heatmap(docente[['Qualidade_aulas', 'proficiencia_ingles']].corr(), 
                    annot=True, cmap='coolwarm', linewidths=0.4, ax=ax5)
        ax5.set_title('Mapa de Calor das Correlações')
        img5 = io.BytesIO()
        plt.savefig(img5, format='png')
        img5.seek(0)
        graficos.append(base64.b64encode(img5.getvalue()).decode('utf-8'))
        plt.close(fig5)

        # Gráfico de violino para a Média de Qualidade das Aulas
        fig6, ax6 = plt.subplots(figsize=(10, 6))  # Definir o tamanho do gráfico
        sns.violinplot(y=docente['Media_Qualidade_Aulas'], ax=ax6, color='lightgreen')

        # Título e rótulos
        ax6.set_title('Distribuição da Média de Qualidade das Aulas', fontsize=16)
        ax6.set_ylabel('Média de Avaliação', fontsize=14)

        # Adicionar anotação com a média
        media_valor = docente['Media_Qualidade_Aulas'].mean()
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
        return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

    # Retornar o template com os gráficos gerados
    return render_template('dashboard_docente.html', graficos=graficos)

# Inicializar o analisador de sentimentos
nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Função para processar o sentimento
def analisar_sentimento(texto):
    return sid.polarity_scores(texto)


@avaliacaodocente_route.route('/analisar_sentimentos', methods=['GET'])
def analisar_sentimentos():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/docente.csv'  # Altere para o caminho correto do arquivo
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

        docente = pd.read_csv(file_path, delimiter=';')

        

        # Exibir as colunas do arquivo CSV para depuração
        print(f"Colunas do CSV carregado: {docente.columns}")

        # Verificar se as colunas de comentários estão presentes antes de renomeá-las
        if 'comentario sobre o programa' not in docente.columns or \
           'comentario sobre a PRPPG' not in docente.columns:
            print("Colunas de comentários não encontradas:")
            flash('Colunas de comentários não encontradas no arquivo.', 'danger')
            return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

        # Renomear colunas para aplicar a análise de sentimento
        docente.rename({
            'comentario sobre o programa': 'Sentimento_Programa',
            'comentario sobre a PRPPG': 'Sentimento_Pro_Reitoria'
        }, axis=1, inplace=True)

        # Remover linhas vazias das colunas de comentários
        df_comentarios = docente[['Sentimento_Programa', 'Sentimento_Pro_Reitoria']].dropna(how='all')

        if df_comentarios.empty or (df_comentarios['Sentimento_Programa'].isnull().all() and df_comentarios['Sentimento_Pro_Reitoria'].isnull().all()):
            flash('Nenhum comentário suficiente disponível para análise de sentimento.', 'warning')
            return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

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

        return render_template('sentimentodocente.html', grafico_sentimentos=grafico_sentimentos,
                               media_programa=media_sentimentos_programa, media_prppg=media_sentimentos_prppg)

    except Exception as e:
        flash(f"Erro ao processar os sentimentos: {e}", 'danger')
        return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

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

@avaliacaodocente_route.route('/visualizar_resultados', methods=['GET'])
def visualizar_resultados():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/docente.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

        docente = pd.read_csv(file_path, delimiter=';')

        # Verificar se os dados têm distribuição suficiente para treinamento
        print(docente.describe())  # Verificar estatísticas gerais para cada coluna

        # Avaliar os sentimentos do Programa de Pós-Graduação
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()

        # Gráfico de barras de sentimentos por ano de ingresso
        # Ajustar o gráfico com rotação dos rótulos no eixo X
        # Aumentar o tamanho da imagem com figsize
      # Aumentar o tamanho da imagem com figsize
        fig, ax = plt.subplots(figsize=(14, 8))  # Ajuste os valores para o tamanho desejado
        docente['Media_Qualidade_Aulas'].plot(kind='bar', ax=ax)
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
        return render_template('resultadodocente.html', 
                               grafico_sentimentos_ingresso=grafico_sentimentos_ingresso,
                               mse_otimizado=mse_otimizado,
                               media_programa=media_sentimentos_programa)

    except Exception as e:
        flash(f"Erro ao processar os resultados: {e}", 'danger')
        return redirect(url_for('avaliacaodocente.importar_planilhadocente'))


################################################################################################
# Função principal que substitui XGBRegressor por GradientBoostingRegressor
@avaliacaodocente_route.route('/analisar_dados_ia', methods=['GET'])
def analisar_dados_ia():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/docente.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

        # Carregar os dados do CSV
        docente = pd.read_csv(file_path, delimiter=';')

        # Renomear as colunas como no seu Colab
        docente.rename({
            

 'A qual  programa esta vinculado?':'programa',
            'Ha quanto tempo esta vinculado ao referido Programas de Pos-Graduacao?':'tempo_programa',
            'Como voce avalia a qualidade das aulas e do material utilizado?[Qualidade das aulas]':'Qualidade_aulas',
            'Como voce avalia a qualidade das aulas e do material utilizado? [Material didatico utilizado nas disciplinas]':'Material_didatico',
            'Como voce avalia a qualidade das aulas e do material utilizado? [Acervo disponivel para consulta]':'Acervo_disponivel',
            'Como voce avalia a infraestrutura do programa? [Infraestrutura geral]':'Infraestrutura_geral',
            'Como voce avalia a infraestrutura do programa? [Laboratorios de pesquisa/Salas de estudo]':'Laboratorio_Salas',
            'Como voce avalia a infraestrutura do programa? [Insumos para pesquisa]':'Insumos_ pesquisa',
            'Como voce avalia o relacionamento entre voce e: [os discentes]':'relacionamento_discentes',
            'Como voce avalia o relacionamento entre voce e: [os demais professores do programa]':'relacionamento_ professores',
            'Como voce avalia o relacionamento entre voce e: [a comissao coordenadora]':'relacionamento_coordenador',
            'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'relacionamento_secretaria',
            'Como voce avalia a gestao do programa? [Processo de gestao/Administrativo do Programa]':'gestao_administrativa',
            'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizacao_ programa',
            'Como voce avalia o seu conhecimento acerca: [do seu papel enquanto orientador]':'papel_orientador',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Interno do Programa]':'regimento_interno',
            'Como voce avalia o seu conhecimento acerca: [do Regimento Geral da Pos-Graduacao]':'regimento_geral',
            'Como voce avalia o seu conhecimento acerca: [normas Capes]':'normas_capes',
            'Como voce avalia o seu conhecimento acerca: [processo de avaliacao da Capes]':'avaliacao_capes',
            'Em relacao aos PROJETOS DE PESQUISA orientados por voce nesse Programa, voce esta:':'orientados_voce',
            'Em relacao a sua PRODUcaO CIENTiFICA relacionada a esse Programa, voce esta:':'producao_cientifica',
            'Voce acredita que os projetos de pesquisa orientados por voce nesse Programa possuem relevancia e pertinencia social?':'orientados_relevancia_social',
            'Voce acredita que os projetos de pesquisa orientados por voce nesse Programa possuem relevancia e pertinencia econômica?':'orientados_ relevancia_economica',
            'Voce acredita que os projetos de pesquisa orientados por voce nesse Programa promovem avanco cientifico?':'orientados_avanco_cientifico',
            'O seu Programa possui visao, missao e objetivos claros?':'visao-missao-objetivos',
            'Voce acredita que os projetos de pesquisa orientados por você nesse programa estão alinhados com o objetivo e missao de seu Programa?':'projetos_objetivo-missao',
            'Quais são os principais atores que podem ser impactados pelas pesquisas sob sua orientacao nesse Programa e das producoes cientificas delas decorrentes? (Marque todas que se aplicam).':'ator_producao cientifica',
            'Voce tem iniciativa de prover captação de recurso externo para o desenvolvimento de seus projetos de pesquisa (exceto bolsa)?':'recurso_externo',
            'Na sua opiniao, o que e preciso para que o seu Programa tenha producao de conhecimento cientifico e tecnologico qualificado, reconhecido pela comunidade científica internacional da área em que atua?':'producao_internacional',
            'Produção de inovacaão tecnologica e uma prioridade em seu programa de pos-graduacao?':'inovacao_tecnologica_programa',
            'Voce acredita que a linha de pesquisa em que atua nesse Programa se destaca pela producao de inovacao tecnologica?':'linha_inovacao_tecnologica',
            'Voce ja depositou alguma patente proveniente dos resultados das pesquisas por você orientadas nesse Programa, ou possui isso como um dos objetivos de algum desses projetos de pesquisa?':'patente',
            'Alguma tecnologia de APLICAcaO SOCIAL ja foi criada como resultado das pesquisas por voce orientadas nesse Programa, ou possui isso como um dos objetivos de algum desses projetos de pesquisa?':'tecnologia_social_orientada',
            'Os resultados das pesquisas por você orientadas ja foram apresentados em algum evento voltado para a COMUNIDADE, ou pretende apresentar?':'projetos_orientados_sociedade',
            'Os resultados das pesquisas por você orientadas ja foram apresentados em algum evento CIENTiFICO, ou pretende apresentar?':'projetos_orientados_evento_cientifico',
            'Os projetos de pesquisa sob sua orientação poderao gerar solucoes para os problemas que a sociedade enfrenta ou vira a enfrentar?':'projetos_orientados_solucoes_sociedade',
            'Quais os principais impactos sociais a serem promovidos por seus projetos de pesquisa? (Marque todas aplicaveis)':'impactos_sociais',
            'Qual o nivel de internacionalização do seu programa?':'nivel_internacionalizacao',
            'No momento, ha interesse por parte do seu Programa de Pos-Graduacao em iniciar um processo de Internacionalizacao?':'interesse_ programa_internacionalizacao',
            'Voce se sente preparado para a internacionalizacao do seu Programa de Pos-Graduacao?':'voce_preparado_internacionalizacao',
            'Voce entende que o seu Programa de Pos-Graduacao esta preparado para a internacionalizacao?':'programa_ preparado_internacionalizacao',
            'Voce possui projetos de pesquisa em parceria com instituicoes internacionais de pesquisa ou ensino?':'projetos_instituicoes_internacionais',
            'Qual o seu nivel de proficiencia em lingua inglesa?':'proficiencia_ingles',
            'Sinto-me capacitado para oferecer disciplinas em lingua inglesa:':'ministrar_ingles',
            'Qual o seu nivel de formacao?':'nivel_formacao',
            'Qual o seu programa de pos-graduacao?':'programa',
            'Gostaria de adicionar algum comentario referente ao Programa de Pos-Graduacao em questao?':'comentario_programa',
            'Gostaria de adicionar algum comentario referente a Pró-Reitoria de Pesquisa e Pos-Graduacao?':'comentario_PRPPG'
            }, axis=1, inplace=True)           


        # 1. Garantir que todas as colunas são numéricas
        colunas_qualidade = ['Qualidade_aulas', 'Material_didatico','Acervo_disponivel']
        colunas_organizacao = ['regimento_interno', 'papel_orientador', 'normas_capes',
                               'avaliacao_capes','regimento_geral']
        colunas_infraestrutura = ['Insumos_ pesquisa','Infraestrutura_geral', 'Laboratorio_Salas']
        colunas_relacionamentos = ['relacionamento_ professores', 'relacionamento_coordenador',
                                   'relacionamento_discentes', 'relacionamento_secretaria']
        colunas_internacionalizacao = ['interesse_ programa_internacionalizacao', 'voce_preparado_internacionalizacao',
                                       'programa_ preparado_internacionalizacao', 'proficiencia_ingles','projetos_instituicoes_internacionais','ministrar_ingles']


       # Converter as colunas para numéricas
        def converter_para_numerico(df, colunas):
            for coluna in colunas:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
            return df

        docente = converter_para_numerico(docente, colunas_qualidade + colunas_organizacao + colunas_infraestrutura + colunas_relacionamentos,colunas_internacionalizacao)

        # Agrupar os dados por programa
        agrupado_por_programa = docente.groupby('programa')

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

        # [Resto do código permanece inalterado]

    except Exception as e:
        flash(f"Erro ao processar os dados: {e}", 'danger')
        return redirect(url_for('avaliacaodocente.importar_planilhadocente'))

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
        return render_template('recomendacaodocente.html', recomendacoes_por_programa=recomendacoes_por_programa)

    except Exception as e:
        flash(f"Erro ao processar os dados: {e}", 'danger')
        return redirect(url_for('avaliacaodocente.importar_planilhadocente'))