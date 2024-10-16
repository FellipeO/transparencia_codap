from flask import Blueprint, render_template
from app.models import Lancamento
from sqlalchemy import desc

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Ordena pela data de lançamento (dDtLanc) de forma decrescente
    lancamentos = Lancamento.query.order_by(desc(Lancamento.dDtLanc)).all()
    # Ajusta os valores quando a natureza for 'P' (contas a pagar)
    for lancamento in lancamentos:
        if lancamento.cNatureza == 'P':
            lancamento.nValorLanc = -lancamento.nValorLanc
    return render_template('index.html', lancamentos=lancamentos)
