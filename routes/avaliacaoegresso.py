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
    df.replace("Não se aplica", np.nan, inplace=True)
    df.replace("Nao se aplica", np.nan, inplace=True)



    for col in colunas:
        df[col] = df[col].apply(calcular_media_digitos)  # Aplicar a função de média dos dígitos
    return df

# Definir o blueprint
avaliacaoegresso_route = Blueprint('avaliacaoegresso', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Verificar se o diretório de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Verifica se o arquivo tem uma extensão permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@avaliacaoegresso_route.route('/importar_planilhaegresso', methods=['GET', 'POST'])
def importar_planilhaegresso():
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
            return redirect(url_for('avaliacaoegresso.gerar_graficos_completos_egressos', filename=filename))

    return render_template('importar_planilhaegresso.html')


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

    df.replace({'Sim': 1,'sim':1, 'NÃO': 0, 'Não': 0, 'Nao': 0}, inplace=True)
    
    for col in colunas:
        df[col] = df[col].apply(calcular_media_digitos)  # Aplicar a função de média dos dígitos
    return df

# Função para renomear colunas de forma segura
def renomear_colunas(egresso):
    # Dicionário de colunas para renomear
    colunas_para_renomear = {
                    'Como voce identifica seu genero?':'genero', 
                    'Qual o ultimo nivel de formacao que voce obteve na UNIFEI?':'ultima_formacao',
                    'Qual o seu ano de conclusao?':'ano_conclusao',
                    'A qual programa esteve vinculado?':'programa',
                    'Em uma escala de 0 a 10, o quanto voce recomendaria o Programa em que realizou sua pos-graduacao na UNIFEI?':'recomendacao_programa',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Qualidade das aulas]':'qualidade_aulas',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Material didatico utilizado nas disciplinas]':'material_didatico',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Acervo disponivel para consulta]':'acervo_consulta',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Infraestrutura geral]':'infraestrututra_geral',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Laboratorios de pesquisa/Salas de estudo]':'laboratorios_sala',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Insumos para pesquisa]':'insumos_pesquisa',
                    'Como voce avalia o relacionamento entre voce e: [os colegas]':'relacionamento_colegas',
                    'Como voce avalia o relacionamento entre voce e: [a comissao orientadora]':'relacionamento_orientador',
                    'Como voce avalia o relacionamento entre voce e: [a comissao coordenadora]':'relacionamento_coordenador',
                    'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'relacionamento_secretaria',
                    'Como voce avalia a gestao do programa? [Processo de gestao/Administrativo do Programa]':'administrativo',
                    'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizacao_programa',
                    'Em relacao a sua TESE/DISSERTAcaO, voce ficou:':'satisfacao_dissertacao_tese',
                    'Em relacao a sua PRODUcaO CIENTiFICA, voce ficou satisfeito:':'satisfacao_producao',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia social?':'relevancia_social',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia economico?':'relevancia_economico',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia ambiental?':'relevancia_ambiental',
                    'Voce acredita que a sua pesquisa promoveu o avanco cientifico?':'pesquisa_cientifico',
                    'Voce acredita que sua pesquisa esteve alinhada com missao, visao e objetivos de seu Programa?':'missao-visao-objetivos',
                    'Voce recebeu bolsa de pos-graduacao?':'bolsa',
                    'Para a realizacao de seu projeto de pesquisa houve algum tipo de captacao de recurso externo (exceto bolsa)?':'recurso_externo',
                    'O programa de pos-graduacao em que atuou tem como objetivo a producao de inovacao tecnologica?':'inovacao_programa',
                    'Voce acredita que a linha de pesquisa em que atuou se destaca pela producao de inovacao tecnologica?':'linha_pesquisa_inovacao',
                    'Voce depositou alguma patente proveniente de sua pesquisa?':'patente',
                    'O programa de pos-graduacao em que atuou tem como objetivo a producao de tecnologias de APLICAcaO SOCIAL?':'programa_aplicacao_social',
                    'Alguma tecnologia de aplicacao social foi criada como resultado de sua pesquisa?':'pesquisa_tecnologia_social',
                    'Voce ja apresentou algum resultado de sua pesquisa em algum evento voltado para a sociedade, ou pretende apresentar?':'evento_sociedade',
                    'Voce ja apresentou algum resultado de sua pesquisa em algum evento CIENTiFICO, ou pretende apresentar?':'evento_cientifico',
                    'Sua pesquisa gerou solucões para os problemas que a sociedade enfrenta ou vira a enfrentar?':'solucao_pesquica_sociedade',
                    'Qual foi o principal impacto social promovido por seu projeto de pesquisa? (Marque todas aplicaveis)':'impacto_projeto',
                    'Seu projeto de pesquisa possuiu parcerias com instituicoes internacionais de pesquisa ou ensino?':'parceria_internacional',
                    'Quando aluno da UNIFEI, teve a oportunidade de fazer parte da sua pos-graduacao em outra instituicao (Nacional ou Internacional)?':'aluno_outra_instituicao',
                    'Se sim, onde? Qual nivel? Qual foi o periodo de duracao (mes/ano)?':'lugar_nivel',
                    'Em sua trajetoria profissional, teve a oportunidade de atuar fora do Brasil?':'profissional_exterior',
                    'Caso se sinta a vontade, pedimos que compartilhe como fez para pleitear a oportunidade fora do Brasil.':'pleitear',
                    'Qual sua colocacao profissional atualmente?':'colocacao_profissional_hoje',
                    'Seu emprego esta relacionado a sua area de formacao na pos-graduacao da UNIFEI?':'emprego_formacao',
                    'Qual a sua faixa salarial e/ou de rendimentos em moeda do seu pais atual? Destacamos que esta informacao tem sido requisitada ao Programas de Pos-Graduacao pela Capes e que nao sera divulgada expondo a realidade individual do egresso (em caso de moeda estrangeira, necessario realizar conversao para moeda brasileira).':'faixa_salarial',
                    'Voce teve dificuldade para conseguir o primeiro emprego?':'dificuldade_primeiro_emprego',
                    'Caso tenha tido/tenha dificuldade para conseguir o primeiro emprego, o que poderia ser melhorado no programa, visando maior insercao no mercado de trabalho?':'melhoria_emprego',
                    'Teve bolsa de iniciacao cientifica na graduacao?':'bolsa_cientifica_graduacao',
                    'Voce teve recursos e estrutura fisica suficiente para a conducao dos seus experimentos?':'recursos_experimentos',
                    'Gostariamos de saber sua satisfacao pessoal e profissional com relacao a sua formacao na UNIFEI. Fique a vontade em descreve-las.':'satisfacao_formacao',
                    'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?':'cometario_prppg'
       
         }
     # Renomear apenas colunas existentes no DataFrame
    colunas_existentes = {col: colunas_para_renomear[col] for col in colunas_para_renomear if col in egresso.columns}
    egresso.rename(columns=colunas_existentes, inplace=True)
    return egresso
           
