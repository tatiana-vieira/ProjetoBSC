from flask import Blueprint, render_template, redirect, url_for, request, flash, session,jsonify,send_file,make_response
from .models import Users, Programa,CadeiaValor, PlanejamentoEstrategico,AcaoPE,Risco,HistoricoIndicador, PDI,Objetivo,ObjetivoPE,MetaPE,IndicadorPlan,Valorindicador,Valormeta # Certifique-se de importar seus modelos corretamente
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
from datetime import datetime
from flask import get_flashed_messages
import base64
import logging
from reportlab.pdfgen import canvas
from io import BytesIO
from fpdf import FPDF
import tempfile
import matplotlib.pyplot as plt
import nltk


# Configurar logging
logging.basicConfig(level=logging.INFO)
# Certifique-se de que AcaoPE está importado corretamente


planejamento_route = Blueprint('planejamento', __name__)
login_manager = LoginManager(planejamento_route)

# Implemente o decorador coordenador_required

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

def coordenador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'Coordenador':
            flash('Acesso negado. Apenas coordenadores podem acessar esta página.', 'danger')
            return redirect(url_for('login.login_page'))
        return f(*args, **kwargs)
    return decorated_function

#########################################

def calcular_percentual_metas_atingidas(planejamento):
    total_metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in planejamento.objetivos])).count()
    metas_atingidas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in planejamento.objetivos]), MetaPE.status == 'Concluída').count()
    return (metas_atingidas / total_metas * 100) if total_metas > 0 else 0

def calcular_percentual_acoes_concluidas(planejamento):
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in planejamento.objetivos])).all()
    total_acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).count()
    acoes_concluidas = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas]), AcaoPE.status == 'Concluída').count()
    return (acoes_concluidas / total_acoes * 100) if total_acoes > 0 else 0

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
    
    planejamento_estrategico = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
    planejamento_selecionado = None
    objetivos_pdi = []
    objetivos_pe = []

    if request.method == 'POST':
        planejamento_id = request.form.get('planejamento_id')
        if planejamento_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.filter_by(id=planejamento_id).first()
            # Carregar os objetivos do PDI relacionados ao planejamento selecionado
            objetivos_pdi = Objetivo.query.filter_by(pdi_id=planejamento_selecionado.pdi_id).all()

            # Carregar os objetivos associados ao planejamento estratégico selecionado
            objetivos_pe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()

        nome = request.form.get('nome')
        objetivo_pdi_id = request.form.get('objetivo_id')

        if nome and objetivo_pdi_id and planejamento_id:
            novo_objetivo = ObjetivoPE(
                nome=nome, 
                objetivo_pdi_id=objetivo_pdi_id, 
                planejamento_estrategico_id=planejamento_id
            )

            try:
                db.session.add(novo_objetivo)
                db.session.commit()
                flash('Objetivo cadastrado com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()  # Reverter o commit em caso de erro
                flash(f'Erro ao cadastrar objetivo: {str(e)}', 'danger')

            return redirect(url_for('planejamento.associar_objetivospe'))

    elif request.method == 'GET':
        # Carregar objetivos associados ao planejamento mesmo em uma requisição GET
        if 'planejamento_id' in request.args:
            planejamento_id = request.args.get('planejamento_id')
            if planejamento_id:
                planejamento_selecionado = PlanejamentoEstrategico.query.filter_by(id=planejamento_id).first()
                # Carregar os objetivos do PDI relacionados ao planejamento selecionado
                objetivos_pdi = Objetivo.query.filter_by(pdi_id=planejamento_selecionado.pdi_id).all()

                # Carregar os objetivos associados ao planejamento estratégico selecionado
                objetivos_pe = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()

    return render_template('objetivope.html', 
                           planejamento_estrategico=planejamento_estrategico,
                           planejamento_selecionado=planejamento_selecionado,
                           objetivos_pdi=objetivos_pdi,
                           objetivos_pe=objetivos_pe)



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
        return redirect(url_for('planejamento.associar_objetivospe'))

    # Lista de todos os planejamentos estratégicos
    planejamento_estrategico = PlanejamentoEstrategico.query.all()
    # Lista de todos os objetivos PDI
    objetivos_pdi = Objetivo.query.all()

    return render_template(
        'editar_objetivope.html', 
        objetivo=objetivo, 
        planejamento_estrategico=planejamento_estrategico, 
        objetivos_pdi=objetivos_pdi
    )
########################################################################
def calcular_previsao(meta, porcentagem_execucao, data_inicio, data_termino):
    # Lógica para calcular a previsão de impacto
    previsao = (porcentagem_execucao / 100) * (data_termino - data_inicio).days
    return previsao
####################################################################################################################
@planejamento_route.route('/associar_acaope', methods=['GET', 'POST'])
@coordenador_required
def associar_acaope():
    programa_id = current_user.programa_id
    if not programa_id:
        flash('Programa não encontrado!', 'error')
        return redirect(url_for('login.get_coordenador'))

    planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
    metas_pe_associadas = []
    acoes = []

    # Carregar todas as metas e ações associadas ao planejamento
    for planejamento in planejamentos:
        objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
        for objetivo in objetivos:
            metas_pe = MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all()
            metas_pe_associadas.extend(metas_pe)
            for meta in metas_pe:
                acoes.extend(AcaoPE.query.filter_by(meta_pe_id=meta.id).all())

    if request.method == 'POST':
        # Debug: Exibir todos os dados recebidos do formulário
        print("Dados do formulário recebidos:", request.form)

        # Capturar os dados do formulário
        meta_pe_id = int(request.form.get('meta_pe_id')) if request.form.get('meta_pe_id') else None
        nome = request.form.get('nome')
        porcentagem_execucao = request.form.get('porcentagem_execucao')
        data_inicio = request.form.get('data_inicio')
        data_termino = request.form.get('data_termino')
        responsavel = request.form.get('responsavel')
        status = request.form.get('status')
        observacao = request.form.get('observacao')

        # Debug: Exibir os valores capturados
        print("Dados capturados:", meta_pe_id, nome, porcentagem_execucao, data_inicio, data_termino, responsavel, status, observacao)

        # Verificar se a meta foi encontrada
        meta_pe = MetaPE.query.get(meta_pe_id)
        if not meta_pe:
            flash('Meta não encontrada!', 'error')
            return redirect(url_for('planejamento.associar_acaope'))

        try:
            # Criar uma nova ação
            nova_acao = AcaoPE(
                nome=nome,
                meta_pe_id=meta_pe_id,
                porcentagem_execucao=int(porcentagem_execucao),
                data_inicio=datetime.strptime(data_inicio, '%Y-%m-%d'),
                data_termino=datetime.strptime(data_termino, '%Y-%m-%d'),
                responsavel=responsavel,
                status=status,
                observacao=observacao
            )

            # Adicionar a nova ação ao banco de dados
            db.session.add(nova_acao)
            db.session.commit()

            # Função para calcular a previsão de impacto (se aplicável)
            previsao = calcular_previsao(
                meta_pe,
                int(porcentagem_execucao),
                datetime.strptime(data_inicio, '%Y-%m-%d'),
                datetime.strptime(data_termino, '%Y-%m-%d')
            )

            # Exibir uma mensagem de sucesso com a previsão de impacto
            flash(f'Ação cadastrada com sucesso! {previsao}', 'success')

        except Exception as e:
            db.session.rollback()
            print("Erro ao cadastrar a ação:", str(e))
            flash('Erro ao cadastrar a ação!', 'error')

        return redirect(url_for('planejamento.associar_acaope'))

    # Renderizar o template com os dados necessários
    return render_template('acaope.html', metas_pe=metas_pe_associadas, acoes=acoes)


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
    
    return render_template(
        'dados_programa.html',
        planejamento=planejamento,
        objetivos=objetivospe,
        metas=metaspe,
        indicadores=indicadores,
        acoes=acoes,
        valores_metas=valores_metas
    )


###################################################################################################################################
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
            # Dados do formulário
            meta_pe_id = request.form['meta_pe_id']
            nome_indicador = request.form['nome']
            descricao = request.form['descricao']
            frequencia_coleta = request.form['frequencia_coleta']
            peso = request.form['peso']
            responsavel = request.form['responsavel']
            data_inicio = request.form['data_inicio']
            data_fim = request.form['data_fim']

            # Verificar se a meta existe
            meta_pe = MetaPE.query.get(meta_pe_id)
            if not meta_pe:
                flash('Meta não encontrada!', 'error')
                return redirect(url_for('planejamento.associar_indicadorespe'))

            # Valor meta para calcular progresso
            valor_meta = meta_pe.valor_alvo  # Assumindo que `valor_alvo` é o campo de meta na tabela MetaPE

            # Criar ou obter o indicador existente
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
                    responsavel=responsavel,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                )
                db.session.add(novo_indicador)
                db.session.commit()
                indicador_id = novo_indicador.id

                # Registro inicial no histórico
                progresso_inicial = HistoricoIndicador(
                    indicador_pe_id=indicador_id,
                    data=datetime.now().date(),
                    valor_progresso=0.0  # Progresso inicial
                )
                db.session.add(progresso_inicial)
                db.session.commit()

            # Processar valores do indicador
            semestres = request.form.getlist('semestres[]')
            anos = request.form.getlist('anos[]')
            valores = request.form.getlist('valor[]')

            for semestre, ano, valor in zip(semestres, anos, valores):
                if semestre and ano and valor:  # Certificar que os campos estão preenchidos
                    try:
                        semestre = int(semestre)
                        ano = int(ano)
                        valor_realizado = float(valor)

                        # Cálculo do progresso percentual
                        progresso_percentual = (valor_realizado / valor_meta) * 100 if valor_meta > 0 else 0
                        
                        # Criação do novo valor para o indicador
                        novo_valor = Valorindicador(
                            indicadorpe_id=indicador_id,
                            semestre=semestre,
                            ano=ano,
                            valor=valor_realizado,
                            progresso=progresso_percentual  # Armazenar o progresso
                        )
                        db.session.add(novo_valor)
                    except ValueError:
                        flash('Por favor, insira valores válidos para semestre, ano e valor.', 'error')
                        return redirect(url_for('planejamento.associar_indicadorespe'))

            db.session.commit()
            flash('Indicador cadastrado com sucesso!', 'success')
            return redirect(url_for('planejamento.associar_indicadorespe'))

        # Exibir os indicadores associados
        indicadores = IndicadorPlan.query.filter(
            IndicadorPlan.meta_pe_id.in_([meta.id for meta in metas_pe_associadas])
        ).all()
        return render_template('indicadorpe.html', metas_pe=metas_pe_associadas, indicadores=indicadores)

    else:
        flash('Programa não encontrado!', 'error')
        return redirect(url_for('get_coordenador'))


