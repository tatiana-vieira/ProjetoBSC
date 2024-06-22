from flask import Blueprint, render_template, redirect, url_for, request, flash, session,jsonify,send_file
from .models import Users, Programa,CadeiaValor, PlanejamentoEstrategico,Risco, PDI,Objetivo,ObjetivoPE,MetaPE,AcaoPE,IndicadorPlan,Valorindicador,Valormeta # Certifique-se de importar seus modelos corretamente
from routes.db import db
from flask_bcrypt import Bcrypt
import io
import pandas as pd
from flask_login import  login_required, LoginManager, current_user
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from sqlalchemy.orm import joinedload


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
##################################################################33
@planejamento_route.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_planejamento(id):
    planejamento = PlanejamentoEstrategico.query.get(id)
    if request.method == 'POST':
        planejamento.nome = request.form['nome']
        db.session.commit()
        flash('Planejamento atualizado com sucesso!', 'success')
        return redirect(url_for('planejamento.cadastro_planejamentope'))

    return render_template('editar_planejamento.html', planejamento=planejamento)
#############################################################################
@planejamento_route.route('/cadastro_planejamentope', methods=['GET', 'POST'])
@coordenador_required
def cadastro_planejamentope():
    if request.method == 'POST':
        # Processar o formulário de cadastro de planejamento
        nome = request.form['nome']
        pdi_id = request.form['planejamento_id']

        # Lógica para criar um novo planejamento estratégico
        novo_planejamento = PlanejamentoEstrategico(
            nome=nome,
            pdi_id=pdi_id,
            id_programa=current_user.programa_id  # Utilizando o programa_id do usuário atual
        )
        db.session.add(novo_planejamento)
        db.session.commit()

        flash('Planejamento cadastrado com sucesso!', 'success')
        return redirect(url_for('planejamento.cadastro_planejamentope'))
    else:
        # Se o método for GET, renderize o formulário de cadastro
        pdis = PDI.query.all()
        
        # Verifique se o usuário está autenticado e tem um programa associado
        if current_user and hasattr(current_user, 'programa_id') and current_user.programa_id:
            programa_do_usuario = Programa.query.get(current_user.programa_id)
        else:
            flash('Nenhum programa associado encontrado para este usuário.', 'danger')
            return redirect(url_for('login.login_page'))

        # Obter todos os planejamentos cadastrados
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=current_user.programa_id).all()

        return render_template('planejamento.html', pdis=pdis, programa_do_usuario=programa_do_usuario, planejamentos=planejamentos)

#################################################################################################################################
@planejamento_route.route('/associar_objetivospe', methods=['GET', 'POST'])
@coordenador_required
def associar_objetivospe():
    if 'email' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login_page'))

    if not current_user.is_authenticated or current_user.role != 'Coordenador':
        return 'Acesso não autorizado'
    
    if 'programa_id' not in session:
        flash('Você precisa estar associado a um programa para acessar esta página.', 'danger')
        return redirect(url_for('get_coordenador'))

    programa_id = session['programa_id']

    if request.method == 'POST':
        nome = request.form['nome']
        objetivo_pdi_id = request.form['objetivo_id']
        planejamento_estrategico_id = request.form['planejamento_id']

        if planejamento_estrategico_id != programa_id:
            return 'Acesso não autorizado'

        novo_objetivo = ObjetivoPE(
            nome=nome, 
            objetivo_pdi_id=objetivo_pdi_id, 
            planejamento_estrategico_id=planejamento_estrategico_id
        )
        
        db.session.add(novo_objetivo)
        db.session.commit()

        flash('Objetivo cadastrado com sucesso!', 'success')
        return redirect(url_for('planejamento.associar_objetivospe'))

    planejamento_estrategico = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
    objetivos_por_planejamento = []

    for pe in planejamento_estrategico:
        objetivos = Objetivo.query.filter_by(pdi_id=pe.pdi_id).all()
        for objetivo in objetivos:
            objetivos_pe = ObjetivoPE.query.filter_by(objetivo_pdi_id=objetivo.id).all()
            for objetivo_pe in objetivos_pe:
                objetivos_por_planejamento.append((pe, objetivo, objetivo_pe))

    return render_template('objetivope.html', objetivos_por_planejamento=objetivos_por_planejamento)


