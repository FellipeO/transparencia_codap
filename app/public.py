from . import db
from flask import Blueprint, render_template, request, abort, send_from_directory, current_app
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, func
from sqlalchemy.exc import NoResultFound
from app.models import EstatutoSocial, AquisicoesAlienacoes, OportunidadesInvestimento, RegimentoInterno, Lancamento, Clientes, Pessoas, Evento, EventoArquivo
import os

public_bp = Blueprint('public', __name__)

meses_pt = {
    1: 'janeiro',
    2: 'fevereiro',
    3: 'março',  # Corrige o problema com o "ç"
    4: 'abril',
    5: 'maio',
    6: 'junho',
    7: 'julho',
    8: 'agosto',
    9: 'setembro',
    10: 'outubro',
    11: 'novembro',
    12: 'dezembro'
}

# Rota para a página inicial pública
@public_bp.route('/')
def homepage():
    # Obtém o ano e mês atuais
    hoje = datetime.now()

    # Calcula a data de 12 meses atrás
    data_12_meses_antes = hoje - relativedelta(months=12)

    # Calcula o total de contas a pagar (cNatureza = 'P') e a receber (cNatureza = 'R')
    totais = (
        db.session.query(
            Lancamento.cNatureza,
            func.sum(Lancamento.nValorLanc).label('total')
        )
        .filter(
            Lancamento.dDtLanc >= data_12_meses_antes,
            Lancamento.cNatureza.in_(['P', 'R']),  # Apenas "Pagar" e "Receber"
            Lancamento.nCodCCDestino == 0
        )
        .group_by(Lancamento.cNatureza)
        .all()
    )

    # Inicializa os valores como zero
    contas_a_pagar = 0
    contas_a_receber = 0

    # Processa os resultados da consulta
    for natureza, total in totais:
        if natureza == 'P':
            contas_a_pagar = total
        elif natureza == 'R':
            contas_a_receber = total

    # Consulta para contar o total de funcionários e a porcentagem de mulheres
    total_funcionarios = db.session.query(func.count(Pessoas.email)).scalar()
    total_mulheres = db.session.query(func.count(Pessoas.email)).filter(Pessoas.genero == 'Feminino').scalar()

    # Calcula a porcentagem de mulheres
    porcentagem_mulheres = (total_mulheres / total_funcionarios * 100) if total_funcionarios > 0 else 0

    # Pesquisa todas as pessoas presentes no time
    pessoas = Pessoas.query.all()
    hoje = date.today()
    for pessoa in pessoas:
        pessoa.longevidade = (hoje - pessoa.data_admissao).days

    # Consulta os próximos três eventos, com o nome do organizador
    proximos_eventos = (
        db.session.query(Evento, Pessoas.nome.label('organizador_nome'), Pessoas.slug.label('organizador_slug'))
        .join(Pessoas, Pessoas.email == Evento.email_organizador)  # Faz o join para pegar o nome do organizador
        .filter(Evento.data >= hoje)
        .order_by(Evento.data, Evento.hora)  # Ordena por data e hora
        .limit(3)  # Limita a 3 resultados
        .all()
    )

    # Renderiza o template com os dados
    return render_template(
        'homepage.html',
        contas_a_pagar=contas_a_pagar,
        contas_a_receber=contas_a_receber,
        total_funcionarios=total_funcionarios,
        porcentagem_mulheres=porcentagem_mulheres,
        pessoas=pessoas,
        eventos=proximos_eventos
    )

def formatar_mes_em_portugues(mes, ano):
    return f'{meses_pt[mes].capitalize()} {ano}'