#####################################################################333
@avaliacaoegresso_route.route('/gerar_graficos_completos_egressos')
def gerar_graficos_completos_egressos():
    graficos = []
    recomendacoes_por_programa = {}
    # Receber o nome do arquivo da URL
    filename = request.args.get('filename')
    
    if not filename:
        flash('Nenhum arquivo selecionado para gerar gráficos', 'danger')
        return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        flash('Arquivo não encontrado', 'danger')
        return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))

    try:
        # Tentar ler o arquivo CSV e remover o BOM
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            egresso = pd.read_csv(f, delimiter=';')      

        # Imprimir as colunas originais para verificar o problema
            print("Colunas originais:", egresso.columns.tolist())
        

        # Renomear as colunas como no seu Colab
        egresso.rename({
                    'Como voce identifica seu genero?':'genero', 
                    'Qual o ultimo nivel de formacao que voce obteve na UNIFEI?':'ultima_formacao',
                    'Qual o seu ano de conclusao?':'ano_conclusao',
                    'A qual programa esteve vinculado?':'programa',
                    'Em uma escala de 0 a 10, o quanto voce recomendaria o Programa em que realizou sua pos-graduacao na UNIFEI?':'recomendacao_programa',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Qualidade das aulas]':'qualidade_aulas',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Material didatico utilizado nas disciplinas]':'material_didatico',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Acervo disponivel para consulta]':'acervo_consulta',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Infraestrutura geral]':'infraestrututra_geral',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Laboratorios de pesquisa/Salas de estudo]':'laboratorios_sala',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Insumos para pesquisa]':'insumos_pesquisa',
                    'Como voce avalia o relacionamento entre voce e: [os colegas]':'relacionamento_colegas',
                    'Como voce avalia o relacionamento entre voce e: [a comissao orientadora]':'relacionamento_orientador',
                    'Como voce avalia o relacionamento entre voce e: [a comissao coordenadora]':'relacionamento_coordenador',
                    'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'relacionamento_secretaria',
                    'Como voce avalia a gestao do programa? [Processo de gestao/Administrativo do Programa]':'administrativo',
                    'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizacao_programa',
                    'Em relacao a sua TESE/DISSERTAcaO, voce ficou:':'satisfacao_dissertacao_tese',
                    'Em relacao a sua PRODUcaO CIENTiFICA, voce ficou satisfeito:':'satisfacao_producao',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia social?':'relevancia_social',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia economico?':'relevancia_economico',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia ambiental?':'relevancia_ambiental',
                    'Voce acredita que a sua pesquisa promoveu o avanco cientifico?':'pesquisa_cientifico',
                    'Voce acredita que sua pesquisa esteve alinhada com missao, visao e objetivos de seu Programa?':'missao-visao-objetivos',
                    'Voce recebeu bolsa de pos-graduacao?':'bolsa',
                    'Para a realizacao de seu projeto de pesquisa houve algum tipo de captacao de recurso externo (exceto bolsa)?':'recurso_externo',
                    'O programa de pos-graduacao em que atuou tem como objetivo a producao de inovacao tecnologica?':'inovacao_programa',
                    'Voce acredita que a linha de pesquisa em que atuou se destaca pela producao de inovacao tecnologica?':'linha_pesquisa_inovacao',
                    'Voce depositou alguma patente proveniente de sua pesquisa?':'patente',
                    'O programa de pos-graduacao em que atuou tem como objetivo a producao de tecnologias de APLICAcaO SOCIAL?':'programa_aplicacao_social',
                    'Alguma tecnologia de aplicacao social foi criada como resultado de sua pesquisa?':'pesquisa_tecnologia_social',
                    'Voce ja apresentou algum resultado de sua pesquisa em algum evento voltado para a sociedade, ou pretende apresentar?':'evento_sociedade',
                    'Voce ja apresentou algum resultado de sua pesquisa em algum evento CIENTiFICO, ou pretende apresentar?':'evento_cientifico',
                    'Sua pesquisa gerou solucões para os problemas que a sociedade enfrenta ou vira a enfrentar?':'solucao_pesquica_sociedade',
                    'Qual foi o principal impacto social promovido por seu projeto de pesquisa? (Marque todas aplicaveis)':'impacto_projeto',
                    'Seu projeto de pesquisa possuiu parcerias com instituicoes internacionais de pesquisa ou ensino?':'parceria_internacional',
                    'Quando aluno da UNIFEI, teve a oportunidade de fazer parte da sua pos-graduacao em outra instituicao (Nacional ou Internacional)?':'aluno_outra_instituicao',
                    'Se sim, onde? Qual nivel? Qual foi o periodo de duracao (mes/ano)?':'lugar_nivel',
                    'Em sua trajetoria profissional, teve a oportunidade de atuar fora do Brasil?':'profissional_exterior',
                    'Caso se sinta a vontade, pedimos que compartilhe como fez para pleitear a oportunidade fora do Brasil.':'pleitear',
                    'Qual sua colocacao profissional atualmente?':'colocacao_profissional_hoje',
                    'Seu emprego esta relacionado a sua area de formacao na pos-graduacao da UNIFEI?':'emprego_formacao',
                    'Qual a sua faixa salarial e/ou de rendimentos em moeda do seu pais atual? Destacamos que esta informacao tem sido requisitada ao Programas de Pos-Graduacao pela Capes e que nao sera divulgada expondo a realidade individual do egresso (em caso de moeda estrangeira, necessario realizar conversao para moeda brasileira).':'faixa_salarial',
                    'Voce teve dificuldade para conseguir o primeiro emprego?':'dificuldade_primeiro_emprego',
                    'Caso tenha tido/tenha dificuldade para conseguir o primeiro emprego, o que poderia ser melhorado no programa, visando maior insercao no mercado de trabalho?':'melhoria_emprego',
                    'Teve bolsa de iniciacao cientifica na graduacao?':'bolsa_cientifica_graduacao',
                    'Voce teve recursos e estrutura fisica suficiente para a conducao dos seus experimentos?':'recursos_experimentos',
                    'Gostariamos de saber sua satisfacao pessoal e profissional com relacao a sua formacao na UNIFEI. Fique a vontade em descreve-las.':'satisfacao_formacao',
                    'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?':'cometario_prppg'
         }, axis=1, inplace=True)
           
           # Verificar se a coluna foi renomeada corretamente
        print("Colunas após renomeação:", egresso.columns.tolist())

        # Definir as colunas necessárias
        required_columns = ['qualidade_aulas', 'material_didatico', 'infraestrututra_geral']

        # Limpar e converter colunas para numérico
        egresso = limpar_e_converter_para_numeric(egresso, required_columns)
        print(egresso.columns)

        # Garantir que as colunas são numéricas
        for col in required_columns:
            egresso[col] = pd.to_numeric(egresso[col], errors='coerce')

        # Criar novas colunas calculadas (médias)
        egresso['Media_Qualidade_Aulas'] = egresso[required_columns].mean(axis=1)

        # Gráfico de barras - Avaliação da qualidade das aulas
        fig1, ax1 = plt.subplots()
        ax1.bar(egresso['qualidade_aulas'].value_counts().index, 
                egresso['qualidade_aulas'].value_counts())
        ax1.set_title('Distribuição da Qualidade das Aulas')
        ax1.set_xlabel('qualidade_aulas')
        ax1.set_ylabel('Número de Alunos')
        img1 = io.BytesIO()
        plt.savefig(img1, format='png')
        img1.seek(0)
        graficos.append(base64.b64encode(img1.getvalue()).decode('utf-8'))
        plt.close(fig1)

        # Histograma de Proficiência em Inglês
        fig2, ax2 = plt.subplots()
        ax2.hist(egresso['inovacao_programa'], bins=10, color='skyblue')
        ax2.set_title('Programa produção de inovação tecnológica')
        ax2.set_xlabel('inovacao_programa')
        ax2.set_ylabel('Número de Alunos')
        img2 = io.BytesIO()
        plt.savefig(img2, format='png')
        img2.seek(0)
        graficos.append(base64.b64encode(img2.getvalue()).decode('utf-8'))
        plt.close(fig2)

        # Boxplot de Formação vs Qualidade das Aulas
        fig3, ax3 = plt.subplots()
        sns.boxplot(x='ano_conclusao', y='ultima_formacao', data=egresso, ax=ax3)
        ax3.set_title('Nível de Formação vs Qualidade das Aulas')
        ax3.set_xlabel('Ano Conclusão')
        ax3.set_ylabel('Nível de Formação')
        plt.xticks(rotation=45)
        img3 = io.BytesIO()
        plt.savefig(img3, format='png')
        img3.seek(0)
        graficos.append(base64.b64encode(img3.getvalue()).decode('utf-8'))
        plt.close(fig3)

        # Gráfico de linha - Tendência da Qualidade das Aulas ao longo dos anos
        fig4, ax4 = plt.subplots()
        sns.lineplot(x='ultima_formacao', y='qualidade_aulas', data=egresso, ax=ax4)
        ax4.set_title('Tendência da Qualidade das Aulas ao Longo dos Anos')
        ax4.set_xlabel('Ano de ultima_formacao')
        ax4.set_ylabel('Qualidade das Aulas')
        img4 = io.BytesIO()
        plt.savefig(img4, format='png')
        img4.seek(0)
        graficos.append(base64.b64encode(img4.getvalue()).decode('utf-8'))
        plt.close(fig4)

        # Mapa de calor - Correlação entre variáveis
        fig5, ax5 = plt.subplots(figsize=(10, 7))
        sns.heatmap(egresso[['qualidade_aulas', 'inovacao_programa']].corr(), 
                    annot=True, cmap='coolwarm', linewidths=0.4, ax=ax5)
        ax5.set_title('Mapa de Calor das Correlações')
        img5 = io.BytesIO()
        plt.savefig(img5, format='png')
        img5.seek(0)
        graficos.append(base64.b64encode(img5.getvalue()).decode('utf-8'))
        plt.close(fig5)


       # Gráfico 5: Gráfico de Sentimentos
        if 'satisfacao_formacao' in egresso:
            fig5, ax5 = plt.subplots(figsize=(8, 6))
            egresso['Sentimento_Programa'] = egresso['satisfacao_formacao'].fillna('').apply(analisar_sentimento)
            sentimentos = egresso['Sentimento_Programa'].apply(lambda x: x['compound']).dropna()
            sns.histplot(sentimentos, kde=True, ax=ax5)
            ax5.set_title('Distribuição de Sentimentos sobre o Programa')
            ax5.set_xlabel('Score de Sentimento')
            ax5.set_ylabel('Frequência')
            img5 = io.BytesIO()
            plt.savefig(img5, format='png')
            img5.seek(0)
            graficos.append(base64.b64encode(img5.getvalue()).decode('utf-8'))
            plt.close(fig5)

        # Gráfico de violino para a Média de Qualidade das Aulas
        fig6, ax6 = plt.subplots(figsize=(10, 6))  # Definir o tamanho do gráfico
        sns.violinplot(y=egresso['Media_Qualidade_Aulas'], ax=ax6, color='lightgreen')

        # Título e rótulos
        ax6.set_title('Distribuição da Média de Qualidade das Aulas', fontsize=16)
        ax6.set_ylabel('Média de Avaliação', fontsize=14)

        # Adicionar anotação com a média
        media_valor = egresso['Media_Qualidade_Aulas'].mean()
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
        return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))

    # Retornar o template com os gráficos gerados
    return render_template(
        'dashboard_egresso.html',
        graficos=graficos,
        recomendacoes_por_programa=recomendacoes_por_programa
    )


