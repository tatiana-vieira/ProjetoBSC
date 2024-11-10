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


# Configurações globais de estilo para os gráficos
plt.rcParams.update({
    'figure.figsize': (8, 6),  # Tamanho padrão dos gráficos (ajuste conforme necessário)
    'axes.titlesize': 16,      # Tamanho do título dos gráficos
    'axes.labelsize': 14,      # Tamanho dos rótulos dos eixos
    'xtick.labelsize': 12,     # Tamanho das marcas no eixo X
    'ytick.labelsize': 12,     # Tamanho das marcas no eixo Y
    'legend.fontsize': 12      # Tamanho da fonte da legenda, se usar legendas
})

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
        "sem condicoes de avaliar": np.nan,
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
        colunas_requeridas = ['Infraestrutura_geral', 'acompanhamento_discentes', 'tempo_programa']
        colunas_faltantes = [col for col in colunas_requeridas if col not in discentecurso.columns]
        if colunas_faltantes:
                print(f"Colunas faltantes após renomeação: {colunas_faltantes}")

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
        # Carregar o CSV e renomear colunas
        discentecurso = pd.read_csv(file_path, delimiter=';')
        discentecurso = renomear_colunas(discentecurso)
        discentecurso = limpar_dados(discentecurso)


        # Calcular o MSE da Regressão automaticamente
        resultado_regressao = aplicar_regressao_discente(discentecurso)

        # Converter colunas necessárias para numérico
        required_columns = ['Qualidade_aulas', 'Material_didatico', 'Infraestrutura_geral']
        discentecurso[required_columns] = discentecurso[required_columns].apply(pd.to_numeric, errors='coerce')

        # Estatísticas Descritivas
        estatisticas_html = gerar_estatisticas_descritivas(discentecurso)
        
        # Configurações de gráfico
        figsize = (10, 6)
        title_fontsize = 18
        label_fontsize = 14

        # Gráfico 1: Distribuição de Nível de Proficiência em Inglês
        fig, ax = plt.subplots(figsize=figsize)
        ax.hist(discentecurso['proficiencia_ingles'].dropna(), bins=10, color='skyblue')
        ax.set_title('Distribuição de Nível de Proficiência em Inglês', fontsize=title_fontsize)
        ax.set_xlabel('Nível de Proficiência', fontsize=label_fontsize)
        ax.set_ylabel('Número de Alunos', fontsize=label_fontsize)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)

        # Gráfico 2: Violino da Média de Qualidade das Aulas
        fig, ax = plt.subplots(figsize=figsize)
        sns.violinplot(y=discentecurso['Qualidade_aulas'], ax=ax, color='lightgreen')
        ax.set_title('Distribuição da Média de Qualidade das Aulas', fontsize=title_fontsize)
        ax.set_ylabel('Média de Avaliação', fontsize=label_fontsize)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)

        # Gráfico 3: Boxplot de Formação vs Qualidade das Aulas
        fig, ax = plt.subplots(figsize=figsize)
        sns.boxplot(x='formacao', y='Qualidade_aulas', data=discentecurso, ax=ax)
        ax.set_title('Nível de Formação vs Qualidade das Aulas', fontsize=title_fontsize)
        ax.set_xlabel('Formação', fontsize=label_fontsize)
        ax.set_ylabel('Qualidade das Aulas', fontsize=label_fontsize)
        plt.xticks(rotation=45)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)

        # Gráfico 4: Tendência da Qualidade das Aulas ao Longo dos Anos
        fig, ax = plt.subplots(figsize=figsize)
        sns.lineplot(x='ingresso', y='Qualidade_aulas', data=discentecurso, ax=ax)
        ax.set_title('Tendência da Qualidade das Aulas ao Longo dos Anos', fontsize=title_fontsize)
        ax.set_xlabel('Ano de Ingresso', fontsize=label_fontsize)
        ax.set_ylabel('Qualidade das Aulas', fontsize=label_fontsize)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)

        # Gráfico 5: Mapa de Calor das Correlações
        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(discentecurso[['Qualidade_aulas', 'proficiencia_ingles']].corr(), annot=True, cmap='coolwarm')
        ax.set_title('Mapa de Calor das Correlações', fontsize=title_fontsize)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)

        # Gráfico de Satisfação com Relacionamentos
        fig, ax = plt.subplots(figsize=(10, 6))
        try:
            # Converter colunas para numérico, ignorando erros
            rel_cols = ['Relacionamento_colegas', 'Relacionamento_orientador', 
                        'Relacionamento_coordenador', 'Relacionamento_secretaria']
            discentecurso[rel_cols] = discentecurso[rel_cols].apply(pd.to_numeric, errors='coerce')

            # Verificar se há dados suficientes após a conversão
            if discentecurso[rel_cols].dropna().empty:
                raise ValueError("Sem dados suficientes para gerar o gráfico de Satisfação com Relacionamentos.")

            # Calcular a média para cada tipo de relacionamento
            media_relacionamentos = discentecurso[rel_cols].mean()

            # Plotar o gráfico
            media_relacionamentos.plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title('Satisfação com Relacionamentos', fontsize=18)
            ax.set_xlabel('Tipo de Relacionamento', fontsize=14)
            ax.set_ylabel('Avaliação Média', fontsize=14)
            ax.set_xticklabels(media_relacionamentos.index, rotation=45, ha='right')

            # Exibir os valores no topo de cada barra
            for i, valor in enumerate(media_relacionamentos):
                ax.text(i, valor + 0.05, f'{valor:.2f}', ha='center', va='bottom')

            plt.tight_layout()
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
            plt.close(fig)
        except Exception as e:
            print(f"Erro ao gerar gráfico de Satisfação com Relacionamentos: {e}")
            flash(f"Erro ao gerar gráfico de Satisfação com Relacionamentos: {e}", 'danger')


        # Gráfico 7: Relevância da Pesquisa
        pesquisa_cols = ['pesquisa_relevancia_social', 'pesquisa relevancia economica', 'pesquisa relevancia ambiental']
        fig, ax = plt.subplots(figsize=figsize)
        media_pesquisa = discentecurso[pesquisa_cols].mean()
        media_pesquisa.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        ax.set_title('Relevância da Pesquisa', fontsize=title_fontsize)
        ax.set_xlabel('Tipo de Relevância', fontsize=label_fontsize)
        ax.set_ylabel('Avaliação Média', fontsize=label_fontsize)
        plt.xticks(rotation=45)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
        plt.close(fig)

        # Renderizar o template com todos os gráficos
        return render_template(
                    'dashboard_discenteia.html',
                    graficos=graficos,
                    estatisticas=estatisticas_html,
                    resultado_regressao=resultado_regressao
                )
    except Exception as e:
        flash(f"Erro ao gerar gráficos: {str(e)}", 'danger')
        return redirect(url_for('discente.importar_discente'))

