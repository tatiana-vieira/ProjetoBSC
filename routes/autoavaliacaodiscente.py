from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np  # Importar o NumPy para cálculo de linha de tendência
from werkzeug.utils import secure_filename
import pdfkit
from flask import send_file
from flask import render_template_string


autoavaliacaodiscente_route = Blueprint('autoavaliacaodiscente', __name__)
UPLOAD_FOLDER = 'caminho_para_uploads'
GRAPH_FOLDER = 'static/graficos'  # Definição do GRAPH_FOLDER
ALLOWED_EXTENSIONS = {'xlsx'}

# Certifique-se de que o diretório para salvar os gráficos existe
if not os.path.exists(GRAPH_FOLDER):
    os.makedirs(GRAPH_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@autoavaliacaodiscente_route.route('/dashboard_discente/<int:planejamento_id>')
def mostrar_dashboard_discente(planejamento_id):
    try:
        # Carregar os dados relevantes do CSV salvo
        csv_path = os.path.join(UPLOAD_FOLDER, 'dados_relevantes.csv')
        if not os.path.exists(csv_path):
            flash('Arquivo de dados não encontrado. Importe a planilha primeiro.', 'danger')
            return redirect(url_for('autoavaliacaodiscente.importar_planilha_discente'))

        df = pd.read_csv(csv_path)

        # Convertendo colunas para valores numéricos (se houver erros, será convertido para NaN)
        df['Qualidade das aulas'] = pd.to_numeric(df['Qualidade das aulas'], errors='coerce')
        df['Infraestrutura geral'] = pd.to_numeric(df['Infraestrutura geral'], errors='coerce')
        df['ano_ingresso'] = pd.to_numeric(df['ano_ingresso'], errors='coerce')

        # Remover linhas com valores NaN nas colunas importantes
        df.dropna(subset=['Qualidade das aulas', 'Infraestrutura geral', 'ano_ingresso'], inplace=True)

        # Criar gráficos e salvar nas pastas correspondentes
        plt.figure(figsize=(6, 6))
        df['Qualidade das aulas'].value_counts().plot(kind='pie', autopct='%1.1f%%', startangle=90)
        plt.title('Distribuição da Qualidade das Aulas')
        pizza_path = os.path.join(GRAPH_FOLDER, 'pizza_qualidade_aulas.png')
        plt.savefig(pizza_path)
        plt.close()

        plt.figure(figsize=(9, 8))
        df.groupby('ano_ingresso')['Infraestrutura geral'].mean().plot(kind='bar', color='purple')
        plt.title('Média de Infraestrutura Geral por Ano de Ingresso')
        barras_path = os.path.join(GRAPH_FOLDER, 'barras_infraestrutura.png')
        plt.savefig(barras_path)
        plt.close()

        plt.figure(figsize=(9, 8))
        df.groupby('ano_ingresso')['Qualidade das aulas'].mean().plot(kind='line', marker='o', color='blue')
        plt.title('Tendência da Qualidade das Aulas ao Longo dos Anos')
        linha_path = os.path.join(GRAPH_FOLDER, 'linha_qualidade_aulas.png')
        plt.savefig(linha_path)
        plt.close()

        plt.figure(figsize=(9, 8))
        df['Qualidade das aulas'].plot(kind='hist', bins=10, color='orange', alpha=0.7)
        plt.title('Histograma da Qualidade das Aulas')
        histograma_path = os.path.join(GRAPH_FOLDER, 'histograma_qualidade_aulas.png')
        plt.savefig(histograma_path)
        plt.close()

        plt.figure(figsize=(9, 8))
        plt.scatter(df['Infraestrutura geral'], df['Qualidade das aulas'], color='green', alpha=0.5)
        m, b = np.polyfit(df['Infraestrutura geral'], df['Qualidade das aulas'], 1)
        plt.plot(df['Infraestrutura geral'], m * df['Infraestrutura geral'] + b, color='red')
        plt.title('Infraestrutura Geral vs. Qualidade das Aulas com Linha de Tendência')
        scatter_path = os.path.join(GRAPH_FOLDER, 'dispersao_tendencia.png')
        plt.savefig(scatter_path)
        plt.close()

        # Passar os caminhos dos gráficos para o template
        return render_template('dashboard_discente.html', 
                               pizza_path='graficos/pizza_qualidade_aulas.png',
                               barras_path='graficos/barras_infraestrutura.png',
                               linha_path='graficos/linha_qualidade_aulas.png',
                               histograma_path='graficos/histograma_qualidade_aulas.png',
                               scatter_path='graficos/dispersao_tendencia.png',
                               planejamento_id=planejamento_id)

    except Exception as e:
        print(f"Erro ao carregar os dados: {e}")
        flash(f"Ocorreu um erro ao gerar os gráficos: {e}", 'danger')
        return redirect(url_for('autoavaliacaodiscente.importar_planilha_discente'))

  

@autoavaliacaodiscente_route.route('/importar_planilha_discente', methods=['GET', 'POST'])
def importar_planilha_discente():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('Nenhum arquivo foi enviado.', 'danger')
                return redirect(request.url)

            file = request.files['file']

            if file.filename == '':
                flash('Nenhum arquivo selecionado.', 'danger')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                # Verifica se a pasta de upload existe, e cria se necessário
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)

                # Salva o arquivo no caminho especificado
                file.save(filepath)

                # Carrega a planilha em um DataFrame Pandas
                df = pd.read_excel(filepath)

                # Remover espaços em branco dos nomes das colunas
                df.columns = df.columns.str.strip()

                # Verifique se as colunas necessárias estão presentes
                required_columns = ['Qualidade das aulas', 'Infraestrutura geral', 
                                    'Processo de gestão/Administrativo do Programa', 'ano_ingresso']
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    flash(f"Erro: As seguintes colunas estão ausentes na planilha: {', '.join(missing_columns)}", 'danger')
                    return redirect(request.url)

                # Processar os dados necessários e salvar em CSV
                dados_relevantes = df[required_columns]
                dados_relevantes.to_csv(os.path.join(UPLOAD_FOLDER, 'dados_relevantes.csv'), index=False)

                flash('Arquivo importado com sucesso!', 'success')

                # Certifique-se de passar o planejamento_id correto ao redirecionar
                planejamento_id = 1  # Você precisa substituir este valor pelo valor correto
                return redirect(url_for('autoavaliacaodiscente.mostrar_dashboard_discente', planejamento_id=planejamento_id))
            else:
                flash('Tipo de arquivo não permitido. Envie um arquivo .xlsx', 'danger')
                return redirect(request.url)

    except Exception as e:
        print(f"Erro ao processar a planilha: {e}")
        flash(f"Ocorreu um erro ao processar o arquivo: {e}", 'danger')
        return redirect(request.url)

    return render_template('importar_planilha_discente.html')



