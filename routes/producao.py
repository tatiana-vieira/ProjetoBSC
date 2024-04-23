from flask import Blueprint, render_template
from flask import jsonify
from .models import Producaointelectual
import json

producao_route = Blueprint('producao', __name__)

@producao_route.route('/producao')  # Defina a rota para exibir todos as produções
def exibir_producao():
    try:
        # Consulta na tabela Engajamento
        producao = Producaointelectual.query.all()

        # Serializa os resultados para JSON
        producao_list = [{
            'codigoprograma': row.codigoprograma,
            'sigla':row.sigla,
            'instituicaoensino':row.instituicaoensino,
            'anaopublicacao':row.nomeprograma,
            'titulo':row.titulo,
            'producaoglosada':row.producaoglosada,
            'ordem':row.ordem,
            'autor':row.autor,
            'nomeprograma':row.nomeprograma,
            'categoria':row.categoria,
            'tipoproducao':row.tipoproducao,
            'subtipo':row.subtipo,
            'nomedetalhamento':row.nomedetalhamento,
            'valordetalhamento':row.valordetalhamento,
            'areaconcentracao':row.areaconcentracao,
            'linhapesquisa':row.linhapesquisa,
            'projetopesquisa':row.projetopesquisa,
            'prodvinculadaconclusao':row.prodvinculadaconclusao

        } for row in producao]

        # Retornar os resultados em formato JSON
        return jsonify(producao_list)
    
    except Exception as e:
        print(e)
        return "Erro ao buscar dados de Eixo Multidimensional"
    
    
@producao_route.route('/producao/visualizar')
def mostrar_producao():
    try:
        producao_consulta = Producaointelectual.query.filter(Producaointelectual.codigoprograma == '32003013008P4').all() 
        resultado = [{'titulo':row.titulo,'autor': row.autor,'categoria': row.categoria,
        'tipoproducao': row.tipoproducao,'subtipo': row.subtipo,'areaconcentracao': row.areaconcentracao, 
        'linhapesquisa': row.linhapesquisa,'projetopesquisa': row.projetopesquisa,'anaopublicacao': row.anaopublicacao} for row in producao_consulta]
       
          # Retorne os resultados em formato JSON    
        return render_template('producao.html', producao=resultado)

        
    except Exception as e:
        print(e)
        return str(e)
    
   

    