def gerar_graficos_satisfacao(discentecurso):
    graficos = []

    # Configuração global para o tamanho dos gráficos
    figsize = (10, 6)
    title_fontsize = 18
    label_fontsize = 14

    # Gráfico 1: Satisfação com Relacionamentos
    try:
        rel_cols = ['Relacionamento_orientador', 'Relacionamento_coordenador', 
                    'Relacionamento_secretaria', 'Relacionamento_colegas']
        discentecurso[rel_cols] = discentecurso[rel_cols].apply(pd.to_numeric, errors='coerce')
        
        if not discentecurso[rel_cols].empty:
            media_relacionamentos = discentecurso[rel_cols].mean()
            fig, ax = plt.subplots(figsize=figsize)
            media_relacionamentos.plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title('Satisfação com Relacionamentos', fontsize=title_fontsize)
            ax.set_xlabel('Tipo de Relacionamento', fontsize=label_fontsize)
            ax.set_ylabel('Avaliação Média', fontsize=label_fontsize)
            ax.set_xticklabels(media_relacionamentos.index, rotation=45, ha='right')
            plt.tight_layout()

            # Salvar gráfico em memória
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
            plt.close(fig)
    except Exception as e:
        print(f"Erro ao gerar gráfico de Satisfação com Relacionamentos: {e}")

    # Gráfico 2: Relevância da Pesquisa
    try:
        pesquisa_cols = ['pesquisa_relevancia_social', 'pesquisa relevancia economica', 
                         'pesquisa relevancia ambiental']
        discentecurso[pesquisa_cols] = discentecurso[pesquisa_cols].apply(pd.to_numeric, errors='coerce')

        if not discentecurso[pesquisa_cols].empty:
            media_pesquisa = discentecurso[pesquisa_cols].mean()
            fig, ax = plt.subplots(figsize=figsize)
            media_pesquisa.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
            ax.set_title('Relevância da Pesquisa', fontsize=title_fontsize)
            ax.set_xlabel('Tipo de Relevância', fontsize=label_fontsize)
            ax.set_ylabel('Avaliação Média', fontsize=label_fontsize)
            ax.set_xticklabels(media_pesquisa.index, rotation=45, ha='right')
            plt.tight_layout()

            # Salvar gráfico em memória
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
            plt.close(fig)
    except Exception as e:
        print(f"Erro ao gerar gráfico de Relevância da Pesquisa: {e}")

    return graficos