################################################################333    
@planejamento_route.route('/editar_objetivope/<int:id>', methods=['GET', 'POST'])
def editar_objetivope(id):
    objetivo = ObjetivoPE.query.get_or_404(id)

    if request.method == 'POST':
        objetivo.nome = request.form['nome']
        objetivo.planejamento_estrategico_id = request.form['planejamento_id']
        objetivo.objetivo_pdi_id = request.form['objetivo_id']

        db.session.commit()

        flash('Objetivo atualizado com sucesso!', 'success')
        return redirect(url_for('planejamento.editar_objetivope', id=id))

    planejamento_estrategico = PlanejamentoEstrategico.query.all()
    objetivos_pdi = Objetivo.query.all()

    return render_template('editar_objetivope.html', objetivo=objetivo, planejamento_estrategico=planejamento_estrategico, objetivos_pdi=objetivos_pdi)

########################################################################

####################################################################################################################
@planejamento_route.route('/associar_acaope', methods=['GET', 'POST'])
@coordenador_required
def associar_acaope():
    programa_id = current_user.programa_id
    if programa_id:
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
        metas_pe_associadas = []
        acoes = []

        for planejamento in planejamentos:
            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
            for objetivo in objetivos:
                metas_pe = MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all()
                metas_pe_associadas.extend(metas_pe)
                for meta in metas_pe:
                    acoes.extend(AcaoPE.query.filter_by(meta_pe_id=meta.id).all())

        if request.method == 'POST':
            meta_pe_id = request.form['meta_pe_id']
            nome = request.form['nome']
            porcentagem_execucao = request.form['porcentagem_execucao']
            data_inicio = request.form['data_inicio']
            data_termino = request.form['data_termino']
            responsavel = request.form['responsavel']
            status = request.form['status']
            observacao = request.form['observacao']

            meta_pe = MetaPE.query.get(meta_pe_id)
            if meta_pe is None:
                flash('Meta não encontrada!', 'error')
                return redirect(url_for('planejamento.associar_acaope'))

            nova_acao = AcaoPE(
                nome=nome, 
                meta_pe_id=meta_pe_id, 
                porcentagem_execucao=porcentagem_execucao, 
                data_inicio=data_inicio, 
                data_termino=data_termino,
                responsavel=responsavel, 
                status=status, 
                observacao=observacao
            )
            db.session.add(nova_acao)
            db.session.commit()

            flash('Ação cadastrada com sucesso!', 'success')
            return redirect(url_for('planejamento.associar_acaope'))

        return render_template('acaope.html', metas_pe=metas_pe_associadas, acoes=acoes)
    else:
        flash('Programa não encontrado!', 'error')
        return redirect(url_for('login.get_coordenador'))
########################################## Alterar ação #####################################################
@planejamento_route.route('/alterar_acaope/<int:acao_id>', methods=['GET', 'POST'])
@login_required
def alterar_acaope(acao_id):
    acao = AcaoPE.query.get_or_404(acao_id)

    if request.method == 'POST':
        acao.data_termino = request.form['data_termino']
        acao.responsavel = request.form['responsavel']
        acao.status = request.form['status']
        acao.observacao = request.form['observacao']
        acao.porcentagem_execucao = request.form['porcentagem_execucao']

        db.session.commit()
        flash('Ação alterada com sucesso!', 'success')
        return redirect(url_for('planejamento.alterar_acaope', acao_id=acao.id))

    return render_template('alterar_acaope.html', acao=acao)