# Rota para visualizar o histórico de um indicador
@planejamento_route.route('/visualizar_historico/<int:indicador_id>')
@login_required
def visualizar_historico(indicador_id):
    indicador = IndicadorPlan.query.get_or_404(indicador_id)
    historico = HistoricoIndicador.query.filter_by(indicador_pe_id=indicador_id).order_by(HistoricoIndicador.data).all()
    return render_template('historico_indicador.html', indicador=indicador, historico=historico)

# Rota para salvar um indicador (dados de ano, semestre, e valor)
@planejamento_route.route('/salvar_indicador', methods=['POST'])
def salvar_indicador():
    anos = request.form.getlist('anos[]')
    valores = request.form.getlist('valores[]')
    semestres = request.form.getlist('semestres[]')
    indicador_id = request.form.get('indicador_id')

    for ano, valor, semestre in zip(anos, valores, semestres):
        valor = valor.replace(',', '.')
        try:
            ano = int(ano)
            valor = float(valor)
            semestre = int(semestre)
            novo_valor = Valorindicador(
                ano=ano,
                valor=valor,
                semestre=semestre,
                indicadorpe_id=indicador_id
            )
            db.session.add(novo_valor)
        except ValueError:
            flash("Erro ao converter valores. Verifique se ano, valor e semestre estão corretos.", "danger")

    try:
        db.session.commit()
        flash("Indicador salvo com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao salvar o indicador: {str(e)}", "danger")

    return redirect(url_for('planejamento.associar_indicadorespe'))

