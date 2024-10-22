import os
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app,session,send_file
from flask_login import login_required
import pandas as pd
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Planejamento Estratégico', 0, 1, 'C')

    def tabela_objetivos(self, objetivos):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Objetivos', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        for obj in objetivos:
            self.cell(0, 10, obj, 1, 1, 'L')

    def tabela_metas(self, metas):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Metas', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        for meta in metas:
            self.cell(90, 10, meta['nome'], 1)
            self.cell(30, 10, meta['status'], 1)
            self.cell(40, 10, meta['tempo_restante'], 1, 1)

    def tabela_indicadores(self, indicadores):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Indicadores', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        for indicador in indicadores:
            self.cell(60, 10, indicador['nome'], 1)
            self.cell(30, 10, str(indicador['peso']), 1)
            self.cell(40, 10, indicador['frequencia'], 1, 1)

    def tabela_acoes(self, acoes):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Ações', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        for acao in acoes:
            self.cell(90, 10, acao['nome'], 1)
            self.cell(30, 10, str(acao['execucao']), 1)
            self.cell(30, 10, acao['status'], 1)
            self.cell(40, 10, acao['tempo_restante'], 1, 1)



# Configurações do blueprint
autoavaliacaoegresso_route = Blueprint('autoavaliacaoegresso', __name__)



# Definir as pastas de upload e gráficos
UPLOAD_FOLDER = 'static/uploads'
GRAPH_FOLDER = 'static/graficos'

# Certificar-se de que os diretórios de upload e gráficos existem
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(GRAPH_FOLDER):
    os.makedirs(GRAPH_FOLDER)

# Função para verificar se o arquivo tem a extensão permitida
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@autoavaliacaoegresso_route.route('/importar_planilha_egresso', methods=['GET', 'POST'])
def importar_planilha_egresso():
    try:
        if request.method == 'POST':
            # Verifica se o arquivo foi enviado
            if 'file' not in request.files:
                flash('Nenhum arquivo foi enviado.', 'danger')
                print('Nenhum arquivo foi enviado.')
                return redirect(request.url)

            file = request.files['file']

            if file.filename == '':
                flash('Nenhum arquivo selecionado.', 'danger')
                print('Nenhum arquivo selecionado.')
                return redirect(request.url)

            # Verifica se o arquivo tem a extensão permitida
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                # Salva o arquivo no diretório correto
                file.save(filepath)
                flash(f"Arquivo {filename} salvo com sucesso no diretório {UPLOAD_FOLDER}!", 'success')
                print(f"Arquivo {filename} salvo com sucesso no diretório {UPLOAD_FOLDER}")

                # Carrega a planilha em um DataFrame Pandas
                df = pd.read_excel(filepath)

                # Padroniza as colunas para minúsculas e remove espaços
                df.columns = df.columns.str.strip().str.lower()

                # Colunas necessárias
                required_columns = [
                    'qual o seu ano de conclusão?', 
                    'em uma escala de 0 a 10, o quanto você recomendaria o programa em que realizou sua pós-graduação na unifei?',
                    'como você avalia a qualidade das aulas e do material utilizado no programa? [qualidade das aulas]',
                    'qual a sua faixa salarial e/ou de rendimentos em moeda',
                    'você acredita que a sua pesquisa promoveu o avanço científico?',
                    'como você avalia a infraestrutura do programa durante seu período na unifei? [insumos para pesquisa]',
                    'como você avalia a gestão do programa? [processo de gestão/administrativo do programa]'
                ]

                # Verifica se as colunas necessárias estão presentes
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    flash(f"Erro: As seguintes colunas estão ausentes na planilha: {', '.join(missing_columns)}", 'danger')
                    return redirect(request.url)

                # Salva os dados relevantes em um arquivo CSV
                dados_relevantes = df[required_columns]
                dados_relevantes.to_csv(os.path.join(UPLOAD_FOLDER, 'dados_relevantes_egresso.csv'), index=False)

                flash('Arquivo importado e processado com sucesso!', 'success')

                # Redireciona para a página de gráficos
                planejamento_id = 1  # Defina o valor correto para o ID do planejamento
                return redirect(url_for('autoavaliacaoegresso.mostrar_dashboard_egresso', planejamento_id=planejamento_id))

        # Se for um GET, exibe a página de upload
        return render_template('importar_planilhaegresso.html')

    except Exception as e:
        print(f"Erro ao processar a planilha: {e}")
        flash(f"Ocorreu um erro ao processar o arquivo: {e}", 'danger')
        return redirect(request.url)
 