##############################3
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

@discente_route.route('/analise_clusterizacao')
def analise_clusterizacao_discente():
    try:
        # Definir o caminho do arquivo CSV
        file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
        if not os.path.exists(file_path):
            flash('Arquivo "discente.csv" não encontrado.', 'danger')
            return redirect(url_for('discente.importar_discente'))
        
        # Carregar o CSV
        discentecurso = pd.read_csv(file_path, delimiter=';')
        discentecurso = renomear_colunas(discentecurso)
        discentecurso = limpar_dados(discentecurso)

        # Verificar colunas necessárias
        features = ['Qualidade_aulas', 'Infraestrutura_geral', 'Relacionamento_coordenador']
        colunas_faltantes = [col for col in features if col not in discentecurso.columns]
        if colunas_faltantes:
            flash(f"Colunas ausentes: {colunas_faltantes}", 'danger')
            return redirect(url_for('discente.importar_discente'))

        # Convertendo colunas para numérico
        discentecurso[features] = discentecurso[features].apply(pd.to_numeric, errors='coerce')
        discentecurso.dropna(subset=features, inplace=True)

        if discentecurso.empty:
            flash("Dados insuficientes para realizar clustering.", 'danger')
            return redirect(url_for('discente.importar_discente'))

        # Aplicar KMeans Clustering
        kmeans = KMeans(n_clusters=3, random_state=42)
        discentecurso['Cluster'] = kmeans.fit_predict(discentecurso[features])

        # Gerar gráfico
        fig, ax = plt.subplots()
        scatter = ax.scatter(
            discentecurso[features[0]], 
            discentecurso[features[1]], 
            c=discentecurso['Cluster'], cmap='viridis'
        )
        ax.set_title('Resultado de Clustering')
        ax.set_xlabel(features[0])
        ax.set_ylabel(features[1])
        plt.colorbar(scatter)

        # Salvar gráfico em buffer
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        grafico = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close(fig)

        return render_template(
            'clusteringdiscente.html', 
            grafico=grafico,
            features=features
    )
    except Exception as e:
        flash(f"Erro ao realizar análise de clustering: {e}", 'danger')
        return redirect(url_for('discente.importar_discente'))

def aplicar_regressao_discente(df):
    try:
        required_columns = ['Infraestrutura_geral', 'Qualidade_aulas']
        if not all(col in df.columns for col in required_columns):
            return None

        df[required_columns] = df[required_columns].apply(pd.to_numeric, errors='coerce')
        df.dropna(subset=required_columns, inplace=True)

        X = df[['Infraestrutura_geral']]
        y = df['Qualidade_aulas']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        return f"MSE da Regressão: {mse:.2f}"

    except Exception as e:
        print(f"Erro ao aplicar regressão: {e}")
        return None



# Rota para executar análise

def gerar_estatisticas_descritivas(df):
    # Calcula as estatísticas descritivas e converte para HTML
    estatisticas = df.describe().transpose()
    estatisticas_html = estatisticas.to_html(classes="table table-striped")
    return estatisticas_html



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