# Rota para alterar um indicador existente
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
        responsavel = request.form.get('responsavel')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        semestres = request.form.getlist('semestres[]')
        anos = request.form.getlist('anos[]')
        valores = request.form.getlist('valores[]')

        if nome and descricao and frequencia_coleta and peso and responsavel:
            indicador.nome = nome
            indicador.descricao = descricao
            indicador.frequencia_coleta = frequencia_coleta
            indicador.peso = peso
            indicador.responsavel = responsavel
            indicador.data_inicio = data_inicio
            indicador.data_fim = data_fim

            if len(valores_indicadores) == len(semestres) == len(anos) == len(valores):
                for i, valorindicador in enumerate(valores_indicadores):
                    try:
                        valorindicador.semestre = int(semestres[i])
                        valorindicador.ano = int(anos[i])
                        valorindicador.valor = float(valores[i])
                    except ValueError:
                        flash('Erro: Por favor, insira valores numéricos válidos para semestre, ano e valor.', 'error')
                        return render_template('alterar_indicadorpe.html', indicador=indicador, valores_indicadores=valores_indicadores)
            else:
                flash('Erro: Quantidade de valores, anos ou semestres está incorreta.', 'error')
                return render_template('alterar_indicadorpe.html', indicador=indicador, valores_indicadores=valores_indicadores)

            try:
                db.session.commit()
                flash('Indicador e valores atualizados com sucesso.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao salvar as alterações: {str(e)}', 'error')
                return render_template('alterar_indicadorpe.html', indicador=indicador, valores_indicadores=valores_indicadores)

            # Adiciona novo progresso ao histórico
            valor_progresso = indicador.valor_meta if indicador.valor_meta is not None else 0.0
            novo_progresso = HistoricoIndicador(
                indicador_pe_id=indicador.id,
                data=datetime.now().date(),
                valor_progresso=valor_progresso
            )
            db.session.add(novo_progresso)
            db.session.commit()

            return redirect(url_for('planejamento.associar_indicadorespe'))
        else:
            flash('Por favor, preencha todos os campos obrigatórios.', 'error')

    return render_template('alterar_indicadorpe.html', indicador=indicador, valores_indicadores=valores_indicadores)

##############################################################################################################################
@planejamento_route.route('/associar_metaspe', methods=['GET', 'POST'])
@login_required
def associar_metaspe():
    programa_id = current_user.programa_id
    if programa_id:
        # Obter planejamentos associados ao programa
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
        objetivos_pe_associados = []

        for planejamento in planejamentos:
            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
            objetivos_pe_associados.extend(objetivos)

        if request.method == 'POST':
            # Obtém os dados do formulário
            objetivo_pe_id = request.form['objetivo_pe_id']
            nome_meta = request.form['nome']
            descricao = request.form['descricao']
            responsavel = request.form['responsavel']
            recursos = request.form['recursos']
            data_inicio = request.form['data_inicio']
            data_termino = request.form['data_termino']
            status_inicial = request.form['status_inicial']
            status_texto = request.form['status']
            valor_alvo = request.form['valor_alvo']

            objetivo_pe = ObjetivoPE.query.get(objetivo_pe_id)
            if not objetivo_pe:
                flash('Objetivo não encontrado!', 'error')
                return redirect(url_for('planejamento.associar_metaspe'))

            # Verifica se a meta já existe
            meta_existente = MetaPE.query.filter_by(nome=nome_meta, objetivo_pe_id=objetivo_pe_id).first()
            if meta_existente:
                flash('Essa meta já existe para o objetivo selecionado!', 'warning')
                return redirect(url_for('planejamento.associar_metaspe'))

            try:
                # Cria a nova meta
                nova_meta = MetaPE(
                    objetivo_pe_id=objetivo_pe_id,
                    nome=nome_meta,
                    descricao=descricao,
                    responsavel=responsavel,
                    recursos_necessarios=recursos,
                    data_inicio=data_inicio,
                    data_termino=data_termino,
                    status_inicial=status_inicial,
                    status=status_texto,
                    valor_alvo=valor_alvo
                )
                db.session.add(nova_meta)
                db.session.commit()

                # Salva os valores de ano, semestre e valor na tabela Valormeta
                anos = request.form.getlist('ano[]')
                semestres = request.form.getlist('semestre[]')
                valores = request.form.getlist('valor[]')

                for ano, semestre, valor in zip(anos, semestres, valores):
                    novo_valor_meta = Valormeta(
                        metape_id=nova_meta.id,
                        ano=int(ano),
                        semestre=int(semestre),
                        valor=float(valor)
                    )
                    db.session.add(novo_valor_meta)

                db.session.commit()
                flash('Meta cadastrada com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar a meta: {str(e)}', 'error')
                return redirect(url_for('planejamento.associar_metaspe'))

            return redirect(url_for('planejamento.associar_metaspe'))

        metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos_pe_associados])).all()
        return render_template('metaspe.html', objetivos_pe=objetivos_pe_associados, metas=metas)

    else:
        flash('Programa não encontrado!', 'error')
        return redirect(url_for('planejamento.associar_metaspe'))


#########################33 calcular ####################################################
def calcular_percentual_metas_atingidas(planejamento):
    # Obter todas as metas associadas ao planejamento
    metas = MetaPE.query.filter_by(objetivo_pe_id=ObjetivoPE.id).filter(
        ObjetivoPE.planejamento_estrategico_id == planejamento.id).all()
    total_metas = len(metas)
    metas_atingidas = sum(1 for meta in metas if meta.status == 'Concluída')
    
    # Calcular o percentual
    percentual_metas = (metas_atingidas / total_metas) * 100 if total_metas > 0 else 0
    return percentual_metas

def calcular_percentual_acoes_concluidas(planejamento):
    # Obter todas as ações associadas ao planejamento
    metas = MetaPE.query.filter_by(objetivo_pe_id=ObjetivoPE.id).filter(
        ObjetivoPE.planejamento_estrategico_id == planejamento.id).all()
    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).all()
    total_acoes = len(acoes)
    acoes_concluidas = sum(1 for acao in acoes if acao.status == 'Concluída')

    # Calcular o percentual
    percentual_acoes = (acoes_concluidas / total_acoes) * 100 if total_acoes > 0 else 0
    return percentual_acoes




#################################################################################################