@autoavaliacaoegresso_route.route('/dashboard_egresso/<int:planejamento_id>')
@login_required
def mostrar_dashboard_egresso(planejamento_id):
    try:
        # Caminho para o arquivo CSV
        csv_path = os.path.join(UPLOAD_FOLDER, 'dados_relevantes_egresso.csv')
        if not os.path.exists(csv_path):
            flash('Arquivo de dados não encontrado. Importe a planilha primeiro.', 'danger')
            return redirect(url_for('autoavaliacaoegresso.importar_planilha_egresso'))

        # Carregar o CSV em um DataFrame Pandas
        df = pd.read_csv(csv_path)

        # Padronizar colunas
        df.columns = df.columns.str.strip().str.lower()

        # Tratamento de valores nulos
        df.fillna(0, inplace=True)

        # Conversão de colunas numéricas (tratando erros)
        df['ano_conclusao'] = pd.to_numeric(df['qual o seu ano de conclusão?'], errors='coerce')
        df['recomendacao'] = pd.to_numeric(df['em uma escala de 0 a 10, o quanto você recomendaria o programa em que realizou sua pós-graduação na unifei?'], errors='coerce')
        df['qualidade_aulas'] = pd.to_numeric(df['como você avalia a qualidade das aulas e do material utilizado no programa? [qualidade das aulas]'], errors='coerce')
        df['faixa_salarial'] = df['qual a sua faixa salarial e/ou de rendimentos em moeda'].fillna('Não informado')
        df['avanco_cientifico'] = df['você acredita que a sua pesquisa promoveu o avanço científico?'].fillna('Não informado')
        df['insumos_pesquisa'] = pd.to_numeric(df['como você avalia a infraestrutura do programa durante seu período na unifei? [insumos para pesquisa]'], errors='coerce')
        df['processo_gestao'] = pd.to_numeric(df['como você avalia a gestão do programa? [processo de gestão/administrativo do programa]'], errors='coerce')

        # Criação dos gráficos e salvamento
        # Gráfico 1: Barras por Ano de Conclusão
        plt.figure(figsize=(9, 6))
        df['ano_conclusao'].value_counts().sort_index().plot(kind='bar', color='skyblue')
        plt.title('Quantidade de Egressos por Ano de Conclusão')
        plt.xlabel('Ano de Conclusão')
        plt.ylabel('Quantidade de Egressos')
        barras_ano_path = os.path.join(GRAPH_FOLDER, 'barras_ano_conclusao.png')
        plt.savefig(barras_ano_path)
        plt.close()

        # Gráfico 2: Pizza de Recomendação
        plt.figure(figsize=(9, 6))
        df['recomendacao'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['lightgreen', 'lightblue'])
        plt.title('Gráfico Pizza de Recomendação')
        pizza_recomendacao_path = os.path.join(GRAPH_FOLDER, 'pizza_recomendacao.png')
        plt.savefig(pizza_recomendacao_path)
        plt.close()

        # Gráfico 3: Dispersão de Qualidade das Aulas vs Faixa Salarial
        plt.figure(figsize=(9, 6))
        plt.scatter(df['qualidade_aulas'], df['faixa_salarial'].apply(lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else 0), color='purple')
        plt.title('Gráfico de Dispersão de Qualidade das Aulas vs Faixa Salarial')
        plt.xlabel('Qualidade das Aulas')
        plt.ylabel('Faixa Salarial')
        scatter_path = os.path.join(GRAPH_FOLDER, 'scatter_qualidade_vs_salario.png')
        plt.savefig(scatter_path)
        plt.close()

        # Gráfico 4: Barras de Avanço Científico
        plt.figure(figsize=(9, 6))
        df['avanco_cientifico'].value_counts().plot(kind='bar', color='orange')
        plt.title('Gráfico Barras de Avanço Científico')
        barras_avanco_path = os.path.join(GRAPH_FOLDER, 'barras_avanco_cientifico.png')
        plt.savefig(barras_avanco_path)
        plt.close()

        # Gráfico 5: Barras de Insumos para Pesquisa
        plt.figure(figsize=(9, 6))
        df['insumos_pesquisa'].value_counts().plot(kind='bar', color='red')
        plt.title('Gráfico Barras de Avaliação dos Insumos para Pesquisa')
        barras_insumos_path = os.path.join(GRAPH_FOLDER, 'barras_insumos_pesquisa.png')
        plt.savefig(barras_insumos_path)
        plt.close()

        # Gráfico 6: Barras de Avaliação do Processo de Gestão
        plt.figure(figsize=(9, 6))
        df['processo_gestao'].value_counts().plot(kind='bar', color='blue')
        plt.title('Gráfico Barras de Avaliação do Processo de Gestão')
        barras_gestao_path = os.path.join(GRAPH_FOLDER, 'barras_gestao.png')
        plt.savefig(barras_gestao_path)
        plt.close()

        # Passar os caminhos dos gráficos para o template
        return render_template('dashboard_egresso.html',
                               barras_ano_path='/static/graficos/barras_ano_conclusao.png',
                               pizza_recomendacao_path='/static/graficos/pizza_recomendacao.png',
                               scatter_path='/static/graficos/scatter_qualidade_vs_salario.png',
                               barras_avanco_path='/static/graficos/barras_avanco_cientifico.png',
                               barras_insumos_path='/static/graficos/barras_insumos_pesquisa.png',
                               barras_gestao_path='/static/graficos/barras_gestao.png',
                               planejamento_id=planejamento_id)

    except Exception as e:
        print(f"Erro ao carregar os dados: {e}")
        flash(f"Ocorreu um erro ao gerar os gráficos: {e}", 'danger')
        return redirect(url_for('autoavaliacaoegresso.importar_planilha_egresso'))