################################################################################################
################################################# Pro -reitor ###################################
@planejamento_route.route('/visualizar_programaspe', methods=['GET', 'POST'])
def visualizar_programaspe():
    if request.method == 'POST':
        programa_id = request.form['programa']
        programa = Programa.query.get(programa_id)
        
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
        
        return render_template('visualizar_programas.html', programas=Programa.query.all(), planejamentos=planejamentos, programa_selecionado=programa)
    
    return render_template('visualizar_programas.html', programas=Programa.query.all(), planejamentos=None, programa_selecionado=None)
#####################################################################################################################
@planejamento_route.route('/visualizar_dados_programa', methods=['POST'])
def visualizar_dados_programa():
    planejamento_id = request.form['planejamento']
    planejamento = PlanejamentoEstrategico.query.get(planejamento_id)
    
    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    
    valores_metas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()
    
    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    
    return render_template('dados_programa.html', planejamento=planejamento, objetivos=objetivospe, metas=metaspe, indicadores=indicadores, acoes=acoes, valores_metas=valores_metas)
###################################################################################################################################
###########################################################################################################################
@planejamento_route.route('/associar_indicadorespe', methods=['GET', 'POST'])
@login_required
def associar_indicadorespe():
    programa_id = current_user.programa_id
    if programa_id:
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
        metas_pe_associadas = []

        for planejamento in planejamentos:
            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
            for objetivo in objetivos:
                metas_pe = MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all()
                metas_pe_associadas.extend(metas_pe)

        if request.method == 'POST':
            meta_pe_id = request.form['meta_pe_id']
            nome_indicador = request.form['nome']
            descricao = request.form['descricao']
            frequencia_coleta = request.form['frequencia_coleta']
            peso = request.form['peso']
            valor_meta = request.form['valor_meta']

            meta_pe = MetaPE.query.get(meta_pe_id)
            if meta_pe is None:
                flash('Meta não encontrada!', 'error')
                return redirect(url_for('planejamento.associar_indicadorespe'))

            indicador_existente = IndicadorPlan.query.filter_by(nome=nome_indicador, meta_pe_id=meta_pe_id).first()

            if indicador_existente:
                indicador_id = indicador_existente.id
            else:
                novo_indicador = IndicadorPlan(
                    nome=nome_indicador,
                    meta_pe_id=meta_pe_id,
                    descricao=descricao,
                    frequencia_coleta=frequencia_coleta,
                    peso=peso,
                    valor_meta=valor_meta
                )
                db.session.add(novo_indicador)
                db.session.commit()
                indicador_id = novo_indicador.id

            ano = request.form.getlist('ano[]')
            semestre = request.form.getlist('semestre[]')
            valor = request.form.getlist('valor[]')

            for ano, semestre, valor in zip(ano, semestre, valor):
                novo_valor = Valorindicador(indicadorpe_id=indicador_id, ano=ano, semestre=semestre, valor=valor)
                db.session.add(novo_valor)

            db.session.commit()
            flash('Indicador cadastrado com sucesso!', 'success')
            return redirect(url_for('planejamento.associar_indicadorespe'))

        indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas_pe_associadas])).all()
        return render_template('indicadorpe.html', metas_pe=metas_pe_associadas, indicadores=indicadores)
    
    else:
        flash('Programa não encontrado!', 'error')
        return redirect(url_for('get_coordenador'))