def sugerir_ajustes(meta, progresso, restante):
    """Sugere ajustes com base nos dados da meta e progresso."""
    sugestoes = []
    
    # Verifica se a data_termino está definida e converte corretamente
    if meta.data_termino:
        dias_restantes = (meta.data_termino - datetime.now().date()).days
    else:
        dias_restantes = None  # Define como None se a data de término não estiver definida
    
    # Verifica se o valor_alvo está definido e converte para float
    valor_alvo = float(meta.valor_alvo) if meta.valor_alvo else 0
    
    # Regras de sugestão baseadas no progresso e nos dias restantes
    if progresso < 0.5 * valor_alvo and (dias_restantes is not None and dias_restantes < 30):
        sugestoes.append(f"A meta '{meta.nome}' está com progresso lento. Considere aumentar os recursos ou estender o prazo.")
    
    if progresso > 0.8 * valor_alvo and (dias_restantes is not None and dias_restantes > 30):
        sugestoes.append(f"A meta '{meta.nome}' está no caminho certo. Continue monitorando.")
    
    if not sugestoes:
        sugestoes.append("Não há sugestões no momento.")
    
    return sugestoes
#######################################################################################################################    
@planejamento_route.route('/get_objetivosplano/<int:planejamento_id>')
def get_objetivos(planejamento_id):
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
    print(objetivos)
    options = [{'id': objetivo.id, 'nome': objetivo.nome} for objetivo in objetivos]
    return jsonify(options)
    
    
##############################################################################################################################
@planejamento_route.route('/alterar_metape/<int:metape_id>', methods=['GET', 'POST'])
@login_required
def alterar_metape(metape_id):
    meta_pe = MetaPE.query.get_or_404(metape_id)
    mensagem = None

    if request.method == 'POST':
        # Atualiza os campos com valores recebidos do formulário
        meta_pe.nome = request.form.get('nome', meta_pe.nome)
        meta_pe.descricao = request.form.get('descricao', meta_pe.descricao)
        meta_pe.responsavel = request.form.get('responsavel', meta_pe.responsavel)
        meta_pe.recursos_necessarios = request.form.get('recursos', meta_pe.recursos_necessarios)

        # Atualiza data de início e data de término com validação de formato
        data_inicio = request.form.get('data_inicio')
        if data_inicio:
            try:
                datetime.strptime(data_inicio, '%Y-%m-%d')
                meta_pe.data_inicio = data_inicio
            except ValueError:
                flash('Formato de data de início inválido. Use o formato YYYY-MM-DD.', 'danger')

        data_termino = request.form.get('data_termino')
        if data_termino:
            try:
                datetime.strptime(data_termino, '%Y-%m-%d')
                meta_pe.data_termino = data_termino
            except ValueError:
                flash('Formato de data de término inválido. Use o formato YYYY-MM-DD.', 'danger')

        # Atualiza status inicial (percentual) e status (textual)
        meta_pe.status_inicial = request.form.get('status_inicial', meta_pe.status_inicial)
        meta_pe.status = request.form.get('status', meta_pe.status)
        meta_pe.valor_alvo = request.form.get('valor_alvo', meta_pe.valor_alvo)

        # Cadastrar ou atualizar os valores da meta
        try:
            anos = request.form.getlist('ano[]')
            semestres = request.form.getlist('semestre[]')
            valores = request.form.getlist('valor[]')

            for ano, semestre, valor in zip(anos, semestres, valores):
                valor = valor.replace(',', '.')
                novo_valor = Valormeta(metape_id=metape_id, ano=int(ano), semestre=int(semestre), valor=float(valor))
                db.session.add(novo_valor)

            db.session.commit()
            flash('Meta e valores atualizados com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar valores da meta: {str(e)}', 'error')

        return redirect(url_for('planejamento.associar_metaspe'))

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
##################################################################################333333
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
    


def obter_planejamento():
    # Supondo que você esteja buscando o primeiro planejamento cadastrado no banco de dados
    planejamento = PlanejamentoEstrategico.query.first()
    return planejamento

def calcular_metas_prazo():
    hoje = datetime.now().date()
    metas_no_prazo = MetaPE.query.filter(MetaPE.data_termino >= hoje, MetaPE.status != 'Concluída').all()
    metas_atrasadas = MetaPE.query.filter(MetaPE.data_termino < hoje, MetaPE.status != 'Concluída').all()
    return metas_no_prazo, metas_atrasadas

def log_mensagem(mensagem):
    with open('log.txt', 'a') as f:
        f.write(mensagem + '\n')


def calcular_percentual_metas_atingidas(planejamento):
    metas = planejamento.metas  # Verifique se a relação está definida corretamente
    if not metas:
        return 0
    metas_atingidas = [meta for meta in metas if meta.status.lower() == 'concluída']  # Considere status como 'Concluída'
    percentual = (len(metas_atingidas) / len(metas)) * 100
    return round(percentual, 2)

def calcular_percentual_acoes_concluidas(planejamento):
    acoes = planejamento.acoes  # Verifique se a relação está definida corretamente
    if not acoes:
        return 0
    acoes_concluidas = [acao for acao in acoes if acao.status.lower() == 'concluída']  # Considere status como 'Concluída'
    percentual = (len(acoes_concluidas) / len(acoes)) * 100
    return round(percentual, 2)


##########################################################################################################3

def gerar_grafico_base64(percentual_concluidas):
    labels = ['Concluído', 'Em Andamento']
    sizes = [percentual_concluidas, 100 - percentual_concluidas]
    colors = ['#36a2eb', '#ff6384']

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    # Converter gráfico para imagem base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_base64 = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close(fig)

    return graph_base64

##################################################################################333
@planejamento_route.route('/indicadores_chave')
@login_required
def indicadores_chave():
    # Calcula o % de metas atingidas
    percentual_metas_atingidas = calcular_percentual_metas_atingidas()

    # Calcula as ações com maior impacto (ordenadas pela maior porcentagem de execução)
    acoes_maior_impacto = AcaoPE.query.order_by(AcaoPE.porcentagem_execucao.desc()).limit(5).all()

    # Calcula metas no prazo e metas atrasadas
    metas_no_prazo, metas_atrasadas = calcular_metas_prazo()

    return render_template(
        'indicadores_chave.html', 
        percentual_metas_atingidas=percentual_metas_atingidas,
        acoes_maior_impacto=acoes_maior_impacto,
        metas_no_prazo=metas_no_prazo,
        metas_atrasadas=metas_atrasadas
    )

