import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
import unicodedata

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
            return redirect(url_for('avaliacaodiscente.gerar_graficos', filename=filename))

    return render_template('importar_planilhadiscente.html')

def normalize_column_names(df):
    df.columns = [unicodedata.normalize('NFKD', col).encode('ascii', 'ignore').decode('utf-8').strip().lower() for col in df.columns]
    return df

@avaliacaodiscente_route.route('/gerar_graficos')
def gerar_graficos():
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
            data_corrected = pd.read_csv(f, delimiter=';')
        print("Colunas do CSV:", data_corrected.columns)  # Verificar as colunas carregadas
    except Exception as e:
        flash(f"Erro ao processar o arquivo: {e}", "danger")
        return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

    # Substituir valores ausentes por 0
    data_corrected.fillna(0, inplace=True)

    # Substituir 'Sim' por 1 e 'Não' por 0
    data_corrected = data_corrected.infer_objects(copy=False)  # Resolve o aviso de FutureWarning
    data_corrected.replace({'Sim': 1, 'Não': 0, 'NÃ£o': 0, 'Nao': 0}, inplace=True)

    # Normalizar os nomes das colunas
    data_corrected = normalize_column_names(data_corrected)

# Agora, normalize também a lista de colunas esperadas
    required_columns = ['1. qual o seu nivel de formacao?', '2. qual o seu ano de ingresso?',
       '3. a qual programa esta vinculado?',
       'como voce avalia a qualidade das aulas e do material utilizado? [qualidade das aulas]',
       'como voce avalia a qualidade das aulas e do material utilizado? [material didatico utilizado nas disciplinas]',
       'como voce avalia a qualidade das aulas e do material utilizado? [acervo disponivel para consulta]',
       'como voce avalia a infraestrutura do programa? [infraestrutura geral]',
       'como voce avalia a infraestrutura do programa? [laboratorios de pesquisa/salas de estudo]',
       'como voce avalia a infraestrutura do programa? [insumos para pesquisa]',
       'como voce avalia o relacionamento entre voce e: [os colegas]',
       'como voce avalia o relacionamento entre voce e: [a comissao orientadora]',
       'como voce avalia o relacionamento entre voce e: [a comissao coordenadora]',
       'como voce avalia o relacionamento entre voce e: [a secretaria do programa]',
       'como voce avalia a gestao do programa? [processo de gestao/administrativo do programa]',
       'como voce avalia a gestao do programa? [organizacao do programa]',
       'como voce avalia o seu conhecimento acerca: [do seu papel enquanto aluno]',
       'como voce avalia o seu conhecimento acerca: [do regimento interno do programa]',
       'como voce avalia o seu conhecimento acerca: [do regimento geral da pos-graduacao]',
       'como voce avalia o seu conhecimento acerca: [das normas da capes]',
       'como voce avalia o seu conhecimento acerca: [do processo de avaliacao da capes]',
       'em relacao ao seu projeto de pesquisa, voce esta:',
       'em relacao a sua producao cientifica, voce esta:',
       'voce acredita que sua pesquisa possui relevancia e pertinencia social?',
       'voce acredita que sua pesquisa possui relevancia e pertinencia economica?',
       'voce acredita que sua pesquisa possui relevancia e pertinencia ambiental?',
       'voce acredita que sua pesquisa promove avanco cientifico?',
       'o seu programa possui visao, missao e objetivos claros?',
       'voce acredita que sua pesquisa esta alinhada com o objetivo e missao de seu programa?',
       'quais sao os principais atores que podem ser impactados por sua pesquisa e producao cientifica dela decorrente? (marque todas que se aplicam).',
       'voce recebe bolsa de pos-graduacao?',
       'para a realizacao de seu projeto de pesquisa houve algum tipo de captacao de recurso externo (exceto bolsa)?',
       'na sua opiniao, o que e preciso para que o seu programa tenha producao de conhecimento cientifico e tecnologico qualificado, reconhecido pela comunidade cientifica internacional da area em que atua?',
       'producao de inovacao tecnologica e uma prioridade em seu programa de pos-graduacao?',
       'voce acredita que sua linha de pesquisa se destaca pela producao de inovacao tecnologica?',
       'voce ja depositou alguma patente proveniente de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?',
       'producao de tecnologias de aplicacao social e uma prioridade em seu programa de pos-graduacao?',
       'alguma tecnologia de aplicacao social ja foi criada como resultado de sua pesquisa, ou possui isso como um dos objetivos de seu projeto de pesquisa?',      
       'voce ja apresentou algum resultado de sua pesquisa em algum evento voltado para a comunidade, ou pretende apresentar?',
       'voce ja apresentou algum resultado de sua pesquisa em algum evento cientifico, ou pretende apresentar?',
       'sua pesquisa podera gerar solucoes para os problemas que a sociedade enfrenta ou vira a enfrentar?',
       'qual o principal impacto social a ser promovido por seu projeto de pesquisa? (marque todas aplicaveis)',
       'qual o nivel de internacionalizacao do seu programa?',
       'no momento, ha interesse por parte do seu programa de pos-graduacao em iniciar um processo de internacionalizacao?',
       'voce se sente preparado para a internacionalizacao do seu programa de pos-graduacao?',
       'voce entende que o seu programa de pos-graduacao esta preparado para a internacionalizacao?',
       'seu projeto de pesquisa possui parcerias com instituicoes internacionais de pesquisa ou ensino?',
       'qual o seu nivel de proficiencia em lingua inglesa?',
       'gostaria de adicionar algum comentario referente seu programa de pos-graduacao?',
       'gostaria de adicionar algum comentario referente a pro-reitoria de pesquisa e pos-graduacao?']
    
   # Verificar se as colunas estão presentes
    available_columns = [col for col in required_columns if col in data_corrected.columns]
    print("Colunas disponíveis:", available_columns)  # Verificar quais colunas estão disponíveis

    if not available_columns:
        flash(f"O arquivo CSV não contém nenhuma das colunas esperadas.", 'danger')
        return redirect(url_for('avaliacaodiscente.importar_planilhadiscente'))

    # Geração do gráfico de exemplo - Qualidade das aulas
    if 'como voce avalia a qualidade das aulas e do material utilizado? [qualidade das aulas]' in available_columns:
        fig1, ax1 = plt.subplots()
        qualidade_aulas = data_corrected['como voce avalia a qualidade das aulas e do material utilizado? [qualidade das aulas]']
        qualidade_aulas = qualidade_aulas[qualidade_aulas != 'Sem condições de avaliar'].astype(float)  # Certificar que são valores numéricos
        ax1.hist(qualidade_aulas, bins=10)
        ax1.set_title('Distribuição da Qualidade das Aulas')
        ax1.set_xlabel('Nota')
        ax1.set_ylabel('Número de Alunos')

        img1 = io.BytesIO()
        plt.savefig(img1, format='png')
        img1.seek(0)
        graficos.append(base64.b64encode(img1.getvalue()).decode('utf-8'))
        plt.close(fig1)

    # Adicionando gráfico de teste para verificar funcionalidade
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])  # Testando com dados simples
    ax.set_title('Teste de Geração de Gráfico')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graficos.append(base64.b64encode(img.getvalue()).decode('utf-8'))
    plt.close(fig)

    # Exibir gráficos na página HTML
    return render_template('dashboard_discente.html', graficos=graficos)