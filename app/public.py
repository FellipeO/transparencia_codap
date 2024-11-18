from flask import Blueprint, render_template, request
from app.models import EstatutoSocial, AquisicoesAlienacoes, OportunidadesInvestimento, Lancamento

public_bp = Blueprint('public', __name__)

# Rota para a página inicial pública
@public_bp.route('/')
def homepage():
    return render_template('homepage.html')

@public_bp.route('/lancamentos')
def lancamentos():
    # Consulta ao banco de dados para buscar lançamentos ordenados por data
    lancamentos = Lancamento.query.order_by(Lancamento.dDtLanc.desc()).all()
    return render_template('lancamentos_frontend.html', lancamentos=lancamentos)

# Rota para exibir o estatuto, com a versão selecionada
@public_bp.route('/estatuto')
def estatuto():
    versao = request.args.get('versao', default=None, type=int)  # Captura o parâmetro de versão da URL
    
    # Sempre pega todas as versões para a barra lateral
    estatutos = EstatutoSocial.query.order_by(EstatutoSocial.versao.desc()).all()

    if versao:
        # Filtra apenas a versão selecionada para exibir o conteúdo principal
        estatuto_atual = EstatutoSocial.query.filter_by(versao=versao).first()
        return render_template('estatuto_frontend.html', estatutos=estatutos, estatuto_atual=estatuto_atual)
    
    # Se nenhuma versão for selecionada, exibe a mais recente
    estatuto_atual = estatutos[0] if estatutos else None
    return render_template('estatuto_frontend.html', estatutos=estatutos, estatuto_atual=estatuto_atual)

# Rota para exibir o regulamento de aquisições, com a versão selecionada
@public_bp.route('/aquisicao')
def aquisicao():
    versao = request.args.get('versao', default=None, type=int)  # Captura o parâmetro de versão da URL
    
    # Sempre pega todas as versões para a barra lateral
    aquisicoes = AquisicoesAlienacoes.query.order_by(AquisicoesAlienacoes.versao.desc()).all()

    if versao:
        # Filtra apenas a versão selecionada para exibir o conteúdo principal
        aquisicao_atual = AquisicoesAlienacoes.query.filter_by(versao=versao).first()
        return render_template('aquisicao_frontend.html', aquisicoes=aquisicoes, aquisicao_atual=aquisicao_atual)
    
    # Se nenhuma versão for selecionada, exibe a mais recente
    aquisicao_atual = aquisicoes[0] if aquisicoes else None
    return render_template('aquisicao_frontend.html', aquisicoes=aquisicoes, aquisicao_atual=aquisicao_atual)

# Rota para exibir a política de investimento, com a versão selecionada
@public_bp.route('/oportunidade')
def oportunidade():
    versao = request.args.get('versao', default=None, type=int)  # Captura o parâmetro de versão da URL
    
    # Sempre pega todas as versões para a barra lateral
    oportunidades = OportunidadesInvestimento.query.order_by(OportunidadesInvestimento.versao.desc()).all()

    if versao:
        # Filtra apenas a versão selecionada para exibir o conteúdo principal
        oportunidade_atual = OportunidadesInvestimento.query.filter_by(versao=versao).first()
        return render_template('oportunidade_frontend.html', oportunidades=oportunidades, oportunidade_atual=oportunidade_atual)
    
    # Se nenhuma versão for selecionada, exibe a mais recente
    oportunidade_atual = oportunidades[0] if oportunidades else None
    return render_template('oportunidade_frontend.html', oportunidades=oportunidades, oportunidade_atual=oportunidade_atual)