@public_bp.route('/extratofinanceiro')
def extratofinanceiro():
    # Obtém o mês e ano atual caso nenhum seja fornecido
    mes = request.args.get('mes', default=datetime.now().month, type=int)
    ano = request.args.get('ano', default=datetime.now().year, type=int)
    
    # Obtém o código da conta (nCodCC), se fornecido, senão retorna None (todos)
    cod_cc = request.args.get('cod_cc', default=None, type=int)

    # Filtra os lançamentos pelo mês e ano selecionados, e pela conta (se fornecida)
    lancamentos_query = (
        db.session.query(Lancamento)
        .outerjoin(Clientes, Lancamento.nCodCliente == Clientes.codigo_cliente_omie)
        .filter(
            extract('month', Lancamento.dDtLanc) == mes,
            extract('year', Lancamento.dDtLanc) == ano
        )
    )
    
    # Aplica o filtro de conta se um nCodCC for selecionado
    if cod_cc is not None:
        lancamentos_query = lancamentos_query.filter(Lancamento.nCodCC == cod_cc)

    # Obter todos os lançamentos que atendem aos filtros (mês, ano, e cod_cc)
    lancamentos = lancamentos_query.order_by(Lancamento.dDtLanc.desc()).all()

    # Obter todos os meses disponíveis para o dropdown
    meses_disponiveis = (
        db.session.query(
            extract('month', Lancamento.dDtLanc).label('mes'),
            extract('year', Lancamento.dDtLanc).label('ano')
        )
        .distinct()
        .order_by(extract('year', Lancamento.dDtLanc).desc(), extract('month', Lancamento.dDtLanc).desc())
        .all()
    )

    # Obter todas as contas (nCodCC) distintas
    contas_disponiveis = db.session.query(Lancamento.nCodCC).distinct().all()
    contas = [conta[0] for conta in contas_disponiveis]  # Extrai os valores de nCodCC das tuplas

    # Formatar os meses para exibir no dropdown
    meses_dropdown = [
    {'mes': int(mes), 'ano': int(ano), 'label': formatar_mes_em_portugues(mes, ano)}
    for mes, ano in meses_disponiveis
    ]

    # Renderizar o template com os dados necessários
    return render_template(
        'extratofinanceiro_frontend.html',
        lancamentos=lancamentos,
        meses_dropdown=meses_dropdown,
        mes_atual=mes,
        ano_atual=ano,
        contas=contas,  # Passar as contas para o template
        cod_cc_selecionada=cod_cc,  # Passar o código da conta selecionada
        datetime=datetime,  # Passar datetime para uso no template
        formatar_mes_em_portugues=formatar_mes_em_portugues
    )

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

# Rota para exibir o regimento, com a versão selecionada
@public_bp.route('/regimento')
def regimento():
    versao = request.args.get('versao', default=None, type=int)  # Captura o parâmetro de versão da URL
    
    # Sempre pega todas as versões para a barra lateral
    regimentos = RegimentoInterno.query.order_by(RegimentoInterno.versao.desc()).all()

    if versao:
        # Filtra apenas a versão selecionada para exibir o conteúdo principal
        regimento_atual = RegimentoInterno.query.filter_by(versao=versao).first()
        return render_template('regimento_frontend.html', regimentos=regimentos, regimento_atual=regimento_atual)
    
    # Se nenhuma versão for selecionada, exibe a mais recente
    regimento_atual = regimentos[0] if regimentos else None
    return render_template('regimento_frontend.html', regimentos=regimentos, regimento_atual=regimento_atual)

@public_bp.route('/time/<string:slug>')
def time_detalhe(slug):
    # Tenta buscar a pessoa pelo slug
    try:
        pessoa = db.session.query(Pessoas).filter_by(slug=slug).one()
    except NoResultFound:
        abort(404, description="Pessoa não encontrada.")

    current_date = datetime.utcnow().date()
    
    return render_template('time_detalhe_frontend.html', pessoa=pessoa, current_date=current_date)

@public_bp.route('/uploads/<path:filename>')
def uploads(filename):
    """Serve arquivos do diretório de uploads."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER_TIME'], filename)


# Rota para exibir os detalhes de um evento
@public_bp.route('/evento/<int:id>')
def evento_detalhe(id):
    # Buscar o evento pelo ID
    evento = db.session.get(Evento, id)
    if not evento:
        abort(404)  # Retorna erro 404 se o evento não for encontrado

    # Buscar organizador relacionado
    organizador = db.session.query(Pessoas).filter_by(email=evento.email_organizador).first()

    # Diretório do evento
    evento_folder = os.path.join(current_app.config['UPLOAD_FOLDER_EVENTOS'], str(id))
    arquivos = os.listdir(evento_folder) if os.path.exists(evento_folder) else []

    # Obter as descrições dos arquivos associados ao evento
    descricoes_arquivos = {
        arquivo.nome_arquivo: arquivo.descricao
        for arquivo in db.session.query(EventoArquivo).filter_by(evento_id=id).all()
    }

    return render_template(
        'evento_detalhe_frontend.html',
        evento=evento,
        organizador=organizador,
        arquivos=arquivos,
        evento_folder=evento_folder,
        descricoes_arquivos=descricoes_arquivos
    )

# Rota para fazer o download de um arquivo
@public_bp.route('/evento/<int:id>/download/<path:arquivo>')
def download_arquivo(id, arquivo):
    evento_folder = os.path.join(current_app.config['UPLOAD_FOLDER_EVENTOS'], str(id))
    return send_from_directory(evento_folder, arquivo, as_attachment=True)