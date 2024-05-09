from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from .models import Users, Programa, PlanejamentoEstrategico, PDI,ObjetivoPE,Objetivo,MetaPE,AcaoPE,IndicadorPE,Valorindicador # Certifique-se de importar seus modelos corretamente
from routes.db import db
from flask_bcrypt import Bcrypt
from flask_login import login_user, login_required, LoginManager, current_user
from functools import wraps


planejamento_route = Blueprint('planejamento', __name__)
login_manager = LoginManager(planejamento_route)


# Implemente o decorador coordenador_required
def coordenador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'Coordenador':
            flash('Acesso negado. Apenas coordenadores podem acessar esta página.', 'danger')
            return redirect(url_for('login.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@planejamento_route.route('/cadastro_planejamentope', methods=['GET', 'POST'])
@coordenador_required
def cadastro_planejamentope():
    if request.method == 'POST':
        # Processar o formulário de cadastro de planejamento
        nome = request.form['nome']
        pdi_id = request.form['pdi_id']

        # Lógica para criar um novo planejamento estratégico
        novo_planejamento = PlanejamentoEstrategico(
            nome=nome,
            pdi_id=pdi_id,
            id_programa=current_user.programa_id  # Utilizando o programa_id do usuário atual
        )
        db.session.add(novo_planejamento)
        db.session.commit()

        flash('Planejamento cadastrado com sucesso!', 'success')
        return redirect(url_for('login.get_coordenador'))
    else:
        # Se o método for GET, renderize o formulário de cadastro
        pdis = PDI.query.all()
        
        # Verifique se o usuário está autenticado e tem um programa associado
        if current_user and hasattr(current_user, 'programa_id') and current_user.programa_id:
            programa_do_usuario = Programa.query.get(current_user.programa_id)
        else:
            flash('Nenhum programa associado encontrado para este usuário.', 'danger')
            return redirect(url_for('login.login_page'))

        return render_template('planejamento.html', pdis=pdis, programa_do_usuario=programa_do_usuario)
     
@planejamento_route.route('/sucesso_cadastro')
def sucesso_cadastro():
    return 'Indicador cadastrado com sucesso!'

#################################################################################################################################
@planejamento_route.route('/associar_objetivospe', methods=['GET', 'POST'])
def associar_objetivospe():
    if request.method == 'POST':
        # Aqui vai o código para lidar com o formulário submetido
        nome = request.form['nome']
        planejamento_estrategico_id = request.form['planejamento_id']
        objetivo_pdi_id = request.form['objetivo_id']

        # Cria um novo objetivo PE e o adiciona ao banco de dados
        novo_objetivo = ObjetivoPE(
            nome=nome,
            planejamento_estrategico_id=planejamento_estrategico_id,
            objetivo_pdi_id=objetivo_pdi_id
        )

        db.session.add(novo_objetivo)
        db.session.commit()

        flash('Objetivo cadastrado com sucesso!', 'success')
        return redirect(url_for('login.get_coordenador'))
    else:
        # Se o método não for POST, obtemos os dados necessários apenas do programa do Coordenador logado
        programa_id = current_user.programa_id
        planejamento_estrategico = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
        objetivos_por_planejamento = []

        # Para cada planejamento estratégico, obtemos os objetivos associados
        for pe in planejamento_estrategico:
            objetivos = Objetivo.query.filter_by(pdi_id=pe.pdi_id).all()
            objetivos_por_planejamento.append((pe, objetivos))

        # Se o programa existir, você pode acessar seus planejamentos estratégicos
        if programa_id:
            programa = Programa.query.get(programa_id)
            planejamentos = programa.planejamentos
            for planejamento in planejamentos:
                print(planejamento.nome)  # Ou qualquer outra operação que você deseje fazer com os planejamentos
        else:
            print("Programa não encontrado")

        # Renderizamos o formulário HTML com os dados obtidos
        return render_template('objetivope.html', objetivos_por_planejamento=objetivos_por_planejamento)

###################################################################################################################################
@planejamento_route.route('/associar_metaspe', methods=['GET', 'POST'])
def associar_metaspe():
    if request.method == 'POST':
        # Aqui vai o código para lidar com o formulário submetido
        nome = request.form['nome']
        objetivo_pe_id = request.form['objetivo_pe_id']
        porcentagem_execucao = request.form['porcentagem_execucao']
        
        # Verifica se o objetivo existe
        objetivo_pe = ObjetivoPE.query.get(objetivo_pe_id)
        if objetivo_pe is None:
            flash('Objetivo PE não encontrado!', 'error')
            return redirect(url_for('login.get_coordenador'))  # Usando 'login.get_coordenador' aqui
        
        # Cria uma nova meta PE e a associa ao objetivo PE
        nova_meta = MetaPE(
            nome=nome,
            objetivo_pe_id=objetivo_pe_id,
            porcentagem_execucao=porcentagem_execucao
        )

        db.session.add(nova_meta)
        db.session.commit()

        flash('Meta cadastrada com sucesso!', 'success')
        return redirect(url_for('login.get_coordenador'))  # Usando 'login.get_coordenador' aqui
    else:
        # Se o método não for POST, obtenha os dados necessários para o formulário
        # Obtenha o programa do Coordenador logado
        programa_id = current_user.programa_id
        
        # Busca os planejamentos estratégicos associados ao programa do Coordenador logado
        planejamentos_estrategicos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
        
        # Busca os objetivos PE associados aos planejamentos estratégicos do programa do Coordenador logado
        objetivos_pe = []
        for pe in planejamentos_estrategicos:
            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=pe.id).all()
            objetivos_pe.extend(objetivos)
        
        # Renderiza o formulário HTML com os dados obtidos
        return render_template('metaspe.html', planejamentos_estrategicos=planejamentos_estrategicos, objetivos_pe=objetivos_pe)
#####################################################################################################################################3
@planejamento_route.route('/associar_indicadorespe', methods=['GET', 'POST'])
def associar_indicadorespe():
    if request.method == 'POST':
        meta_pe_id = request.form['meta_pe_id']
        nome_indicador = request.form['nome']
        descricao = request.form['descricao']

        # Verifica se a meta PE existe e se está associada a um objetivo do programa do Coordenador
        meta_pe = MetaPE.query.get(meta_pe_id)
        if meta_pe is None:
            flash('Meta não encontrada!', 'error')
            return redirect(url_for('get_coordenador'))

        # Verifica se o indicador já existe na tabela IndicadorPE
        indicador_existente = IndicadorPE.query.filter_by(nome=nome_indicador, meta_pe_id=meta_pe_id).first()

        # Se o indicador já existir, obtenha o ID
        if indicador_existente:
            indicador_id = indicador_existente.id
        else:
            # Se o indicador não existir, adicione-o à tabela IndicadorPE
            novo_indicador = IndicadorPE(nome=nome_indicador, meta_pe_id=meta_pe_id, descricao=descricao)
            db.session.add(novo_indicador)
            db.session.commit()
            # Obtenha o ID do indicador recém-adicionado
            indicador_id = novo_indicador.id

        # Salvar os valores do indicador na tabela Valorindicador
        ano = request.form.getlist('ano[]')
        semestre = request.form.getlist('semestre[]')
        valor = request.form.getlist('valor[]')

        for ano, semestre, valor in zip(ano, semestre, valor):
            novo_valor = Valorindicador(indicadorpe_id=indicador_id, ano=ano, semestre=semestre, valor=valor)
            db.session.add(novo_valor)

        db.session.commit()

        flash('Indicador cadastrado com sucesso!', 'success')
        return redirect(url_for('login.get_coordenador'))
    else:
        # Se o método não for POST, obtenha os dados necessários para o formulário
        # Obtenha o programa do Coordenador logado
        programa_id = current_user.programa_id
        
        # Se o programa existir, obtenha os planejamentos estratégicos associados a ele
        if programa_id:
            planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
            
            # Inicialize uma lista para armazenar as metas associadas a objetivos associados a esses planejamentos estratégicos
            metas_pe_associadas = []
            
            # Para cada planejamento estratégico, obtenha os objetivos associados
            for planejamento in planejamentos:
                objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
                
                # Para cada objetivo, obtenha as metas associadas
                for objetivo in objetivos:
                    metas_pe = MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all()
                    metas_pe_associadas.extend(metas_pe)

            return render_template('indicadorpe.html', metas_pe=metas_pe_associadas)
        else:
            flash('Programa não encontrado!', 'error')
            return redirect(url_for('get_coordenador'))
#####################################################################################################################
#######################################################################################################################
@planejamento_route.route('/associar_acaope', methods=['GET', 'POST'])
def associar_acaope():
    if request.method == 'POST':
        meta_pe_id = request.form['meta_pe_id']
        nome = request.form['nome']
        porcentagem_execucao = request.form['porcentagem_execucao']   
        data_inicio = request.form['data_inicio']
        data_termino = request.form['data_termino']   
        responsavel=request.form['responsavel']
        status = request.form['status']
        observacao = request.form['observacao']

        # Verifica se a meta existe
        meta_pe = MetaPE.query.get(meta_pe_id)
        if meta_pe is None:
            flash('Meta não encontrada!', 'error')
            return redirect(url_for('get_coordenador'))
        
        # Cria uma nova ação associada à meta
        nova_acao = AcaoPE(nome=nome, meta_pe_id=meta_pe_id, porcentagem_execucao=porcentagem_execucao, data_inicio=data_inicio, data_termino=data_termino,
                       responsavel=responsavel,status=status, observacao=observacao )
        db.session.add(nova_acao)
        db.session.commit()

        flash('Ação cadastrada com sucesso!', 'success')
        return redirect(url_for('get_coordenador'))
    
    else:
        # Se o método não for POST, obtenha os dados necessários para o formulário
        # Obtenha o programa do Coordenador logado
        programa_id = current_user.programa_id
        
        # Se o programa existir, obtenha os planejamentos estratégicos associados a ele
        if programa_id:
            planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
            
            # Inicialize uma lista para armazenar as metas associadas a objetivos associados a esses planejamentos estratégicos
            metas_pe_associadas = []
            
            # Para cada planejamento estratégico, obtenha os objetivos associados
            for planejamento in planejamentos:
                objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
                
                # Para cada objetivo, obtenha as metas associadas
                for objetivo in objetivos:
                    metas_pe = MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all()
                    metas_pe_associadas.extend(metas_pe)

            return render_template('acaope.html', metas_pe=metas_pe_associadas)
        else:
            flash('Programa não encontrado!', 'error')
            return redirect(url_for('get_coordenador'))
        
########################################## Alterar ação #####################################################
@planejamento_route.route('/alterar_acaope/<int:acao_id>', methods=['GET', 'POST'])
def alterar_acaope(acao_id):
    # Busca a ação a ser alterada pelo ID
    acao = AcaoPE.query.get_or_404(acao_id)
    
    if request.method == 'POST':
        # Atualiza os campos da ação com os dados do formulário, se fornecidos
        if 'data_termino' in request.form:
            acao.data_termino = request.form['data_termino']
        if 'responsavel' in request.form:
            acao.responsavel = request.form['responsavel']
        if 'status' in request.form:
            acao.status = request.form['status']
        if 'observacao' in request.form:
            acao.observacao = request.form['observacao']
        
        # Salva as alterações no banco de dados
        db.session.commit()

        flash('Ação alterada com sucesso!', 'success')
        return redirect(url_for('login.get_coordenador'))
    else:
        # Retorna o formulário de alteração preenchido com os dados da ação
        return render_template('alterar_acaope.html', acao=acao)
    
################################################# Pro -reitor ###################################
@planejamento_route.route('/visualizar_programaspe')
def visualizar_programaspe():
    programas = Programa.query.all()
    return render_template('visualizar_programas.html', programas=programas)

@planejamento_route.route('/visualizar_dados_programa', methods=['POST'])
def visualizar_dados_programa():
    programa_id = request.form['programa']
    programa = Programa.query.get(programa_id)
    
    # Lógica para obter os dados do programa selecionado
    planejamentope = PlanejamentoEstrategico.query.all()
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.objetivo_pdi_id.in_([pdi.id for pdi in planejamentope])).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    indicadores = IndicadorPE.query.filter(IndicadorPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    
    # Passar os dados para o template
    return render_template('dados_programa.html', programa=programa, planejamentos=planejamentope, objetivos=objetivospe, metas=metaspe, indicadores=indicadores)