#####################################################################



# Inicializar o analisador de sentimentos
nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Função para processar o sentimento
def analisar_sentimento(texto):
    return sid.polarity_scores(texto)


@avaliacaoegresso_route.route('/analisar_sentimentos_egresso', methods=['GET'])
def analisar_sentimentos_egresso():
    try:
        # Caminho para o arquivo
        file_path = 'uploads/egresso.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))

        # Carregar o arquivo CSV
        egresso = pd.read_csv(file_path, delimiter=';')
        egresso = renomear_colunas(egresso)
        egresso = limpar_dados(egresso)

        # Verificar se as colunas de comentários estão presentes
        if 'satisfacao_formacao' not in egresso.columns or 'cometario_prppg' not in egresso.columns:
            flash('Colunas de comentários não encontradas no arquivo.', 'danger')
            return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))

        # Renomear colunas para aplicar a análise de sentimento
        egresso.rename({
            'satisfacao_formacao': 'Sentimento_Programa',
            'cometario_prppg': 'Sentimento_Pro_Reitoria'
        }, axis=1, inplace=True)

        # Garantir que os valores nas colunas de comentários são strings e substituir NaN por string vazia
        egresso['Sentimento_Programa'] = egresso['Sentimento_Programa'].fillna('').astype(str)
        egresso['Sentimento_Pro_Reitoria'] = egresso['Sentimento_Pro_Reitoria'].fillna('').astype(str)

        # Selecionar as colunas de comentários para análise
        df_comentarios = egresso[['Sentimento_Programa', 'Sentimento_Pro_Reitoria']].copy()

        # Aplicar a função de sentimento para cada comentário e lidar com valores vazios
        df_comentarios['Sent_Programa_Score'] = df_comentarios['Sentimento_Programa'].apply(lambda x: analisar_sentimento(str(x)) if x else {'compound': 0})
        df_comentarios['Sent_Pro_Reitoria_Score'] = df_comentarios['Sentimento_Pro_Reitoria'].apply(lambda x: analisar_sentimento(str(x)) if x else {'compound': 0})

        # Expandir os resultados do VADER em colunas separadas
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_Programa_Score']).add_prefix('Programa_'))
        df_comentarios = df_comentarios.join(pd.json_normalize(df_comentarios['Sent_Pro_Reitoria_Score']).add_prefix('Pro_Reitoria_'))

        # Calcular médias dos sentimentos
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()
        media_sentimentos_prppg = df_comentarios['Pro_Reitoria_compound'].mean()

        # Contagem de tipos de sentimento para o gráfico
        total_negativos_programa = len(df_comentarios[df_comentarios['Programa_compound'] < 0])
        total_positivos_programa = len(df_comentarios[df_comentarios['Programa_compound'] > 0])
        total_neutros_programa = len(df_comentarios[df_comentarios['Programa_compound'] == 0])

        # Criar gráfico de barras para visualização dos sentimentos
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.bar(['Negativos', 'Positivos', 'Neutros'], [total_negativos_programa, total_positivos_programa, total_neutros_programa], color=['red', 'green', 'gray'])
        ax.set_title('Distribuição de Sentimentos sobre o Programa de Pós-Graduação')
        ax.set_xlabel('Tipo de Sentimento')
        ax.set_ylabel('Número de Comentários')

        # Salvar o gráfico no buffer
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        grafico_sentimentos = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close(fig)

        return render_template('sentimentoegresso.html', 
                               grafico_sentimentos=grafico_sentimentos,
                               media_programa=media_sentimentos_programa, 
                               media_prppg=media_sentimentos_prppg)

    except Exception as e:
        flash(f"Erro ao processar os sentimentos: {e}", 'danger')
        return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))


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