#########################################################################################################3
@planejamento_route.route('/alterar_indicadorpe/<int:indicador_id>', methods=['GET', 'POST'])
@login_required
def alterar_indicadorpe(indicador_id):
    indicador = IndicadorPlan.query.get_or_404(indicador_id)
    valores_indicadores = Valorindicador.query.filter_by(indicadorpe_id=indicador.id).all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        frequencia_coleta = request.form.get('frequencia_coleta')
        peso = request.form.get('peso')
        valor_meta = request.form.get('valor_meta')
        semestres = request.form.getlist('semestres[]')
        anos = request.form.getlist('anos[]')
        valores = request.form.getlist('valores[]')

        if nome:
            indicador.nome = nome
        if descricao:
            indicador.descricao = descricao
        if frequencia_coleta:
            indicador.frequencia_coleta = frequencia_coleta
        if peso:
            indicador.peso = peso
        if valor_meta:
            indicador.valor_meta = valor_meta

        for i, valorindicador in enumerate(valores_indicadores):
            valorindicador.semestre = semestres[i]
            valorindicador.ano = anos[i]
            valorindicador.valor = valores[i]

        db.session.commit()
        flash('Indicador e valores atualizados com sucesso.', 'success')
        return redirect(url_for('planejamento.alterar_indicadorpe', indicador_id=indicador.id))

    return render_template('alterar_indicadorpe.html', indicador=indicador, valores_indicadores=valores_indicadores)
##############################################################################################################################
@planejamento_route.route('/associar_metaspe', methods=['GET', 'POST'])
@login_required
def associar_metaspe():
    programa_id = current_user.programa_id
    if programa_id:
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
        objetivos_pe_associados = []

        for planejamento in planejamentos:
            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
            objetivos_pe_associados.extend(objetivos)

        if request.method == 'POST':
            objetivo_pe_id = request.form['objetivo_pe_id']
            nome_meta = request.form['nome']
            descricao = request.form['descricao']
            responsavel = request.form['responsavel']
            recursos = request.form['recursos']
            data_inicio = request.form['data_inicio']
            data_termino = request.form['data_termino']
            status_inicial = request.form['status_inicial']
            valor_alvo = request.form['valor_alvo']

            objetivo_pe = ObjetivoPE.query.get(objetivo_pe_id)
            if objetivo_pe is None:
                flash('Objetivo não encontrado!', 'error')
                return redirect(url_for('planejamento.associar_metaspe'))

            # Verifica se a meta já existe na tabela MetaPE
            meta_existente = MetaPE.query.filter_by(nome=nome_meta, objetivo_pe_id=objetivo_pe_id).first()
            meta_id = None  # Inicializa a variável meta_id

            if meta_existente:
                meta_id = meta_existente.id
            else:
                nova_meta = MetaPE(
                    objetivo_pe_id=objetivo_pe_id, 
                    nome=nome_meta,
                    descricao=descricao,
                    responsavel=responsavel,
                    recursos_necessarios=recursos,
                    data_inicio=data_inicio,
                    data_termino=data_termino,
                    status_inicial=status_inicial,
                    valor_alvo=valor_alvo
                )
                db.session.add(nova_meta)
                db.session.commit()
                meta_id = nova_meta.id
                print(f"Nova Meta criada com ID: {meta_id}")

            # Verifique se a meta foi criada com sucesso
            if not meta_id:
                flash('Erro ao criar a meta!', 'error')
                return redirect(url_for('planejamento.associar_metaspe'))

            # Adiciona uma verificação para garantir que o meta_id é válido
            meta = MetaPE.query.get(meta_id)
            if not meta:
                flash('Erro: Meta não encontrada após criação!', 'error')
                return redirect(url_for('planejamento.associar_metaspe'))

            # Se a meta foi criada com sucesso, cadastrar os valores da meta
            try:
                anos = request.form.getlist('ano[]')
                semestres = request.form.getlist('semestre[]')
                valores = request.form.getlist('valor[]')

                for ano, semestre, valor in zip(anos, semestres, valores):
                    valor = valor.replace(',', '.')  # Substituir vírgula por ponto
                    novo_valor = Valormeta(metape_id=meta_id, ano=int(ano), semestre=int(semestre), valor=float(valor))
                    db.session.add(novo_valor)

                db.session.commit()
                flash('Meta e valores cadastrados com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar valores da meta: {str(e)}', 'error')
            
            return redirect(url_for('planejamento.associar_metaspe'))

        # Obter todas as metas cadastradas para exibição
        metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos_pe_associados])).all()
        return render_template('metaspe.html', objetivos_pe=objetivos_pe_associados, metas=metas)

    else:
        flash('Programa não encontrado!', 'error')
        return redirect(url_for('planejamento.associar_metaspe'))