@discente_route.route('/exibir_recomendacoes_discente', methods=['GET'])
def exibir_recomendacoes_discente():
   
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
        return render_template('recomendacaoprogdiscente.html', recomendacoes=recomendacoes_programa)
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

# Função para análise de sentimentos usando VADER
def analisar_sentimento(texto):
    analyser = SentimentIntensityAnalyzer()
    return analyser.polarity_scores(texto)


################### Analise sentimentos ##############################################
@discente_route.route('/analisar_sentimentosdiscente', methods=['GET'])
def analisar_sentimentosdiscente():
    try:
        # Definir o caminho do arquivo CSV
        file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('discente.importar_discente'))

        # Carregar e renomear colunas do CSV
        discente = pd.read_csv(file_path, delimiter=';')
        discente = renomear_colunas(discente)

        # Renomear colunas relevantes para análise de sentimento
        discente.rename({
            'comentario_programa': 'Sentimento_Programa',
            'comentario_PRPPG': 'Sentimento_Pro_Reitoria',
            'preparado_internacionalizacao': 'Sentimento_Internacional'
        }, axis=1, inplace=True)

        # Selecionar colunas de sentimento e substituir valores nulos por strings vazias
        colunas_sentimento = ['Sentimento_Programa', 'Sentimento_Pro_Reitoria', 'Sentimento_Internacional']
        df_comentarios = discente[colunas_sentimento].fillna('')

        # Verificar se há comentários disponíveis
        if df_comentarios.empty:
            flash('Nenhum comentário disponível para análise de sentimento.', 'warning')
            return redirect(url_for('discente.importar_discente'))

        # Função para analisar o sentimento usando VADER
        analyser = SentimentIntensityAnalyzer()
        def analisar_sentimento(texto):
            if texto:
                return analyser.polarity_scores(str(texto))['compound']
            return 0

        # Aplicar análise de sentimentos nas colunas
        df_comentarios['Programa_Score'] = df_comentarios['Sentimento_Programa'].apply(analisar_sentimento)
        df_comentarios['Pro_Reitoria_Score'] = df_comentarios['Sentimento_Pro_Reitoria'].apply(analisar_sentimento)
        df_comentarios['Internacional_Score'] = df_comentarios['Sentimento_Internacional'].apply(analisar_sentimento)

        # Calcular a média dos sentimentos (ignorando valores NaN)
        media_sentimentos_programa = df_comentarios['Programa_Score'].mean()
        media_sentimentos_prppg = df_comentarios['Pro_Reitoria_Score'].mean()
        media_sentimentos_internacional = df_comentarios['Internacional_Score'].mean()

        # Contagem de sentimentos para o Programa
        total_negativos = len(df_comentarios[df_comentarios['Programa_Score'] < 0])
        total_positivos = len(df_comentarios[df_comentarios['Programa_Score'] > 0])
        total_neutros = len(df_comentarios[df_comentarios['Programa_Score'] == 0])

        # Gerar gráfico de distribuição de sentimentos
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.bar(['Negativos', 'Positivos', 'Neutros'], [total_negativos, total_positivos, total_neutros], color=['red', 'green', 'gray'])
        ax.set_title('Distribuição de Sentimentos sobre o Programa de Pós-Graduação')
        ax.set_xlabel('Tipo de Sentimento')
        ax.set_ylabel('Número de Comentários')

        # Salvar o gráfico em buffer
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        grafico_sentimentos = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close(fig)

        # Renderizar o template com as médias de sentimentos e o gráfico
        return render_template('sentimentosdiscente.html',
                               grafico_sentimentos=grafico_sentimentos,
                               media_programa=round(media_sentimentos_programa, 2) if not pd.isna(media_sentimentos_programa) else 0,
                               media_prppg=round(media_sentimentos_prppg, 2) if not pd.isna(media_sentimentos_prppg) else 0,
                               media_internacional=round(media_sentimentos_internacional, 2) if not pd.isna(media_sentimentos_internacional) else 0)

    except Exception as e:
        flash(f"Erro ao processar os sentimentos: {e}", 'danger')
        return redirect(url_for('discente.importar_discente'))

       