@autoavaliacaodiscente_route.route('/gerar_pdf/<int:planejamento_id>')
def gerar_pdf(planejamento_id):
    try:
        # Usar os gráficos que foram gerados na função `mostrar_dashboard_discente`
        pizza_path = 'graficos/pizza_qualidade_aulas.png'
        barras_path = 'graficos/barras_infraestrutura.png'
        linha_path = 'graficos/linha_qualidade_aulas.png'
        histograma_path = 'graficos/histograma_qualidade_aulas.png'
        scatter_path = 'graficos/dispersao_tendencia.png'

        # Renderizar o template HTML com os gráficos
        rendered_html = render_template('dashboard_discente.html', 
                                        pizza_path=pizza_path, 
                                        barras_path=barras_path, 
                                        linha_path=linha_path, 
                                        histograma_path=histograma_path, 
                                        scatter_path=scatter_path,
                                        planejamento_id=planejamento_id)

        # Gerar o PDF a partir do HTML renderizado, incluindo os gráficos
        pdf_path = f'static/relatorios/autoavaliacao_discente_{planejamento_id}.pdf'
        pdfkit.from_string(rendered_html, pdf_path)

        # Enviar o PDF gerado para download
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        flash(f"Ocorreu um erro ao gerar o PDF: {e}", 'danger')
        return redirect(url_for('autoavaliacaodiscente.mostrar_dashboard_discente', planejamento_id=planejamento_id))