#####################################################################33
@planejamento_route.route('/carregar_avisos')
@login_required
def carregar_avisos():
    coordenador_programa_id = session.get('programa_id')
    programa = Programa.query.get(coordenador_programa_id)
    alertas = []

    if programa:
        planejamentos = programa.planejamentos
        for planejamento in planejamentos:
            # Acessar objetivos associados ao planejamento
            for objetivo in planejamento.objetivos_pe:
                # Acessar metas associadas a cada objetivo
                for meta in objetivo.metas:
                    dias_restantes = (meta.data_termino - datetime.now().date()).days
                    if dias_restantes <= 7:
                        alertas.append({
                            'mensagem': f"Meta '{meta.nome}' está a {dias_restantes} dias do vencimento!",
                            'tipo': 'urgente' if dias_restantes <= 3 else 'aviso'
                        })

                    # Acessar ações associadas à meta
                    for acao in meta.acao_pe:
                        dias_restantes_acao = (acao.data_termino - datetime.now().date()).days
                        if dias_restantes_acao <= 7:
                            alertas.append({
                                'mensagem': f"Ação '{acao.nome}' da meta '{meta.nome}' está a {dias_restantes_acao} dias do vencimento!",
                                'tipo': 'urgente' if dias_restantes_acao <= 3 else 'aviso'
                            })

    return jsonify(alertas)



def carregar_alertas():
    alertas = []
    coordenador_programa_id = session.get('programa_id')
    programa = Programa.query.get(coordenador_programa_id)
    if programa:
        planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa.id).all()
        for planejamento in planejamentos:
            metas = MetaPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
            for meta in metas:
                dias_restantes = (meta.data_termino - datetime.now().date()).days
                if dias_restantes <= 7:
                    alertas.append({
                        'mensagem': f"Meta '{meta.nome}' está a {dias_restantes} dias do vencimento!",
                        'tipo': 'urgente' if dias_restantes <= 3 else 'aviso'
                    })
                acoes = AcaoPE.query.filter_by(meta_pe_id=meta.id).all()
                for acao in acoes:
                    dias_restantes_acao = (acao.data_termino - datetime.now().date()).days
                    if dias_restantes_acao <= 7:
                        alertas.append({
                            'mensagem': f"Ação '{acao.nome}' está a {dias_restantes_acao} dias do vencimento!",
                            'tipo': 'urgente' if dias_restantes_acao <= 3 else 'aviso'
                        })
    return alertas

def sugerir_ajustes(meta, progresso, restante):
    """Sugere ajustes com base nos dados da meta e progresso."""
    sugestoes = []
    if meta.data_termino:
        dias_restantes = (meta.data_termino - datetime.now().date()).days
    else:
        dias_restantes = None

    valor_alvo = float(meta.valor_alvo) if meta.valor_alvo else 0

    if progresso < 0.5 * valor_alvo and (dias_restantes is not None and dias_restantes < 30):
        sugestoes.append(f"A meta '{meta.nome}' está com progresso lento. Considere aumentar os recursos ou estender o prazo.")

    if progresso > 0.8 * valor_alvo and (dias_restantes is not None and dias_restantes > 30):
        sugestoes.append(f"A meta '{meta.nome}' está no caminho certo. Continue monitorando.")

    if not sugestoes:
        sugestoes.append("Não há sugestões no momento.")

    return sugestoes


####################################################################################
@planejamento_route.route('/atualizar_metas', methods=['POST'])
@login_required
def atualizar_metas():
    meta_id = request.form.get('meta_id')
    novo_status = request.form.get('status')

    # Busca a meta no banco de dados
    meta = MetaPE.query.get(meta_id)

    if meta:
        meta.status = novo_status
        db.session.commit()
        flash('Status atualizado com sucesso!', 'success')
    else:
        flash('Meta não encontrada.', 'danger')

    return redirect(url_for('planejamento.acompanhamento_metas'))

########################relatorio metas###############################333
@planejamento_route.route('/acompanhamento_metas', methods=['GET', 'POST'])
@login_required
def acompanhamento_metas():
    programa_id = current_user.programa_id
    planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()
    metas = []
    graph_base64 = None
    dados_graficos = []

    if request.method == 'POST':
        planejamento_id = request.form.get('planejamento_id')

        if planejamento_id:
            planejamento_selecionado = PlanejamentoEstrategico.query.get(planejamento_id)
            objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
            metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos])).all()
            valoresmetas = Valormeta.query.filter(Valormeta.metape_id.in_([meta.id for meta in metas])).all()

            # Preparar dados para o gráfico e sugestões
            for meta in metas:
                valores = [valor for valor in valoresmetas if valor.metape_id == meta.id]
                progresso = sum(valor.valor for valor in valores)
                valor_alvo = meta.valor_alvo or 0
                restante = max(valor_alvo - progresso, 0)

                sugestoes = sugerir_ajustes(meta, progresso, restante)
                dados_graficos.append({
                    'meta': meta.nome,
                    'data_inicio': meta.data_inicio,
                    'data_termino': meta.data_termino,
                    'progresso': progresso,
                    'restante': restante,
                    'sugestoes': sugestoes
                })

            # Gerar gráfico com legendas
            if dados_graficos:
                plt.figure(figsize=(12, 7))
                for dado in dados_graficos:
                    plt.barh(dado['meta'], dado['progresso'], color='skyblue', label='Progresso' if 'Progresso' not in plt.gca().get_legend_handles_labels()[1] else "")
                    plt.barh(dado['meta'], dado['restante'], left=dado['progresso'], color='lightcoral', label='Restante' if 'Restante' not in plt.gca().get_legend_handles_labels()[1] else "")

                plt.xlabel('Valor')
                plt.title('Progresso das Metas')
                plt.legend(loc='upper right')
                plt.tight_layout()

                img = BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                plt.close()

                graph_base64 = base64.b64encode(img.getvalue()).decode()

            if not metas:
                flash('Nenhuma meta encontrada para o planejamento selecionado.', 'warning')
        else:
            flash('Por favor, selecione um planejamento.', 'danger')

    return render_template(
        'acompanhamento_metas.html',
        metas=metas,
        planejamentos=planejamentos,
        graph_base64=graph_base64,
        dados_graficos=dados_graficos
    )


