from flask import Blueprint, render_template, redirect, url_for, request, flash, session,jsonify,send_file
from .models import Users, Programa, PlanejamentoEstrategico, PDI,ObjetivoPE,Objetivo,MetaPE,AcaoPE,IndicadorPlan,Valorindicador,Valormeta # Certifique-se de importar seus modelos corretamente
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

        return render_template('planejamento.html', pdis=pdis, programa_do_usuario=programa_do_usuario)


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
        # Redireciona para a mesma página para exibir a mensagem
        return redirect(url_for('associar_objetivospe'))

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
#######################################################################################################################
@planejamento_route.route('/associar_acaope', methods=['GET', 'POST'])
@coordenador_required
def associar_acaope():
    if request.method == 'POST':
        meta_pe_id = request.form['meta_pe_id']
        nome = request.form['nome']
        porcentagem_execucao = request.form['porcentagem_execucao']
        data_inicio = request.form['data_inicio']
        data_termino = request.form['data_termino']
        responsavel = request.form['responsavel']
        status = request.form['status']
        observacao = request.form['observacao']

        # Verifica se a meta existe
        meta_pe = MetaPE.query.get(meta_pe_id)
        if meta_pe is None:
            flash('Meta não encontrada!', 'error')
            return redirect(url_for('associar_acaope'))

        # Cria uma nova ação associada à meta
        nova_acao = AcaoPE(nome=nome, meta_pe_id=meta_pe_id, porcentagem_execucao=porcentagem_execucao, data_inicio=data_inicio, data_termino=data_termino,
                           responsavel=responsavel, status=status, observacao=observacao)
        db.session.add(nova_acao)
        db.session.commit()

        flash('Ação cadastrada com sucesso!', 'success')
        return redirect(url_for('associar_acaope'))

    else:
        programa_id = current_user.programa_id
        if programa_id:
            planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
            metas_pe_associadas = []
            for planejamento in planejamentos:
                objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
                for objetivo in objetivos:
                    metas_pe = MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all()
                    metas_pe_associadas.extend(metas_pe)
            return render_template('acaope.html', metas_pe=metas_pe_associadas)
        else:
            flash('Programa não encontrado!', 'error')
            return redirect(url_for('login.get_coordenador'))
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
        if 'porcentagem_execucao' in request.form:
            acao.porcentagem_execucao = request.form['porcentagem_execucao']
        
        # Salva as alterações no banco de dados
        db.session.commit()

        flash('Ação alterada com sucesso!', 'success')
        # Redireciona de volta para a página de alteração de ação para permanecer na mesma tela
        return redirect(url_for('planejamento.alterar_acaope', acao_id=acao_id))
    else:
        # Retorna o formulário de alteração preenchido com os dados da ação
        return render_template('alterar_acaope.html', acao=acao)
################################################################################################
################################################# Pro -reitor ###################################
@planejamento_route.route('/visualizar_programaspe', methods=['GET', 'POST'])
def visualizar_programaspe():
    if request.method == 'POST':
        programa_id = request.form['programa']
        programa = Programa.query.get(programa_id)
        print(f"Programa selecionado: {programa}")
        
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
        print(f"Planejamentos Estratégicos: {planejamentos}")
        
        return render_template('visualizar_programas.html', programas=Programa.query.all(), planejamentos=planejamentos, programa_selecionado=programa)
    
    return render_template('visualizar_programas.html', programas=Programa.query.all(), planejamentos=None, programa_selecionado=None)


@planejamento_route.route('/visualizar_dados_programa', methods=['POST'])
def visualizar_dados_programa():
    planejamento_id = request.form['planejamento']
    planejamento = PlanejamentoEstrategico.query.get(planejamento_id)
    print(f"Planejamento selecionado: {planejamento}")
    
    objetivospe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    print(f"Objetivos: {objetivospe}")
    
    metaspe = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([objetivo.id for objetivo in objetivospe])).all()
    print(f"Metas: {metaspe}")
    
    indicadores = IndicadorPlan.query.filter(IndicadorPlan.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    print(f"Indicadores: {indicadores}")
    
    valores_metas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metaspe])).all()
    print(f"Valores das Metas: {valores_metas}")
    
    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metaspe])).all()
    print(f"Ações: {acoes}")
    
    return render_template('dados_programa.html', planejamento=planejamento, objetivos=objetivospe, metas=metaspe, indicadores=indicadores, acoes=acoes, valores_metas=valores_metas)