#################################################################################################


#######################################################################################################################    
@planejamento_route.route('/get_objetivosplano/<int:planejamento_id>')
def get_objetivos(planejamento_id):
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    print(objetivos)
    options = [{'id': objetivo.id, 'nome': objetivo.nome} for objetivo in objetivos]
    return jsonify(options)
    
    
##############################################################################################################################
@planejamento_route.route('/alterar_metape/<int:metape_id>', methods=['GET', 'POST'])
def alterar_metape(metape_id):
    # Busca a meta PE a ser alterada pelo ID
    meta_pe = MetaPE.query.get_or_404(metape_id)
    mensagem = None  # Inicializa a mensagem como None

    if request.method == 'POST':
        # Atualiza os campos da meta PE com os dados do formulário, se fornecidos
        if 'nome' in request.form:
            meta_pe.nome = request.form['nome']
        if 'descricao' in request.form:
            meta_pe.descricao = request.form['descricao']
        if 'responsavel' in request.form:
            meta_pe.responsavel = request.form['responsavel']
        if 'recursos' in request.form:
            meta_pe.recursos_necessarios = request.form['recursos']
        if 'data_inicio' in request.form:
            meta_pe.data_inicio = request.form['data_inicio']
        if 'data_termino' in request.form:
            meta_pe.data_termino = request.form['data_termino']
        if 'status_inicial' in request.form:
            meta_pe.status_inicial = request.form['status_inicial']
        if 'valor_alvo' in request.form:
            meta_pe.valor_alvo = request.form['valor_alvo']
                
        # Salva as alterações no banco de dados
        db.session.commit()

        flash('Meta alterada com sucesso!', 'success')
        return redirect(url_for('planejamento.associar_metaspe'))  # Redireciona para a página de metas

    # Passa a variável 'meta' para o template
    return render_template('alterarmetas.html', meta=meta_pe, mensagem=mensagem)
#############################################################################
#################################################################################
@planejamento_route.route('/sucesso', methods=['GET'])
def sucesso():
    mensagem = "Meta alterada com sucesso!"
    return render_template('sucesso.html', mensagem=mensagem)

############################################################################################
@planejamento_route.route('/export_programa/excel/<int:programa_id>')
@login_required
def export_programa_excel(programa_id):
    planejamentope = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.planejamento_estrategico_id.in_([pe.id for pe in planejamentope])).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    valores_metas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()
    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    
    data = []
    for objetivo in objetivospe:
        for meta in metaspe:
            if meta.objetivo_pe_id == objetivo.id:
                valor_meta = next((v.valor for v in valores_metas if v.metape_id == meta.id), 'N/A')
                meta_indicadores = [indicador.nome for indicador in indicadores if indicador.meta_pe_id == meta.id]
                if meta_indicadores:
                    for indicador_nome in meta_indicadores:
                        for acao in acoes:
                            if acao.meta_pe_id == meta.id:
                                data.append({
                                    'Objetivo': objetivo.nome,
                                    'Meta': meta.nome,
                                    'Valor da Meta': f"{valor_meta}%",
                                    'Indicador': indicador_nome,
                                    'Ação': acao.nome,
                                    'Status da Ação': acao.status
                                })
                else:
                    data.append({
                        'Objetivo': objetivo.nome,
                        'Meta': meta.nome,
                        'Valor da Meta': f"{valor_meta}%",
                        'Indicador': '-',
                        'Ação': '-',
                        'Status da Ação': '-'
                    })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Planejamento Estratégico')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name='planejamento_estrategico.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@planejamento_route.route('/export_programa/pdf/<int:programa_id>')