def gerar_grafico_metas(dados_graficos):
    plt.figure(figsize=(12, 7))  # Ajuste do tamanho para centralizar e dar mais espaço para rótulos

    for dado in dados_graficos:
        plt.barh(dado['meta'], dado['progresso'], color='skyblue', label='Progresso' if 'Progresso' not in plt.gca().get_legend_handles_labels()[1] else "")
        plt.barh(dado['meta'], dado['restante'], left=dado['progresso'], color='lightcoral', label='Restante' if 'Restante' not in plt.gca().get_legend_handles_labels()[1] else "")
    
    plt.xlabel('Valor')
    plt.title('Progresso das Metas')
    plt.legend(loc='upper right')  # Adicionar a legenda no canto superior direito
    plt.tight_layout()  # Ajustar o layout para melhor centralização e legibilidade

    # Salvando a imagem em base64 para exibir no HTML
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    graph_base64 = base64.b64encode(img.getvalue()).decode()
    return graph_base64



def sugerir_ajustes(meta, progresso, restante):
    """Sugere ajustes com base nos dados da meta e progresso."""
    sugestoes = []
    
    if meta.data_termino:
        dias_restantes = (meta.data_termino - datetime.now().date()).days
    else:
        dias_restantes = None
    
    valor_alvo = float(meta.valor_alvo) if meta.valor_alvo else 0
    
    if progresso < 0.5 * valor_alvo and (dias_restantes is not None and dias_restantes < 30):
        sugestoes.append(f"A meta '{meta.nome}' está com progresso lento. Considere aumentar os recursos ou estender o prazo.")
    
    if progresso > 0.8 * valor_alvo and (dias_restantes is not None and dias_restantes > 30):
        sugestoes.append(f"A meta '{meta.nome}' está no caminho certo. Continue monitorando.")

    return sugestoes
@planejamento_route.route('/atualizar_status_meta/<int:meta_id>', methods=['POST'])
@login_required
def atualizar_status_meta(meta_id):
    # Lógica para atualizar o status da meta
    meta = MetaPE.query.get(meta_id)
    if meta:
        novo_status = request.form.get('status')
        meta.status = novo_status
        db.session.commit()
        flash('Status atualizado com sucesso!', 'success')
    else:
        flash('Meta não encontrada.', 'danger')

    # Redireciona de volta para a página de acompanhamento de metas
    return redirect(url_for('planejamento.acompanhamento_metas'))

def calcular_progresso_parcial(meta):
    if meta.data_inicio and meta.data_termino:
        # Convertendo datas para o formato de cálculo
        data_inicio = meta.data_inicio
        data_termino = meta.data_termino
        hoje = datetime.now().date()

        # Verifica se a meta ainda está no prazo
        if hoje < data_inicio:
            return 0
        elif hoje > data_termino:
            return 100

        # Cálculo do progresso parcial
        duracao_total = (data_termino - data_inicio).days
        duracao_decorrida = (hoje - data_inicio).days

        progresso_parcial = (duracao_decorrida / duracao_total) * 100
        return round(progresso_parcial, 2)
    else:
        # Caso a meta não tenha datas definidas
        return 0


def calcular_progresso(meta):
    if meta.status == "Não iniciado":
        return 0
    elif meta.status == "Em andamento":
        # Calcular progresso parcial com base em algum critério (datas, ações realizadas, etc.)
        return calcular_progresso_parcial(meta)
    elif meta.status == "Atrasada":
        # Atrasada, mas o progresso pode ter sido feito
        return calcular_progresso_parcial(meta)
    elif meta.status == "Concluída":
        return 100
    elif meta.status == "Cancelada":
        return 0
    elif meta.status == "Pausada":
        # Retorna o progresso atual sem incrementá-lo
        return meta.progresso_atual
    elif meta.status == "Revisão":
        # Pode colocar em espera até a revisão ser concluída
        return meta.progresso_atual
####################################################################################################################3

@planejamento_route.route('/selecao_planejamento', methods=['GET'])
@login_required
def selecionar_planejamento():
    # Obtenha todos os planejamentos do programa do coordenador
    programa_id = current_user.programa_id
    planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).all()

    # Verifique se há planejamentos cadastrados
    if not planejamentos:
        flash("Não há planejamentos estratégicos cadastrados para o seu programa.")
        return redirect(url_for('outra_pagina'))  # Substitua 'outra_pagina' pelo endpoint desejado

    # Renderizar a página com a lista de planejamentos para seleção
    return render_template('selecionarplanej.html', planejamentos=planejamentos)
##### resumo ##################################3
@planejamento_route.route('/resumo_planejamento')
@login_required
def resumo_planejamento():
    planejamento_id = request.args.get('planejamento_id', type=int)
    programa_id = current_user.programa_id
    
    planejamento = PlanejamentoEstrategico.query.filter_by(id=planejamento_id, id_programa=programa_id).first()
    
    if not planejamento:
        flash("Planejamento estratégico não encontrado ou não pertence ao seu programa.")
        return redirect(url_for('novo_selecionar_planejamento'))

    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos])).all()
    total_metas = len(metas)
    metas_atingidas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos]), MetaPE.status == 'Concluída').count()
    percentual_metas_atingidas = (metas_atingidas / total_metas) * 100 if total_metas > 0 else 0

    # Calcular status das metas
    metas_em_andamento = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos]), MetaPE.status == 'Em Andamento').count()
    metas_atrasadas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos]), MetaPE.status == 'Atrasada').count()

    total_acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).count()
    acoes_concluidas = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas]), AcaoPE.status == 'Concluída').count()
    acoes_atrasadas = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas]), AcaoPE.status == 'Atrasada').count()
    percentual_acoes_concluidas = (acoes_concluidas / total_acoes) * 100 if total_acoes > 0 else 0

    # Obter indicadores e valores de metas
    indicadores_por_meta = {}
    valores_por_meta = {}
    for meta in metas:
        indicadores = IndicadorPlan.query.filter_by(meta_pe_id=meta.id).all()
        valores_metas = Valormeta.query.filter_by(metape_id=meta.id).all()  # Obtém os valores associados

        # Armazena indicadores e valores em dicionários
        indicadores_por_meta[meta.id] = indicadores
        valores_por_meta[meta.id] = valores_metas

    # Print para depuração
    print("Metas, Indicadores e Valores:", {
        meta_id: {
            "indicadores": [ind.nome for ind in inds],
            "valores": [{"ano": val.ano, "semestre": val.semestre, "valor": val.valor} for val in vals]
        }
        for meta_id, (inds, vals) in zip(indicadores_por_meta.keys(), zip(indicadores_por_meta.values(), valores_por_meta.values()))
    })

    return render_template(
        'resumo_planejamento.html',
        planejamento=planejamento,
        total_metas=total_metas,
        metas_atingidas=metas_atingidas,
        percentual_metas_atingidas=percentual_metas_atingidas,
        total_acoes=total_acoes,
        acoes_concluidas=acoes_concluidas,
        percentual_acoes_concluidas=percentual_acoes_concluidas,
        acoes_atrasadas=acoes_atrasadas,
        metas_em_andamento=metas_em_andamento,
        metas_atrasadas=metas_atrasadas,
        indicadores_por_meta=indicadores_por_meta,
        valores_por_meta=valores_por_meta,  # Enviando os valores para o template
        metas=metas
    )


      