#############3 verficar colunas ###########################
def verificar_colunas(df, colunas):
    colunas_faltantes = [col for col in colunas if col not in df.columns]
    if colunas_faltantes:
        print(f"Colunas faltantes: {colunas_faltantes}")
        return False
    return True

################Dashboard de tendencias"""""""""""""""""""""""""""""
@discente_route.route('/executar_analise_discente')
def executar_analise_discente():
    tipo = request.args.get('tipo')
    file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')

    if not os.path.exists(file_path):
        flash('Arquivo "discente.csv" não encontrado.', 'danger')
        return redirect(url_for('discente.importar_discente'))

    discentecurso = pd.read_csv(file_path, delimiter=';')
    discentecurso = renomear_colunas(discentecurso)
    discentecurso = limpar_dados(discentecurso)

    colunas_requeridas = ['Qualidade_aulas', 'Infraestrutura_geral', 'Relacionamento_orientador']
    if not verificar_colunas(discentecurso, colunas_requeridas):
        flash('Colunas necessárias ausentes.', 'danger')
        return redirect(url_for('discente.importar_discente'))

    if tipo == 'clustering':
        return analise_clusterizacao_discente()
    elif tipo == 'regressao':
        resultado_regressao = aplicar_regressao_discente(discentecurso)
        if resultado_regressao:
            return render_template('regressaodiscente.html', resultado=resultado_regressao)
    
    flash("Tipo de análise inválido.", 'danger')
    return redirect(url_for('discente.importar_discente'))


@discente_route.route('/dashboard_tendencias')
def dashboard_tendencias():
    try:
        file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
        discentecurso = pd.read_csv(file_path, delimiter=';')
        discentecurso = renomear_colunas(discentecurso)
        discentecurso = limpar_dados(discentecurso)

     
        colunas = ['Qualidade_aulas', 'Material_didatico', 'Infraestrutura_geral']
        discentecurso[colunas] = discentecurso[colunas].apply(pd.to_numeric, errors='coerce')
        medias = discentecurso[colunas].mean()

        fig, ax = plt.subplots()
        medias.plot(kind='bar', ax=ax)
        ax.set_title('Média de Indicadores')
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        grafico_tendencias = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close(fig)




        return render_template('dashboardtendedicente.html', grafico_tendencias=grafico_tendencias)
    except Exception as e:
        flash(f"Erro ao gerar dashboard: {e}", 'danger')
        return redirect(url_for('discente.importar_discente'))


############################## analise clusterização #####################################


##########################3 Analise de pesquisa #################################
@discente_route.route('/analise_linha_pesquisa')
def analise_linha_pesquisa():
    try:
        file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
        discentecurso = pd.read_csv(file_path, delimiter=';')
        discentecurso = renomear_colunas(discentecurso)
        discentecurso = limpar_dados(discentecurso)

        # Agrupar por linha de pesquisa
        linhas_pesquisa = discentecurso.groupby('programa').mean()

        fig, ax = plt.subplots()
        linhas_pesquisa.plot(kind='bar', ax=ax)
        ax.set_title('Satisfação por Linha de Pesquisa')
        plt.xticks(rotation=45)
        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        grafico_linha_pesquisa = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close(fig)

        return render_template('linha_pesquisa.html', grafico_linha_pesquisa=grafico_linha_pesquisa)
    
    except Exception as e:
        flash(f"Erro ao analisar por linha de pesquisa: {e}", 'danger')
        return redirect(url_for('discente.importar_discente'))

################ Analise feedback ###############################
@discente_route.route('/feedback_nlp')
def feedback_nlp():
    file_path = os.path.join(UPLOAD_FOLDER, 'discente.csv')
    discente = pd.read_csv(file_path, delimiter=';')
    discente = renomear_colunas(discente)
    comentarios = discente['comentario_programa'].dropna()

    # Análise de sentimento com VADER
    analyser = SentimentIntensityAnalyzer()
    discente['sentimento'] = comentarios.apply(lambda x: analyser.polarity_scores(x)['compound'])
    
    temas_positivos = comentarios[discente['sentimento'] > 0.2]
    temas_negativos = comentarios[discente['sentimento'] < -0.2]

    return render_template('feedback_nlp.html', positivos=temas_positivos, negativos=temas_negativos)