@autoavaliacaoegresso_route.route('/dashboard_egresso')
@login_required
def dashboard_egresso():
    plot_urls = request.args.getlist('plot_urls')  # Recebe os gráficos gerados
    return render_template('dashboard_egresso.html',
                       barras_ano_path='/static/graficos/barras_ano_conclusao.png',
                       pizza_recomendacao_path='/static/graficos/pizza_recomendacao.png',
                       scatter_path='/static/graficos/scatter_qualidade_vs_salario.png',
                       barras_avanco_path='/static/graficos/barras_avanco_cientifico.png',
                       barras_insumos_path='/static/graficos/barras_insumos_pesquisa.png',
                       barras_gestao_path='/static/graficos/barras_gestao.png')



def generate_egresso_dashboard(dataframe):
    plot_filenames = []
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Filtrar colunas que podem ser transformadas em gráficos
    for column in dataframe.columns:
        if dataframe[column].dtype == 'object':  # Considera apenas colunas de tipo 'object' (texto)
            if not dataframe[column].dropna().empty:  # Verifica se não está vazia
                filename = os.path.join(upload_folder, f'{uuid.uuid4()}.png')
                try:
                    plt.figure(figsize=(5, 4))
                    dataframe[column].value_counts().plot(kind='bar')
                    plt.title(column, fontsize=7)
                    plt.xlabel('Categorias', fontsize=6)
                    plt.ylabel('Valores', fontsize=7)
                    plt.xticks(rotation=45, fontsize=6)
                    plt.yticks(fontsize=6)
                    plt.tight_layout(pad=2)
                    plt.savefig(filename)
                    plt.close()
                    plot_filenames.append(filename)
                    print(f"Gráfico gerado e salvo: {filename}")  # Debug: caminho do gráfico salvo
                except Exception as e:
                    print(f'Erro ao gerar gráfico para a coluna {column}: {str(e)}')
    
    return plot_filenames




def processar_planilha_egresso(arquivo_planilha):
    graficos = []  # Lista para armazenar os nomes dos arquivos dos gráficos
    
    # Supondo que você carregue os dados da planilha aqui
    dados = pd.read_excel(arquivo_planilha)

    # Exemplo: Gerando gráficos com base nos dados da planilha
    for i, coluna in enumerate(dados.columns):
        plt.figure()
        dados[coluna].plot(kind='bar')
        nome_arquivo = f"grafico_{i}.png"
        caminho_completo = os.path.join("static/uploads", nome_arquivo)
        plt.savefig(caminho_completo)
        graficos.append(nome_arquivo)
    
    return graficos


@autoavaliacaoegresso_route.route('/gerar_pdf_egresso')
@login_required
def gerar_pdf_egresso():
    # Simulação de dados para teste
    objetivos = [
        'Expandir a oferta de disciplinas nas modalidades híbridas ou a distância',
        'Melhorar a reputação institucional',
        'Racionalizar recursos públicos'
    ]

    metas = [
        {'nome': 'Expandir a oferta de cursos', 'status': 'Em andamento', 'tempo_restante': '30'},
        {'nome': 'Reduzir a taxa de evasão', 'status': 'Concluída', 'tempo_restante': '0'}
    ]

    indicadores = [
        {'nome': 'Quantidade de publicações', 'peso': 6.2, 'frequencia': 'trimestral'}
    ]

    acoes = [
        {'nome': 'Acompanhar o desempenho dos discentes', 'execucao': 70, 'status': 'Em andamento', 'tempo_restante': '15'}
    ]

    # Gerar o PDF
    pdf = PDF()
    pdf.add_page()
    pdf.tabela_objetivos(objetivos)
    pdf.tabela_metas(metas)
    pdf.tabela_indicadores(indicadores)
    pdf.tabela_acoes(acoes)

    # Caminho para salvar o PDF
    pdf_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dashboard_egresso.pdf')
    pdf.output(pdf_filename)

    # Enviar o arquivo PDF para download
    return send_file(pdf_filename, as_attachment=True)