@login_required
def export_programa_pdf(programa_id):
    planejamentope = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
    objetivospe = ObjetivoPE.query.filter(ObjetivoPE.planejamento_estrategico_id.in_([pe.id for pe in planejamentope])).all()
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    valores_metas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()
    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()

    # Debug: Verificar se os dados estão sendo recuperados corretamente
    print(f"Planejamento Estratégico: {planejamentope}")
    print(f"Objetivos: {objetivospe}")
    print(f"Metas: {metaspe}")
    print(f"Indicadores: {indicadores}")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleN.alignment = 4  # Justify

    elements = []
    elements.append(Paragraph("Planejamento Estratégico", styles['Title']))

    data = [['Objetivo', 'Meta', 'Valor da Meta', 'Indicador', 'Ação', 'Status da Ação']]
    
    for objetivo in objetivospe:
        for meta in metaspe:
            if meta.objetivo_pe_id == objetivo.id:
                valor_meta = next((v.valor for v in valores_metas if v.metape_id == meta.id), 'N/A')
                meta_indicadores = [indicador.nome for indicador in indicadores if indicador.meta_pe_id == meta.id]
                if meta_indicadores:
                    for indicador_nome in meta_indicadores:
                        for acao in acoes:
                            if acao.meta_pe_id == meta.id:
                                data.append([
                                    Paragraph(objetivo.nome, styleN),
                                    Paragraph(meta.nome, styleN),
                                    Paragraph(f"{valor_meta}%", styleN),
                                    Paragraph(indicador_nome, styleN),
                                    Paragraph(acao.nome, styleN),
                                    Paragraph(acao.status, styleN)
                                ])
                else:
                    data.append([
                        Paragraph(objetivo.nome, styleN),
                        Paragraph(meta.nome, styleN),
                        Paragraph(f"{valor_meta}%", styleN),
                        Paragraph('-', styleN),
                        Paragraph('-', styleN),
                        Paragraph('-', styleN)
                    ])

    # Debug: Print the data to check if it is being captured correctly
    print(f"Data to be included in PDF: {data}")

    table = Table(data, colWidths=[100, 100, 100, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='planejamento_estrategico.pdf', mimetype='application/pdf')

######################################################################################################################
@planejamento_route.route('/associar_cadeiavalor', methods=['GET', 'POST'])
def associar_cadeiavalor():
    if request.method == 'POST':
        macroprocessogerencial = request.form['macroprocessogerencial']
        macroprocessofinalistico = request.form['macroprocessofinalistico']
        valorpublico = request.form['valorpublico']
        macroprocessosuporte = request.form['macroprocessosuporte']
        planejamento_estrategico_id = request.form['planejamento_id']

        if not macroprocessogerencial or not macroprocessofinalistico or not valorpublico or not macroprocessosuporte or not planejamento_estrategico_id:
            flash('All fields are required!')
            return redirect(url_for('planejamento.associar_cadeiavalor'))

        nova_cadeia_valor = CadeiaValor(
            macroprocessogerencial=macroprocessogerencial,
            macroprocessofinalistico=macroprocessofinalistico,
            valorpublico=valorpublico,
            macroprocessosuporte=macroprocessosuporte,
            planejamento_estrategico_id=planejamento_estrategico_id
        )

        db.session.add(nova_cadeia_valor)
        db.session.commit()
        flash('Cadeia de Valor cadastrada com sucesso!', 'success')
        return redirect(url_for('planejamento.associar_cadeiavalor'))

    else:
        programa_id = current_user.programa_id
        planejamento_estrategico = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()

        if programa_id:
            programa = Programa.query.get(programa_id)
            planejamentos = programa.planejamentos
        else:
            planejamentos = []

        return render_template('cadeia_valor.html', planejamentos=planejamentos)
    
###########################################################################################################3
