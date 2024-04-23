from flask import Blueprint, render_template
from flask import jsonify
from .models import Engajamento
from .models import Ensino
from .models import Orientacao
from .models import Transfconhecimento
from .models import Pesquisar
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json

multidimensional_route = Blueprint('multidimensional', __name__)

@multidimensional_route.route('/multidimensional/engajreg')  # Defina a rota para exibir todos os discentes
def exibir_engajreg():
    try:
        # Consulta na tabela Engajamento
        engajreg = Engajamento.query.all()

        # Serializa os resultados para JSON
        engajreg_list = [{
            'nome': row.nome,
            'estagio': row.estagio,
            'publiconjuntareg': row.publiconjuntareg,
            'rendasfontesreg': row.rendasfontesreg,
            'codigo': row.codigo,
            'sigla': row.sigla,
            'pais': row.pais,
            'programa': row.programa,
            'areatematica': row.areatematica,
            'estagioletra': row.estagioletra,
            'publiconjuntaregletra': row.publiconjuntaregletra,
            'rendasfontesregletra': row.rendasfontesregletra,
            'regiao': row.regiao
        } for row in engajreg]

        # Retornar os resultados em formato JSON
        return jsonify(engajreg_list)
    
    except Exception as e:
        print(e)
        return "Erro ao buscar dados de engajamento"
    
@multidimensional_route.route('/multidimensional/ensino')    
def exibir_ensino():
    try:
        # Consulta na tabela Ensino
        ensino = Ensino.query.all()

        # Serializa os resultados para JSON
        ensino_list = [{
            'nome': row.nome,
            'mestradotempocerto': row.mestradotempocerto,
            'equilibriogenero': row.equilibriogenero,
            'pessoalacaddoutorado': row.pessoalacaddoutorado,
            'contatoambientetrabalho': row.contatoambientetrabalho,
            'proporcao': row.proporcao,
            'mestratempocertoletra': row.mestratempocertoletra,
            'equilibriogeneroletra': row.equilibriogeneroletra,
            'pessoalacademicoletra': row.pessoalacademicoletra,
            'contaambienteletra': row.contaambienteletra,
            'proporcaoletra': row.proporcaoletra,
            'codigo': row.codigo,
            'sigla': row.sigla,
            'pais': row.pais,
            'programa': row.programa,
            'areatematica': row.areatematica,
            'regiao': row.regiao
        } for row in ensino]
    
        # Retornar os resultados em formato JSON
        return jsonify(ensino_list)
    except Exception as e:
        print(e)
        return "Erro ao buscar dados de ensino"
    
@multidimensional_route.route('/multidimensional/orientacao')
def exibir_orientacao():
    try:
        # Consulta na tabela Ensino
     orientacao = Orientacao.query.all()
     # Consulta na tabela orientacaointern
     orientacao_list = [{'nome': row.nome,'orientacaointernmestrado': row.orientacaointernmestrado,'oportunidadeestudarexterior': row.oportunidadeestudarexterior,
                                        'doutaradointer': row.doutaradointer,'publconjintern': row.publconjintern,'bolsapesquisaintern': row.bolsapesquisaintern,                               
                                        'codigo': row.codigo,'sigla': row.sigla,'pais': row.pais,'programa': row.programa,'areatematica': row.areatematica,'oportuniestexteletra': row.oportuniestexteletra,
                                        'coutinterletra': row.coutinterletra,'publconinterletra': row.publconinterletra, 'bolsapesletra': row.bolsapesletra,'orientacaointernmestradoletra': row.orientacaointernmestradoletra,
                                        'regiao': row.regiao} for row in orientacao]
      # Retornar os resultados em formato JSON
     return jsonify(orientacao_list)
    except Exception as e:
        print(e)
        return "Erro ao buscar dados de Orientação Internacional"   

@multidimensional_route.route('/multidimensional/transfconhecimento')    
def exibir_transfconhecimento():
 try:
    transfconhecimento= Transfconhecimento.query.all()
    transfconhecimento_list = [{'nome':row.nome,'rendafonteprivada':row.rendafonteprivada,'copublicparcind': row.copublicparcind,
                                          'publcitadaspatentes':row.publcitadaspatentes,'codigo':row.codigo,'sigla':row.sigla,'pais':row.pais,'programa':row.programa,
                                          'areatematica':row.areatematica,'rendaletra':row.rendaletra,' copubletra':row. copubletra,'publicitadasletra':row.publicitadasletra,
                                          'regiao':row.regiao} for row in transfconhecimento]