@avaliacaoegresso_route.route('/visualizar_resultados', methods=['GET'])
def visualizar_resultados():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/egresso.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))

        egresso = pd.read_csv(file_path, delimiter=';')

        # Verificar se os dados têm distribuição suficiente para treinamento
        print(egresso .describe())  # Verificar estatísticas gerais para cada coluna

        # Avaliar os sentimentos do Programa de Pós-Graduação
        media_sentimentos_programa = df_comentarios['Programa_compound'].mean()

        # Gráfico de barras de sentimentos por ano de ingresso
        # Ajustar o gráfico com rotação dos rótulos no eixo X
        # Aumentar o tamanho da imagem com figsize
      # Aumentar o tamanho da imagem com figsize
        fig, ax = plt.subplots(figsize=(14, 8))  # Ajuste os valores para o tamanho desejado
        egresso ['Media_Qualidade_Aulas'].plot(kind='bar', ax=ax)
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
        return render_template('resultadoegresso.html', 
                               grafico_sentimentos_egresso=grafico_sentimentos_egresso,
                               mse_otimizado=mse_otimizado,
                               media_programa=media_sentimentos_programa)

    except Exception as e:
        flash(f"Erro ao processar os resultados: {e}", 'danger')
        return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))


################################################################################################
@avaliacaoegresso_route.route('/analisar_dados_ia', methods=['GET'])
def analisar_dados_ia():
    try:
        # Simulação de leitura do arquivo já carregado
        file_path = 'uploads/egresso.csv'
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))

        # Carregar os dados do CSV
        egresso = pd.read_csv(file_path, delimiter=';')

        # Renomear as colunas como no seu Colab
        egresso.rename({
     'Como voce identifica seu genero?':'genero', 
                    'Qual o ultimo nivel de formacao que voce obteve na UNIFEI?':'ultima_formacao',
                    'Qual o seu ano de conclusao?':'ano_conclusao',
                    'A qual programa esteve vinculado?':'programa',
                    'Em uma escala de 0 a 10, o quanto voce recomendaria o Programa em que realizou sua pos-graduacao na UNIFEI?':'recomendacao_programa',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Qualidade das aulas]':'qualidade_aulas',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Material didatico utilizado nas disciplinas]':'material_didatico',
                    'Como voce avalia a qualidade das aulas e do material utilizado no Programa? [Acervo disponivel para consulta]':'acervo_consulta',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Infraestrutura geral]':'infraestrututra_geral',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Laboratorios de pesquisa/Salas de estudo]':'laboratorios_sala',
                    'Como voce avalia a infraestrutura do programa durante seu periodo na UNIFEI? [Insumos para pesquisa]':'insumos_pesquisa',
                    'Como voce avalia o relacionamento entre voce e: [os colegas]':'relacionamento_colegas',
                    'Como voce avalia o relacionamento entre voce e: [a comissao orientadora]':'relacionamento_orientador',
                    'Como voce avalia o relacionamento entre voce e: [a comissao coordenadora]':'relacionamento_coordenador',
                    'Como voce avalia o relacionamento entre voce e: [a secretaria do programa]':'relacionamento_secretaria',
                    'Como voce avalia a gestao do programa? [Processo de gestao/Administrativo do Programa]':'administrativo',
                    'Como voce avalia a gestao do programa? [Organizacao do Programa]':'organizacao_programa',
                    'Em relacao a sua TESE/DISSERTAcaO, voce ficou:':'satisfacao_dissertacao_tese',
                    'Em relacao a sua PRODUcaO CIENTiFICA, voce ficou satisfeito:':'satisfacao_producao',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia social?':'relevancia_social',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia economico?':'relevancia_economico',
                    'Voce acredita que a sua pesquisa teve relevancia e pertinencia ambiental?':'relevancia_ambiental',
                    'Voce acredita que a sua pesquisa promoveu o avanco cientifico?':'pesquisa_cientifico',
                    'Voce acredita que sua pesquisa esteve alinhada com missao, visao e objetivos de seu Programa?':'missao-visao-objetivos',
                    'Voce recebeu bolsa de pos-graduacao?':'bolsa',
                    'Para a realizacao de seu projeto de pesquisa houve algum tipo de captacao de recurso externo (exceto bolsa)?':'recurso_externo',
                    'O programa de pos-graduacao em que atuou tem como objetivo a producao de inovacao tecnologica?':'inovacao_programa',
                    'Voce acredita que a linha de pesquisa em que atuou se destaca pela producao de inovacao tecnologica?':'linha_pesquisa_inovacao',
                    'Voce depositou alguma patente proveniente de sua pesquisa?':'patente',
                    'O programa de pos-graduacao em que atuou tem como objetivo a producao de tecnologias de APLICAcaO SOCIAL?':'programa_aplicacao_social',
                    'Alguma tecnologia de aplicacao social foi criada como resultado de sua pesquisa?':'pesquisa_tecnologia_social',
                    'Voce ja apresentou algum resultado de sua pesquisa em algum evento voltado para a sociedade, ou pretende apresentar?':'evento_sociedade',
                    'Voce ja apresentou algum resultado de sua pesquisa em algum evento CIENTiFICO, ou pretende apresentar?':'evento_cientifico',
                    'Sua pesquisa gerou solucões para os problemas que a sociedade enfrenta ou vira a enfrentar?':'solucao_pesquica_sociedade',
                    'Qual foi o principal impacto social promovido por seu projeto de pesquisa? (Marque todas aplicaveis)':'impacto_projeto',
                    'Seu projeto de pesquisa possuiu parcerias com instituicoes internacionais de pesquisa ou ensino?':'parceria_internacional',
                    'Quando aluno da UNIFEI, teve a oportunidade de fazer parte da sua pos-graduacao em outra instituicao (Nacional ou Internacional)?':'aluno_outra_instituicao',
                    'Se sim, onde? Qual nivel? Qual foi o periodo de duracao (mes/ano)?':'lugar_nivel',
                    'Em sua trajetoria profissional, teve a oportunidade de atuar fora do Brasil?':'profissional_exterior',
                    'Caso se sinta a vontade, pedimos que compartilhe como fez para pleitear a oportunidade fora do Brasil.':'pleitear',
                    'Qual sua colocacao profissional atualmente?':'colocacao_profissional_hoje',
                    'Seu emprego esta relacionado a sua area de formacao na pos-graduacao da UNIFEI?':'emprego_formacao',
                    'Qual a sua faixa salarial e/ou de rendimentos em moeda do seu pais atual? Destacamos que esta informacao tem sido requisitada ao Programas de Pos-Graduacao pela Capes e que nao sera divulgada expondo a realidade individual do egresso (em caso de moeda estrangeira, necessario realizar conversao para moeda brasileira).':'faixa_salarial',
                    'Voce teve dificuldade para conseguir o primeiro emprego?':'dificuldade_primeiro_emprego',
                    'Caso tenha tido/tenha dificuldade para conseguir o primeiro emprego, o que poderia ser melhorado no programa, visando maior insercao no mercado de trabalho?':'melhoria_emprego',
                    'Teve bolsa de iniciacao cientifica na graduacao?':'bolsa_cientifica_graduacao',
                    'Voce teve recursos e estrutura fisica suficiente para a conducao dos seus experimentos?':'recursos_experimentos',
                    'Gostariamos de saber sua satisfacao pessoal e profissional com relacao a sua formacao na UNIFEI. Fique a vontade em descreve-las.':'satisfacao_formacao',
                    'Gostaria de adicionar algum comentario referente a Pro-Reitoria de Pesquisa e Pos-Graduacao?':'cometario_prppg'
         }, axis=1, inplace=True)
           

        # 1. Garantir que todas as colunas são numéricas
        colunas_qualidade = ['qualidade_aulas','material_didatico', 'acervo_consulta']
        colunas_projetos = ['evento_cientifico', 'evento_sociedade', 'relevancia_social',
                               'relevancia_economico', 'relevancia_ambiental', 'relevancia_social']
        colunas_infraestrutura = ['infraestrututra_geral','laboratorios_sala','insumos_pesquisa']
        colunas_relacionamentos = ['relacionamento_colegas','relacionamento_orientador',
                                   'relacionamento_secretaria','relacionamento_coordenador']
        colunas_internacionalizacao = ['parceria_internacional','pleitear',
                                       'profissional_exterior']

       # Converter as colunas para numéricas
        def converter_para_numerico(df, colunas):
            for coluna in colunas:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
            return df

        egresso = converter_para_numerico(egresso, colunas_qualidade + colunas_projetos + colunas_infraestrutura + colunas_relacionamentos + colunas_internacionalizacao)

        # Agrupar os dados por programa
        agrupado_por_programa = egresso.groupby('programa')

        # Variáveis para armazenar as recomendações por programa
        recomendacoes_por_programa = {}

        for programa, dados_programa in agrupado_por_programa:
            if len(dados_programa) < 2:
                continue  # Pular grupos com poucos dados para evitar erro no treino/teste

            # 2. Criar as médias por grupo de avaliação
            media_qualidade = dados_programa['qualidade_aulas'].mean()
            media_infraestrutura = dados_programa['infraestrutura_geral'].mean()

            # Verificar sentimentos nos comentários (se disponíveis)
            df_comentarios = dados_programa[['satisfacao_formacao']].dropna()
            media_sentimentos_programa = None  # valor padrão se não houver comentários

            if not df_comentarios.empty:
                df_comentarios['Sentimento_Programa_Score'] = df_comentarios['satisfacao_formacao'].apply(lambda x: analisar_sentimento(str(x))['compound'])
                media_sentimentos_programa = df_comentarios['Sentimento_Programa_Score'].mean()

            # 3. RandomForest e XGBoost para prever a qualidade das aulas
            X = dados_programa.drop(['qualidade_aulas'], axis=1)  # Variáveis independentes
            y = dados_programa['qualidade_aulas']  # Variável dependente

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
        return render_template('recomendacaoegresso.html', recomendacoes_por_programa=recomendacoes_por_programa)

    except Exception as e:
        flash(f"Erro ao processar os dados: {e}", 'danger')
        return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))
    