############################# Resumo ##################################################################3
@planejamento_route.route('/get_coordenador', methods=['GET'])
@login_required
def get_planejamento_do_coordenador():
    # Verifique o programa_id do usuário logado
    programa_id = current_user.programa_id
    print(f"[DEBUG] ID do programa do usuário atual: {programa_id}")  # Deve ser o ID real do programa do usuário, por exemplo, 7

    # Tente buscar o planejamento estratégico do programa
    planejamento = PlanejamentoEstrategico.query.filter_by(id_programa=programa_id).first()
    print(f"[DEBUG] Planejamento encontrado: {planejamento}")  # Deve mostrar detalhes do planejamento ou None se não encontrado

    # Verifique se o planejamento foi encontrado
    if not planejamento:
        flash("Nenhum planejamento estratégico encontrado para o programa.")
        return render_template('indexcord.html', planejamento=None)

    # Se o planejamento foi encontrado, colete os dados das metas e ações
    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
    print(f"[DEBUG] Objetivos associados ao planejamento: {objetivos}")  # Lista os objetivos encontrados

    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos])).all()
    total_metas = len(metas)
    print(f"[DEBUG] Total de metas encontradas: {total_metas}")

    # Cálculo de metas atingidas
    metas_atingidas = MetaPE.query.filter(
        MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos]),
        MetaPE.status == 'Concluída'
    ).count()
    print(f"[DEBUG] Metas atingidas: {metas_atingidas}")

    # Percentual de metas atingidas
    percentual_metas_atingidas = (metas_atingidas / total_metas) * 100 if total_metas > 0 else 0
    print(f"[DEBUG] Percentual de metas atingidas: {percentual_metas_atingidas:.2f}%")

    # Cálculo de ações
    total_acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).count()
    print(f"[DEBUG] Total de ações encontradas: {total_acoes}")

    # Ações concluídas
    acoes_concluidas = AcaoPE.query.filter(
        AcaoPE.meta_pe_id.in_([meta.id for meta in metas]),
        AcaoPE.status == 'Concluída'
    ).count()
    print(f"[DEBUG] Ações concluídas: {acoes_concluidas}")

    # Ações atrasadas
    acoes_atrasadas = AcaoPE.query.filter(
        AcaoPE.meta_pe_id.in_([meta.id for meta in metas]),
        AcaoPE.status == 'Atrasada'
    ).count()
    print(f"[DEBUG] Ações atrasadas: {acoes_atrasadas}")

    # Percentual de ações concluídas
    percentual_acoes_concluidas = (acoes_concluidas / total_acoes) * 100 if total_acoes > 0 else 0
    print(f"[DEBUG] Percentual de ações concluídas: {percentual_acoes_concluidas:.2f}%")

    # Renderizar o template com os dados coletados
    return render_template(
        'indexcord.html',
        planejamento=planejamento,
        percentual_metas_atingidas=percentual_metas_atingidas,
        total_metas=total_metas,
        metas_atingidas=metas_atingidas,
        percentual_acoes_concluidas=percentual_acoes_concluidas,
        total_acoes=total_acoes,
        acoes_concluidas=acoes_concluidas,
        acoes_atrasadas=acoes_atrasadas
    )



##################################################3333

@planejamento_route.route('/test_prints/<int:planejamento_id>', methods=['GET'])
def test_prints(planejamento_id):
    print("Este é um teste de prints!")
    print("Planejamento ID:", planejamento_id)
    return "Verifique os prints no console"
#####################################################################################################3
@planejamento_route.route('/indicadores_desempenho')
@login_required
def indicadores_desempenho():
    # Obtenha os planejamentos relacionados ao programa do usuário
    planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=current_user.programa_id).all()
    
    metas = []
    
    # Itere pelos planejamentos para encontrar os objetivos e as metas associadas
    for planejamento in planejamentos:
        objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
        for objetivo in objetivos:
            metas.extend(MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all())
    
    historico_valores = {}

    # Itere sobre as metas associadas e busque os indicadores e seus valores
    for meta in metas:
        for indicador in meta.indicador_pe:
            valores = Valorindicador.query.filter_by(indicadorpe_id=indicador.id).all()
            if valores:
                historico_valores[indicador.nome.title()] = [(valor.ano, valor.valor) for valor in valores]  # Capitaliza o título

    return render_template('indicadores_desempenho.html', historico_valores=historico_valores)



@planejamento_route.route('/gerar_pdf_indicadores_desempenho')
@login_required
def gerar_pdf_indicadores_desempenho():
    # Obter dados atualizados de desempenho
    planejamentos = PlanejamentoEstrategico.query.filter_by(id_programa=current_user.programa_id).all()
    metas = []
    
    for planejamento in planejamentos:
        objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
        for objetivo in objetivos:
            metas.extend(MetaPE.query.filter_by(objetivo_pe_id=objetivo.id).all())
    
    historico_valores = {}
    for meta in metas:
        for indicador in meta.indicador_pe:
            valores = Valorindicador.query.filter_by(indicadorpe_id=indicador.id).all()
            if valores:
                historico_valores[indicador.nome.title()] = [(valor.ano, valor.valor) for valor in valores]

    # Inicializa o PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Indicadores de Desempenho", ln=True, align="C")

    # Itera sobre os indicadores e adiciona os dados e gráficos ao PDF
    for indicador, valores in historico_valores.items():
        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(0, 10, f"Indicador: {indicador}", ln=True)

        # Adiciona valores
        for data, valor in valores:
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"{data}: {valor}", ln=True)

        # Gerar gráfico temporário
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        with plt.ioff():
            plt.figure()
            labels = [f"{data}" for data, valor in valores]
            values = [valor for data, valor in valores]
            plt.plot(labels, values, marker="o")
            plt.title(f"Evolução de {indicador}")
            plt.xlabel("Ano")
            plt.ylabel("Valor")
            plt.savefig(temp_img.name, format="png")
            plt.close()

        # Adiciona o gráfico ao PDF
        pdf.image(temp_img.name, x=10, w=180)
        temp_img.close()

    # Enviar o PDF para download
    response = make_response(pdf.output(dest="S").encode("latin1"))
    response.headers["Content-Disposition"] = "attachment; filename=indicadores_desempenho.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response