# Retornar os resultados em formato JSON
    return jsonify(transfconhecimento_list)
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de Transferência de Conhecimento"   


@multidimensional_route.route('/multidimensional/pesquisar')   
def exibir_pesquisar():
 try:
    pesquisar= Pesquisar.query.all()
    pesquisar_list = [{'nome':row.nome,'receitapesquisaexterna':row.receitapesquisaexterna,'produtividadedoutorado': row.produtividadedoutorado,
                                 'publpesqabsoluto':row.publpesqabsoluto,'taxacitacao': row.taxacitacao,'publicacaomaicitada':row.publicacaomaicitada,
                                 'publicacaointerdisciplinar': row.publicacaointerdisciplinar,'publicacaoacessoaberto': row.publicacaoacessoaberto,'orientacaoopesqensino':row.orientacaoopesqensino,
                                 'autoras': row.autoras,'codigo': row.codigo,'sigla':row.sigla,'pais': row.pais,'programa':row.programa,'areatematica':row.areatematica,
                                 'receitapesquisaexternaletra': row.receitapesquisaexternaletra,'produtividadedoutoradoletra': row.produtividadedoutoradoletra,'publpesqabsolutoletra':row.publpesqabsolutoletra,'taxacitacaoletra': row.taxacitacaoletra,
                                 'publicacaomaicitadaletra':row.publicacaomaicitadaletra,'publicacaointerdisciplinarletra':row.publicacaointerdisciplinarletra,
                                 'publicacaoacessoabertoletra':row.publicacaoacessoabertoletra,'orientacaoopesqensinoletra':row.orientacaoopesqensinoletra,
                                 'autorasletra':row.autorasletra,'regiao':row.regiao} for row in pesquisar]

    return jsonify(pesquisar_list)
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de Pesquisar"   
 
##########################################Consultas da areatemática = 'Ciencia da Computação'##########################################
@multidimensional_route.route('/multidimensional/ensinoaprendizado')  
def exibir_graficosensino(): 
 try: 
    consulta_ensinoaprendiz2 = Ensino.query.filter(Ensino.areatematica == 'Ciência da Computação').all()     
    df_ensinoaprendiz2= [{'nome':row.nome,'mestradotempocerto':row.mestradotempocerto,'pessoalacaddoutorado': row.pessoalacaddoutorado,
    'contatoambientetrabalho': row.contatoambientetrabalho, 'proporcao': row.proporcao,'programa': row.programa} for row in consulta_ensinoaprendiz2]
    df_ensino2 = [{'nome':row.nome,'mestradotempocerto':row.mestradotempocerto,'programa': row.programa} for row in consulta_ensinoaprendiz2]
    df_contato = [{'nome':row.nome,'contatoambientetrabalho':row.contatoambientetrabalho,'programa': row.programa} for row in consulta_ensinoaprendiz2]
    df_proporcao= [{'nome':row.nome,'proporcao':row.proporcao,'programa': row.programa} for row in consulta_ensinoaprendiz2]
 
# Retorne os resultados em formato JSON    
    return jsonify( df_ensinoaprendiz2,df_ensino2,df_contato,df_proporcao)

 except Exception as e:
        print(e)
        return "Erro ao buscar dados de consulta de ensino aprendizado"   

