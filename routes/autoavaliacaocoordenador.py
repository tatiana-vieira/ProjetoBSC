from flask import Flask, render_template, request, flash, redirect, Blueprint
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

autoavaliacaocoordenador_route = Blueprint('autoavaliacaocoordenador', __name__)

# Caminho para salvar gráficos
GRAPH_FOLDER = 'static/graficos'
if not os.path.exists(GRAPH_FOLDER):
    os.makedirs(GRAPH_FOLDER)

@autoavaliacaocoordenador_route.route('/importar_planilha_coordenador', methods=['GET', 'POST'])
def importar_planilha_coordenador():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo enviado', 'danger')
            return redirect(request.url)
        
        file = request.files['file']

        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        # Verifica se o arquivo é um CSV
        if file and file.filename.endswith('.csv'):
            try:
                # Lê o arquivo CSV diretamente da memória
                data = pd.read_csv(file, delimiter=';')
                
                # Exibir as primeiras linhas para ver se foi carregado corretamente
                print(data.head())
                
                # Salvar a tabela em uma lista para exibir no HTML
                table = data.to_html(classes='table table-striped')

                # Gerar um gráfico básico de barras (por exemplo, da primeira coluna numérica)
                numeric_columns = data.select_dtypes(include=['float64', 'int64']).columns
                if len(numeric_columns) > 0:
                    plt.figure(figsize=(10, 6))
                    sns.histplot(data[numeric_columns[0]], kde=False, bins=10)
                    plt.title(f'Histograma de {numeric_columns[0]}')
                    grafico_path = os.path.join(GRAPH_FOLDER, 'grafico.png')
                    plt.savefig(grafico_path)
                    plt.close()
                
                # Calcular média, moda e mediana
                estatisticas = {}
                for col in numeric_columns:
                    estatisticas[col] = {
                        'media': data[col].mean(),
                        'mediana': data[col].median(),
                        'moda': data[col].mode()[0]
                    }

                flash('Arquivo CSV carregado com sucesso!', 'success')
                return render_template('dashboard_coordenador.html', table=table, estatisticas=estatisticas, grafico='grafico.png')
            
            except Exception as e:
                flash(f"Erro ao processar o arquivo: {e}", 'danger')
                return redirect(request.url)
        else:
            flash('Por favor, envie um arquivo CSV válido', 'danger')
            return redirect(request.url)

    return render_template('importar_planilha_coordenador.html')
