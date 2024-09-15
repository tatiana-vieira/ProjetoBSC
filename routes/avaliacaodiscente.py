from flask import Blueprint, render_template, request
from flask_login import login_required

# Definindo o blueprint para a autoavaliação discente
avaliacaodiscente_route = Blueprint('avaliacaodiscente', __name__)

# Rota para a aba de autoavaliação, com autenticação
@avaliacaodiscente_route.route('/autoavaliacao', methods=['GET', 'POST'])
@login_required
def autoavaliacao():
    if request.method == 'POST':
        # Coletar as respostas enviadas pelo formulário
        ano_ingresso = request.form['ano_ingresso']
        programa_vinculado = request.form['programa_vinculado']
        qualidade_aulas = request.form['qualidade_aulas']
        material_didatico = request.form['material_didatico']
        comentario_programa = request.form['comentario_programa']
        
        # Aqui, você pode salvar essas respostas ou fazer a análise com IA ou processamento
        return render_template('resultado.html', resultado={
            "Ano de Ingresso": ano_ingresso,
            "Programa Vinculado": programa_vinculado,
            "Qualidade das Aulas": qualidade_aulas,
            "Material Didático": material_didatico,
            "Comentários": comentario_programa
        })
    
    # Exibir o formulário de autoavaliação se for uma requisição GET
    return render_template('avalicaodiscente.html')