@multidimensional_route.route('/multidimensional/pesquisarconsulta')  
def exibir_graficopesquisar(): 
 try:   
    # Consulta para obter dados da tabela Pesquisar
    consulta_receita = Pesquisar.query.filter(Pesquisar.areatematica == 'Ciência da Computação').all()      
    df_receita= [{'receitapesquisaexterna':row.receitapesquisaexterna,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
    df_pesqabsoluto= [{'publpesqabsoluto':row.publpesqabsoluto,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
    df_pubacesso = [{'publicacaoacessoaberto':row.publicacaoacessoaberto,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
    df_publicacaomaicitada= [{'publicacaomaicitada':row.publicacaomaicitada,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
    df_autoras= [{'autoras':row.autoras,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
  
  # Retorne os resultados em formato JSON    
    return jsonify(df_receita,df_pesqabsoluto,df_pubacesso,df_publicacaomaicitada,df_autoras)
 
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de consulta de Pesquisa"   
    # Consulta para obter dados da tabela Transferência de Conhecimento

@multidimensional_route.route('/multidimensional/conhecimento')  
def exibir_graficoconhecimento(): 
 try:
    consulta_transfconhecimento1 = Transfconhecimento.query.filter(Transfconhecimento.areatematica == 'Ciência da Computação').all()          
    df_transfconhecimento1= [{'rendafonteprivada':row.rendafonteprivada,'nome':row.nome,'programa': row.programa} for row in consulta_transfconhecimento1]
    
    # Retorne os resultados em formato JSON    
    return jsonify(df_transfconhecimento1)
 
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de consulta de TransferÊncia de Conhecimento"   
       
@multidimensional_route.route('/multidimensional/orientacaointernacional')  
def exibir_graficoorientaca(): 
 try: 
   # Construa a consulta SQL corretamente
    consulta_orientacaointern1 = Orientacao.query.filter(Orientacao.areatematica == 'Ciência da Computação').all()
    df_orientacaointern1= [{'orientacaointernmestrado':row.orientacaointernmestrado,'nome':row.nome,'programa': row.programa} for row in consulta_orientacaointern1]
        
        # Retorne os resultados em formato JSON
    return jsonify(df_orientacaointern1)
              
 except Exception as e:  
     print(e)  
     return "Erro ao buscar dados de consulta de Orientação Internacional"  

     
@multidimensional_route.route('/multidimensional/engajamentoregional')  
def exibir_graficoregional1(): 
    try: 
        # Construa a consulta SQL corretamente
        consulta_engajreg1 = Engajamento.query.filter(Engajamento.areatematica == 'Ciência da Computação').all()
        df_engajreg1 = [{'publiconjuntareg': row.publiconjuntareg, 'nome': row.nome, 'programa': row.programa} for row in consulta_engajreg1]
        df_engajreg2 = [{'rendasfontesreg':row.rendasfontesreg,'nome':row.nome,'programa': row.programa} for row in consulta_engajreg1]
        df_engajreg3 = [{'estagio':row.estagio,'nome':row.nome,'programa': row.programa} for row in consulta_engajreg1]
        # Retorne os resultados em formato JSON
        return jsonify(df_engajreg1,df_engajreg2,df_engajreg3)
              
    except Exception as e:  
     print(e)  
     return "Erro ao buscar dados de consulta de Engajamento Regional"  

from flask import Blueprint, render_template
from flask import jsonify
from .models import Engajamento
from .models import Ensino
from .models import Orientacao
from .models import Transfconhecimento
from .models import Pesquisar

multidimensional_route = Blueprint('um', __name__)

@multidimensional_route.route('/multidimensional/engajreg')  # Defina a rota para exibir todos os discentes
def exibir_engajreg():
    try:
        # Consulta na tabela Engajamento
        engajreg = Engajamento.query.all()

        # Serializa os resultados para JSON
        engajreg_list = [{
            'nome': row.nome,
            'estagio': row.estagio,
            'publiconjuntareg': row.publiconjuntareg,
            'rendasfontesreg': row.rendasfontesreg,
            'codigo': row.codigo,
            'sigla': row.sigla,
            'pais': row.pais,
            'programa': row.programa,
            'areatematica': row.areatematica,
            'estagioletra': row.estagioletra,
            'publiconjuntaregletra': row.publiconjuntaregletra,
            'rendasfontesregletra': row.rendasfontesregletra,
            'regiao': row.regiao
        } for row in engajreg]

        # Retornar os resultados em formato JSON
        return jsonify(engajreg_list)
    
    except Exception as e:
        print(e)
        return "Erro ao buscar dados de engajamento"
    
@multidimensional_route.route('/multidimensional/ensino')    
def exibir_ensino():
    try:
        # Consulta na tabela Ensino
        ensino = Ensino.query.all()

        # Serializa os resultados para JSON
        ensino_list = [{
            'nome': row.nome,
            'mestradotempocerto': row.mestradotempocerto,
            'equilibriogenero': row.equilibriogenero,
            'pessoalacaddoutorado': row.pessoalacaddoutorado,
            'contatoambientetrabalho': row.contatoambientetrabalho,
            'proporcao': row.proporcao,
            'mestratempocertoletra': row.mestratempocertoletra,
            'equilibriogeneroletra': row.equilibriogeneroletra,
            'pessoalacademicoletra': row.pessoalacademicoletra,
            'contaambienteletra': row.contaambienteletra,
            'proporcaoletra': row.proporcaoletra,
            'codigo': row.codigo,
            'sigla': row.sigla,
            'pais': row.pais,
            'programa': row.programa,
            'areatematica': row.areatematica,
            'regiao': row.regiao
        } for row in ensino]
    
        # Retornar os resultados em formato JSON
        return jsonify(ensino_list)
    except Exception as e:
        print(e)
        return "Erro ao buscar dados de ensino"
    
@multidimensional_route.route('/multidimensional/orientacao')
def exibir_orientacao():
    try:
        # Consulta na tabela Ensino
     orientacao = Orientacao.query.all()
     # Consulta na tabela orientacaointern
     orientacao_list = [{'nome': row.nome,'orientacaointernmestrado': row.orientacaointernmestrado,'oportunidadeestudarexterior': row.oportunidadeestudarexterior,
                                        'doutaradointer': row.doutaradointer,'publconjintern': row.publconjintern,'bolsapesquisaintern': row.bolsapesquisaintern,                               
                                        'codigo': row.codigo,'sigla': row.sigla,'pais': row.pais,'programa': row.programa,'areatematica': row.areatematica,'oportuniestexteletra': row.oportuniestexteletra,
                                        'coutinterletra': row.coutinterletra,'publconinterletra': row.publconinterletra, 'bolsapesletra': row.bolsapesletra,'orientacaointernmestradoletra': row.orientacaointernmestradoletra,
                                        'regiao': row.regiao} for row in orientacao]
      # Retornar os resultados em formato JSON
     return jsonify(orientacao_list)
    except Exception as e:
        print(e)
        return "Erro ao buscar dados de Orientação Internacional"   

@multidimensional_route.route('/multidimensional/transfconhecimento')    
def exibir_transfconhecimento():
 try:
    transfconhecimento= Transfconhecimento.query.all()
    transfconhecimento_list = [{'nome':row.nome,'rendafonteprivada':row.rendafonteprivada,'copublicparcind': row.copublicparcind,
                                          'publcitadaspatentes':row.publcitadaspatentes,'codigo':row.codigo,'sigla':row.sigla,'pais':row.pais,'programa':row.programa,
                                          'areatematica':row.areatematica,'rendaletra':row.rendaletra,' copubletra':row. copubletra,'publicitadasletra':row.publicitadasletra,
                                          'regiao':row.regiao} for row in transfconhecimento]
# Retornar os resultados em formato JSON
    return jsonify(transfconhecimento_list)
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de Transferência de Conhecimento"   


@multidimensional_route.route('/multidimensional/pesquisar')   
def exibir_pesquisar():
 try:
    pesquisar= Pesquisar.query.all()
    pesquisar_list = [{'nome':row.nome,'receitapesquisaexterna':row.receitapesquisaexterna,'produtividadedoutorado': row.produtividadedoutorado,
                                 'publpesqabsoluto':row.publpesqabsoluto,'taxacitacao': row.taxacitacao,'publicacaomaicitada':row.publicacaomaicitada,
                                 'publicacaointerdisciplinar': row.publicacaointerdisciplinar,'publicacaoacessoaberto': row.publicacaoacessoaberto,'orientacaoopesqensino':row.orientacaoopesqensino,
                                 'autoras': row.autoras,'codigo': row.codigo,'sigla':row.sigla,'pais': row.pais,'programa':row.programa,'areatematica':row.areatematica,
                                 'receitapesquisaexternaletra': row.receitapesquisaexternaletra,'produtividadedoutoradoletra': row.produtividadedoutoradoletra,'publpesqabsolutoletra':row.publpesqabsolutoletra,'taxacitacaoletra': row.taxacitacaoletra,
                                 'publicacaomaicitadaletra':row.publicacaomaicitadaletra,'publicacaointerdisciplinarletra':row.publicacaointerdisciplinarletra,
                                 'publicacaoacessoabertoletra':row.publicacaoacessoabertoletra,'orientacaoopesqensinoletra':row.orientacaoopesqensinoletra,
                                 'autorasletra':row.autorasletra,'regiao':row.regiao} for row in pesquisar]

    return jsonify(pesquisar_list)
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de Pesquisar"   
 
##########################################Consultas da areatemática = 'Ciencia da Computação'##########################################
@multidimensional_route.route('/multidimensional/ensinoaprendizado')  
def exibir_graficosensino(): 
 try: 
    consulta_ensinoaprendiz2 = Ensino.query.filter(Ensino.areatematica == 'Ciência da Computação').all()     
    df_ensinoaprendiz2= [{'nome':row.nome,'mestradotempocerto':row.mestradotempocerto,'pessoalacaddoutorado': row.pessoalacaddoutorado,
    'contatoambientetrabalho': row.contatoambientetrabalho, 'proporcao': row.proporcao,'programa': row.programa} for row in consulta_ensinoaprendiz2]
    df_ensino2 = [{'nome':row.nome,'mestradotempocerto':row.mestradotempocerto,'programa': row.programa} for row in consulta_ensinoaprendiz2]
    df_contato = [{'nome':row.nome,'contatoambientetrabalho':row.contatoambientetrabalho,'programa': row.programa} for row in consulta_ensinoaprendiz2]
    df_proporcao= [{'nome':row.nome,'proporcao':row.proporcao,'programa': row.programa} for row in consulta_ensinoaprendiz2]
 
 # Retorne os resultados em formato JSON    
    return jsonify( df_ensinoaprendiz2,df_ensino2,df_contato,df_proporcao)
 # Retornar o JSON do gráfico
  
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de consulta de ensino aprendizado"   
 
@multidimensional_route.route('/multidimensional/pesquisarconsulta')  
def exibir_graficopesquisar(): 
 try:   
    # Consulta para obter dados da tabela Pesquisar
    consulta_receita = Pesquisar.query.filter(Pesquisar.areatematica == 'Ciência da Computação').all()      
    df_receita= [{'receitapesquisaexterna':row.receitapesquisaexterna,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
    df_pesqabsoluto= [{'publpesqabsoluto':row.publpesqabsoluto,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
    df_pubacesso = [{'publicacaoacessoaberto':row.publicacaoacessoaberto,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
    df_publicacaomaicitada= [{'publicacaomaicitada':row.publicacaomaicitada,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
    df_autoras= [{'autoras':row.autoras,'nome':row.nome,'programa': row.programa} for row in consulta_receita]
  
  # Retorne os resultados em formato JSON    
    return jsonify(df_receita,df_pesqabsoluto,df_pubacesso,df_publicacaomaicitada,df_autoras)
 
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de consulta de Pesquisa"   
    # Consulta para obter dados da tabela Transferência de Conhecimento

@multidimensional_route.route('/multidimensional/conhecimento')  
def exibir_graficoconhecimento(): 
 try:
    consulta_transfconhecimento1 = Transfconhecimento.query.filter(Transfconhecimento.areatematica == 'Ciência da Computação').all()          
    df_transfconhecimento1= [{'rendafonteprivada':row.rendafonteprivada,'nome':row.nome,'programa': row.programa} for row in consulta_transfconhecimento1]
    
    # Retorne os resultados em formato JSON    
    return jsonify(df_transfconhecimento1)
 
 except Exception as e:
        print(e)
        return "Erro ao buscar dados de consulta de TransferÊncia de Conhecimento"   
       
@multidimensional_route.route('/multidimensional/orientacaointernacional')  
def exibir_graficoorientaca(): 
 try: 
   # Construa a consulta SQL corretamente
    consulta_orientacaointern1 = Orientacao.query.filter(Orientacao.areatematica == 'Ciência da Computação').all()
    df_orientacaointern1= [{'orientacaointernmestrado':row.orientacaointernmestrado,'nome':row.nome,'programa': row.programa} for row in consulta_orientacaointern1]
        
        # Retorne os resultados em formato JSON
    return jsonify(df_orientacaointern1)
              
 except Exception as e:  
     print(e)  
     return "Erro ao buscar dados de consulta de Orientação Internacional"  

     
@multidimensional_route.route('/multidimensional/grafico')
def exibir_graficoensino():
    try:
        # Consulta ao banco de dados para obter os dados
        consulta_ensinoaprendiz4 = Ensino.query.filter(Ensino.areatematica == 'Ciência da Computação').all()
        df_ensinoaprendiz4 = pd.DataFrame([{'nome': row.nome, 'mestradotempocerto': row.mestradotempocerto} for row in consulta_ensinoaprendiz4])

        # Convertendo o DataFrame para JSON
        dados_json = df_ensinoaprendiz4.to_json(orient='records', force_ascii=False)
        print(dados_json)

        # Retornar o JSON dos dados para o template HTML
        return render_template('multidimensional.html', dados_json=dados_json)
    except Exception as e:
        print(e)
        return "Erro ao buscar dados de consulta de ensino aprendizado"