###################################################################################################################################
###########################################################################################################################
@planejamento_route.route('/associar_indicadorespe', methods=['GET', 'POST'])
def associar_indicadorespe():
    # Se o programa existir, obtenha os planejamentos estratégicos associados a ele
    programa_id = current_user.programa_id
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

        # Se a requisição for POST, processar o formulário
        if request.method == 'POST':
            # Obtenha os dados do formulário
            meta_pe_id = request.form['meta_pe_id']
            nome_indicador = request.form['nome']
            descricao = request.form['descricao']  # Adicionado para obter a descrição do indicador 

            # Verifica se a meta PE existe e se está associada a um objetivo do programa do Coordenador
            meta_pe = MetaPE.query.get(meta_pe_id)
            if meta_pe is None:
                flash('Meta não encontrada!', 'error')
                return redirect(url_for('get_coordenador'))

            # Verifica se o indicador já existe na tabela IndicadorPE
            indicador_existente = IndicadorPlan.query.filter_by(nome=nome_indicador, meta_pe_id=meta_pe_id).first()

            # Se o indicador já existir, obtenha o ID
            if indicador_existente:
                indicador_id = indicador_existente.id
            else:
                # Se o indicador não existir, adicione-o à tabela IndicadorPE
                novo_indicador = IndicadorPlan(nome=nome_indicador, meta_pe_id=meta_pe_id, descricao=descricao)  # Adicionado descricao
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
        
        # Se a requisição for GET, renderize o template com as metas
        return render_template('indicadorpe.html', metas_pe=metas_pe_associadas)
    
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
        semestres = request.form.getlist('semestres[]')
        anos = request.form.getlist('anos[]')
        valores = request.form.getlist('valores[]')

        # Atualiza o nome do indicador
        if nome:
            indicador.nome = nome

        # Atualiza os valores dos indicadores
        for i, valorindicador in enumerate(valores_indicadores):
            valorindicador.semestre = semestres[i]
            valorindicador.ano = anos[i]
            valorindicador.valor = valores[i]

        # Salva as alterações no banco de dados
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
            objetivo_pe = ObjetivoPE.query.get(objetivo_pe_id)
            if objetivo_pe is None:
                flash('Objetivo não encontrado!', 'error')
                return redirect(url_for('associar_metaspe'))

            # Verifica se a meta já existe na tabela MetaPE
            meta_existente = MetaPE.query.filter_by(nome=nome_meta, objetivo_pe_id=objetivo_pe_id).first()
            meta_id = None  # Inicializa a variável meta_id

            if meta_existente:
                meta_id = meta_existente.id
            else:
                nova_meta = MetaPE(objetivo_pe_id=objetivo_pe_id, nome=nome_meta)
                db.session.add(nova_meta)
                db.session.commit()
                meta_id = nova_meta.id
                print(f"Nova Meta criada com ID: {meta_id}")

            # Verifique se a meta foi criada com sucesso
            if not meta_id:
                flash('Erro ao criar a meta!', 'error')
                return redirect(url_for('associar_metaspe'))

            # Adiciona uma verificação para garantir que o meta_id é válido
            meta = MetaPE.query.get(meta_id)
            if not meta:
                flash('Erro: Meta não encontrada após criação!', 'error')
                return redirect(url_for('associar_metaspe'))

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
            
            return redirect(url_for('associar_metaspe'))

        return render_template('metaspe.html', objetivos_pe=objetivos_pe_associados)

    else:
        flash('Programa não encontrado!', 'error')
        return redirect(url_for('associar_metaspe'))
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
                
        # Salva as alterações no banco de dados
        db.session.commit()

        flash('Meta alterada com sucesso!', 'success')
        return redirect(url_for('sucesso'))  # Redireciona para a página de sucesso

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