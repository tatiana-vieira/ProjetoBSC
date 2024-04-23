from flask import Blueprint, render_template

home_route = Blueprint('home', __name__)

@home_route.route('/')
def page_home():
    return render_template('index.html')

@home_route.route('/PDI')
def page_pdi():
    return render_template('pdi.html')

@home_route.route('/visualizacao')
def visualizacao():
     return render_template('bsc.html')

@home_route.route('/login')
def login():
  return render_template('login.html')

@home_route.route('/register')
def register():
  return render_template('register.html')