#############################################################################3
@planejamento_route.route('/gerar_pdf_metas', methods=['GET', 'POST'])
@login_required
def gerar_pdf_metas():
    # Obtém o ID do programa do usuário logado
    programa_id = current_user.programa_id
    planejamento_id = request.args.get('planejamento_id')

    # Verifica se o planejamento foi selecionado e recupera as metas associadas
    metas = []
    if planejamento_id:
        objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento_id).all()
        metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos])).all()

    # Cria um buffer para armazenar o PDF em memória
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Acompanhamento de Metas")

    # Configurações de layout do PDF
    pdf.drawString(100, 750, "Acompanhamento de Metas")
    pdf.drawString(100, 735, f"Planejamento Estratégico ID: {planejamento_id}")

    y_position = 700
    for meta in metas:
        # Adiciona as informações da meta no PDF
        pdf.drawString(100, y_position, f"Nome da Meta: {meta.nome}")
        pdf.drawString(100, y_position - 15, f"Data de Início: {meta.data_inicio}")
        pdf.drawString(100, y_position - 30, f"Data de Término: {meta.data_termino}")
        pdf.drawString(100, y_position - 45, f"Status Atual: {meta.status or 'Não definido'}")
        pdf.drawString(100, y_position - 60, "-"*80)  # Linha separadora
        y_position -= 80

        # Caso a posição Y atinja o fim da página, cria uma nova página
        if y_position < 50:
            pdf.showPage()
            y_position = 750

    pdf.save()
    buffer.seek(0)

    # Envia o PDF para download
    return send_file(buffer, as_attachment=True, download_name="acompanhamento_metas.pdf", mimetype="application/pdf")


####################33 gerar pdf resumo planejmaneto ################################
from flask import make_response
from fpdf import FPDF

@planejamento_route.route('/gerar_pdf')
@login_required
def gerar_pdf():
    planejamento_id = request.args.get('planejamento_id', type=int)
    programa_id = current_user.programa_id
    
    planejamento = PlanejamentoEstrategico.query.filter_by(id=planejamento_id, id_programa=programa_id).first()
    if not planejamento:
        flash("Planejamento estratégico não encontrado ou não pertence ao seu programa.")
        return redirect(url_for('novo_selecionar_planejamento'))

    objetivos = ObjetivoPE.query.filter_by(planejamento_estrategico_id=planejamento.id).all()
    metas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos])).all()
    total_metas = len(metas)
    metas_atingidas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos]), MetaPE.status == 'Concluída').count()
    percentual_metas_atingidas = (metas_atingidas / total_metas) * 100 if total_metas > 0 else 0
    metas_em_andamento = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos]), MetaPE.status == 'Em Andamento').count()
    metas_atrasadas = MetaPE.query.filter(MetaPE.objetivo_pe_id.in_([obj.id for obj in objetivos]), MetaPE.status == 'Atrasada').count()

    acoes = AcaoPE.query.filter(AcaoPE.meta_pe_id.in_([meta.id for meta in metas])).all()
    total_acoes = len(acoes)
    acoes_concluidas = len([acao for acao in acoes if acao.status == 'Concluída'])
    percentual_acoes_concluidas = (acoes_concluidas / total_acoes) * 100 if total_acoes > 0 else 0

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Cabeçalho
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(200, 10, txt="Resumo do Planejamento Estratégico", ln=True, align="C")
    pdf.ln(10)

    # Planejamento
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(200, 10, txt=f"Planejamento: {planejamento.nome}", ln=True)
    pdf.ln(10)

    # Resumo das Metas
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Resumo das Metas:", ln=True)
    pdf.cell(200, 10, txt=f"- Total de Metas: {total_metas}", ln=True)
    pdf.cell(200, 10, txt=f"- Metas Atingidas: {percentual_metas_atingidas:.2f}%", ln=True)
    pdf.cell(200, 10, txt=f"- Metas em Andamento: {metas_em_andamento}", ln=True)
    pdf.cell(200, 10, txt=f"- Metas Atrasadas: {metas_atrasadas}", ln=True)
    pdf.ln(10)

    # Resumo das Ações
    pdf.cell(200, 10, txt="Resumo das Ações:", ln=True)
    pdf.cell(200, 10, txt=f"- Total de Ações: {total_acoes}", ln=True)
    pdf.cell(200, 10, txt=f"- Ações Concluídas: {percentual_acoes_concluidas:.2f}%", ln=True)
    pdf.cell(200, 10, txt=f"- Ações Atrasadas: {acoes_concluidas}", ln=True)
    pdf.ln(10)

    # Objetivos
    pdf.cell(200, 10, txt="Objetivos:", ln=True)
    for objetivo in objetivos:
        pdf.cell(200, 10, txt=f"- {objetivo.nome}", ln=True)
    pdf.ln(10)

    # Detalhamento das Metas e Indicadores
    pdf.cell(200, 10, txt="Metas e Indicadores:", ln=True)
    for meta in metas:
        pdf.cell(200, 10, txt=f"- Meta: {meta.nome}", ln=True)
        indicadores = IndicadorPlan.query.filter_by(meta_pe_id=meta.id).all()
        for indicador in indicadores:
            pdf.cell(200, 10, txt=f"  - Indicador: {indicador.nome} (Meta: {indicador.valor_meta})", ln=True)
        pdf.ln(5)

    # Geração do PDF
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=resumo_planejamento_{planejamento.id}.pdf'
    return response
