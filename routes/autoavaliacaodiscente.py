from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt  # Certifique-se de importar matplotlib
import seaborn as sns  # Se necessário, certifique-se de importar seaborn
from reportlab.pdfgen import canvas  # Certifique-se de importar canvas do reportlab
from io import BytesIO  # Para manipular imagens em buffer
import tempfile  # Certifique-se de importar tempfile


autoavaliacaodiscente_route = Blueprint('autoavaliacaodiscente', __name__)
UPLOAD_FOLDER = 'caminho_para_uploads'
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)

                # Salvar o arquivo CSV
                file.save(filepath)

                # Carregar o arquivo CSV com separador ";"
                df = pd.read_csv(filepath, encoding='ISO-8859-1', sep=';')

                # Se quiser selecionar as colunas numéricas automaticamente
                numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()

                # Se quiser especificar as colunas manualmente
                if not numerical_columns:
                    columns_to_cluster = [
                        'Como você avalia a qualidade das aulas e do material utilizado?  [Qualidade das aulas]', 
                        'Como você avalia a  infraestrutura do programa?  [Infraestrutura geral]', 
                        'Como você avalia o relacionamento entre você e: [os colegas]', 
                        'Como você avalia a gestão do programa? [Processo de gestão/Administrativo do Programa]'
                    ]
                else:
                    columns_to_cluster = numerical_columns

                # Remover as linhas com valores nulos
                df_cleaned = df[columns_to_cluster].replace('Sem condições de avaliar', float('nan')).dropna()

                # Normalizar os dados
                scaler = StandardScaler()
                df_scaled = scaler.fit_transform(df_cleaned)

                # Aplicar K-Means para clusterizar em 3 grupos
                kmeans = KMeans(n_clusters=3, random_state=42)
                kmeans.fit(df_scaled)

                # Adicionar os clusters ao DataFrame
                df_cleaned['Cluster'] = kmeans.labels_

                # Salvar o resultado com os clusters
                resultado_path = os.path.join(UPLOAD_FOLDER, 'resultado_clusters.csv')
                df_cleaned.to_csv(resultado_path, index=False)

                flash('Arquivo importado e analisado com sucesso!', 'success')
                return redirect(url_for('autoavaliacaodiscente.mostrar_dashboard_discente'))

            else:
                flash('Tipo de arquivo não permitido. Envie um arquivo CSV.', 'danger')
                return redirect(request.url)

    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
        flash(f"Ocorreu um erro ao processar o arquivo: {e}", 'danger')
        return redirect(request.url)

    return render_template('importar_planilha_discente.html')

@autoavaliacaodiscente_route.route('/dashboard_discente')
def mostrar_dashboard_discente():
    # Código que gera o dashboard
    # Carregar o arquivo da análise gerada
    analise_path = os.path.join(UPLOAD_FOLDER, 'analise_clusters.csv')
    
    if os.path.exists(analise_path):
        # Carregar os dados de análise
        df_analysis = pd.read_csv(analise_path)

        # Converter os dados de análise para dicionário (para passar ao template)
        analysis_data = df_analysis.to_dict()

        # Renderizar o template 'dashboard_analisediscente.html' com os dados de análise
        return render_template('dashboard_analisediscente.html', analysis_data=analysis_data)

    else:
        flash('Nenhum dado de análise disponível. Importe uma planilha e gere os clusters primeiro.', 'danger')
        return redirect(url_for('autoavaliacaodiscente.importar_planilha_discente'))



@autoavaliacaodiscente_route.route('/gerar_pdf_analise')
def gerar_pdf_analise():
    # Carregar o arquivo da análise gerada
    analise_path = os.path.join(UPLOAD_FOLDER, 'analise_clusters.csv')
    
    if os.path.exists(analise_path):
        # Carregar os dados de análise
        df_analysis = pd.read_csv(analise_path)
        
        # Criar o caminho para o arquivo PDF
        pdf_path = os.path.join(UPLOAD_FOLDER, 'analise_clusters_reportlab.pdf')
        
        # Criar o canvas para o PDF
        c = canvas.Canvas(pdf_path)
        
        # Adicionar título ao PDF
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 800, "Análise de Clusters - Relatório")

        # Posição inicial do texto
        y_position = 750
        c.setFont("Helvetica", 12)

        # Adicionar os dados da análise ao PDF
        for index, row in df_analysis.iterrows():
            if y_position < 100:
                c.showPage()  # Adicionar nova página se o espaço acabar
                y_position = 750
            c.drawString(50, y_position, f"Cluster {index}")
            y_position -= 20
            for col in df_analysis.columns:
                c.drawString(50, y_position, f"{col}: {row[col]}")
                y_position -= 20

        # Gerar gráfico de barras da distribuição de clusters
        plt.figure(figsize=(6, 4))
        sns.countplot(x='Cluster', data=df_analysis)
        plt.title('Distribuição de Clusters')

        # Criar um arquivo temporário para salvar o gráfico
        temp_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        plt.savefig(temp_img.name)  # Salvar o gráfico no arquivo temporário
        plt.close()

        # Adicionar gráfico ao PDF
        c.drawImage(temp_img.name, 50, y_position - 300, width=500, height=300)

        # Remover o arquivo temporário
        temp_img.close()
        os.unlink(temp_img.name)

        # Finalizar e salvar o PDF
        c.save()

        # Enviar o PDF gerado para download
        return send_file(pdf_path, as_attachment=True)

    else:
        flash('Nenhum dado de análise disponível. Importe uma planilha e gere os clusters primeiro.', 'danger')
        return redirect(url_for('autoavaliacaodiscente.importar_planilha_discente'))
