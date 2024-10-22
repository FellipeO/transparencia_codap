from flask import Blueprint, render_template, session, redirect, url_for
from app.models import Lancamento
from app.decorators import login_required  # Certifique-se de usar o decorator de login

main_bp = Blueprint('main', __name__)

# Rota para a homepage
@main_bp.route('/')
def homepage():
    return render_template('homepage.html')  # Simples homepage

# Rota para exibir os lançamentos, protegida por login
@main_bp.route('/lancamentos')
@login_required  # Verifica se o usuário está logado
def lancamentos():
    # Se estiver autenticado, exibe a tabela de lançamentos
    lancamentos = Lancamento.query.order_by(Lancamento.dDtLanc.desc()).all()
    return render_template('lancamentos.html', lancamentos=lancamentos)
