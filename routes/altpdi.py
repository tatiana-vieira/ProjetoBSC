from flask import Flask, render_template,jsonify,request,url_for,redirect,flash
from .models import PDI, Objetivo, Meta, Indicador,db
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint

#pdi_route = Flask(__name__)
altpdi_route = Blueprint('altpdi', __name__)

@altpdi_route.route('/selecionar_programa', methods=['GET', 'POST'])
def selecionar_programa():
    if request.method == 'POST':
        pdi_id = request.form['pdi_id']
        return redirect(url_for('altpdi.exibir_altpdi', pdi_id=pdi_id))

    pdis = PDI.query.all()
    return render_template('selecionar_programa.html', pdis=pdis)

@altpdi_route.route('/exibir_altpdi')
def exibir_altpdi():
    pdi_id = request.args.get('pdi_id')
    if not pdi_id:
        return redirect(url_for('selecionar_programa'))

    pdi_data = PDI.query.filter_by(id=pdi_id).first()
    if not pdi_data:
        flash('Programa não encontrado.')
        return redirect(url_for('selecionar_programa'))

    objetivos = Objetivo.query.filter_by(pdi_id=pdi_id).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()

    if not objetivos or not metas or not indicadores:
        flash('Ainda não há planejamento para este programa.')
        return redirect(url_for('selecionar_programa'))

    return render_template('altpdi.html', pdi=pdi_data, objetivos=objetivos, metas=metas, indicadores=indicadores)


@altpdi_route.route('/selecionar_planejamento', methods=['GET', 'POST'])
def selecionar_planejamento():
    if request.method == 'POST':
        pdi_id = request.form['pdi_id']
        return redirect(url_for('altpdi.exibir_planejamento', pdi_id=pdi_id))

    pdis = PDI.query.all()
    return render_template('selecionar_planejamento.html', pdis=pdis)

@altpdi_route.route('/exibir_planejamento')
def exibir_planejamento():
    pdi_id = request.args.get('pdi_id')
    if not pdi_id:
        return redirect(url_for('altpdi.selecionar_planejamento'))

    pdi_data = PDI.query.filter_by(id=pdi_id).first()
    if not pdi_data:
        flash('Planejamento não encontrado.')
        return redirect(url_for('altpdi.selecionar_planejamento'))

    objetivos = Objetivo.query.filter_by(pdi_id=pdi_id).all()
    metas = Meta.query.filter(Meta.objetivo_id.in_([objetivo.id for objetivo in objetivos])).all()
    indicadores = Indicador.query.filter(Indicador.meta_pdi_id.in_([meta.id for meta in metas])).all()

    if not objetivos and not metas and not indicadores:
        flash('Ainda não há planejamento para este PDI.')
        return redirect(url_for('altpdi.selecionar_planejamento'))

    return render_template('exibir_planejamento.html', pdi=pdi_data, objetivos=objetivos, metas=metas, indicadores=indicadores)