# Função para substituir "Sim"/"Não" e valores problemáticos
def limpar_dados(df):
    df.replace({
        "Sem condições de avaliar": np.nan,
        "Sem condiÃ§Ãµes de avaliar": np.nan,
        "Sem condicoes de avaliar": np.nan,
        "Não se aplica": np.nan
    }, inplace=True)
    return df
####################################################################################################333
@avaliacaoegresso_route.route('/exibir_recomendacoes_egresso', methods=['GET'])
def exibir_recomendacoes_egresso():
    try:
        file_path = os.path.join(UPLOAD_FOLDER, 'egresso.csv')
        if not os.path.exists(file_path):
            flash('Arquivo "egresso.csv" não encontrado na pasta uploads.', 'danger')
            return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))
        
        # Carregar, limpar e renomear colunas do CSV
        egresso = pd.read_csv(file_path, delimiter=';', encoding='latin1')
        egresso = renomear_colunas(egresso)
        egresso = limpar_dados(egresso)
            
        # Garantir que as colunas relevantes são numéricas
        colunas_qualidade = ['qualidade_aulas', 'material_didatico', 'acervo_consulta']
        colunas_projetos = ['evento_cientifico', 'evento_sociedade', 'relevancia_social', 
                            'relevancia_economico', 'relevancia_ambiental', 'relevancia_social']
        colunas_infraestrutura = ['infraestrututra_geral', 'laboratorios_sala', 'insumos_pesquisa']
        colunas_relacionamentos = ['relacionamento_colegas', 'relacionamento_orientador', 
                                   'relacionamento_secretaria', 'relacionamento_coordenador']
        colunas_internacionalizacao = ['parceria_internacional', 'profissional_exterior']
        
        # Converter colunas para numérico e tratar valores ausentes
        def converter_para_numerico(df, colunas):
            for coluna in colunas:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
            return df

        egresso = converter_para_numerico(egresso, colunas_qualidade + colunas_projetos +
                                          colunas_infraestrutura + colunas_relacionamentos +
                                          colunas_internacionalizacao)

        # Calcular médias por grupo
        egresso['Media_Qualidade'] = egresso[colunas_qualidade].mean(axis=1)
        egresso['Media_Projetos'] = egresso[colunas_projetos].mean(axis=1)
        egresso['Media_Infraestrutura'] = egresso[colunas_infraestrutura].mean(axis=1)
        egresso['Media_Relacionamentos'] = egresso[colunas_relacionamentos].mean(axis=1)
        egresso['Media_Internacionalizacao'] = egresso[colunas_internacionalizacao].mean(axis=1)
        
        # Agrupar por programa e calcular médias
        df_por_programa = egresso.groupby('programa').agg({
            'Media_Qualidade': 'mean',
            'Media_Projetos': 'mean',
            'Media_Infraestrutura': 'mean',
            'Media_Relacionamentos': 'mean',
            'Media_Internacionalizacao': 'mean'
        }).reset_index()

        # Gerar recomendações para cada programa
        recomendacoes_por_programa = gerar_recomendacoes_programa(df_por_programa)

        # Passar as recomendações para o template com o nome correto
        return render_template('recomendacaoegresso.html', recomendacoes_por_programa=recomendacoes_por_programa)
    
    except Exception as e:
        flash(f"Erro ao gerar recomendações: {e}", 'danger')
        return redirect(url_for('avaliacaoegresso.importar_planilhaegresso'))

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

        if row['Media_Projetos'] < 3:
            recomendacoes.append({
                "objetivo": "Reavaliar e aprimorar os projetos de pesquisa",
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

            # Adiciona as recomendações para o programa, ou "Sem recomendações específicas" se vazio
        recomendacoes_por_programa[programa] = recomendacoes if recomendacoes else ["Sem recomendações específicas."]

    return recomendacoes_por_programa
