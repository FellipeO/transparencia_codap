from flask import Blueprint, render_template, session, redirect, url_for
from app.models import Lancamento

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Verifica se o usuário está autenticado
    if 'user' not in session:
        return redirect(url_for('auth.login'))  # Redireciona para a página de login se não estiver autenticado
    print("Sessão atual:", session)
    # Se estiver autenticado, exibe a tabela de lançamentos
    lancamentos = Lancamento.query.order_by(Lancamento.dDtLanc.desc()).all()
    return render_template('index.html', lancamentos=lancamentos)
