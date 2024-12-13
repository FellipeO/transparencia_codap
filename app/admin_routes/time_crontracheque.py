from flask import Blueprint, request, redirect, url_for, render_template, flash
from app import db
from app.admin_routes.routes import verificar_diretor
from app.models import Contracheque, Pessoas
from datetime import datetime
from urllib.parse import unquote

time_contracheque_bp = Blueprint('time_contracheque', __name__, url_prefix='/admin/time')

@time_contracheque_bp.route('/contracheque/<string:email>', methods=['GET'])
def listar_contracheques(email):
    if not verificar_diretor():  # Verifica se o usuário tem permissão
        return redirect(url_for('auth.error'))

    # Verificar se a pessoa existe
    pessoa = Pessoas.query.filter_by(email=email).first()
    if not pessoa:
        flash('Pessoa não encontrada.', 'danger')
        return redirect(url_for('time.index'))

    # Obter os contracheques da pessoa agrupados por mês/ano
    contracheques = Contracheque.query.filter_by(email=email).all()
    tabela_contracheques = {}

    for entrada in contracheques:
        if entrada.mes_ano not in tabela_contracheques:
            tabela_contracheques[entrada.mes_ano] = {
                'Salário Líquido': None,
                'INSS': None,
                'Gratificação': None,
                'Imposto de Renda': None
            }
        tabela_contracheques[entrada.mes_ano][entrada.descricao] = entrada.valor

    return render_template(
        'contracheque_lista.html',
        pessoa=pessoa,
        tabela_contracheques=tabela_contracheques
    )

@time_contracheque_bp.route('/contracheque/<string:email>/adicionar', methods=['GET', 'POST'])
def adicionar_contracheque(email):
    if not verificar_diretor():  # Verifica se o usuário tem permissão
        return redirect(url_for('auth.error'))
    
    # Verificar se a pessoa existe
    pessoa = Pessoas.query.filter_by(email=email).first()
    if not pessoa:
        flash('Pessoa não encontrada.', 'danger')
        return redirect(url_for('time.index'))

    if request.method == 'POST':
        mes_ano = request.form.get('mes_ano')
        salario_liquido = request.form.get('salario_liquido')
        inss = request.form.get('inss')
        gratificacao = request.form.get('gratificacao')
        imposto_renda = request.form.get('imposto_renda')

        # Lista de descrições e valores
        itens = [
            ("Salário Líquido", salario_liquido),
            ("INSS", inss),
            ("Gratificação", gratificacao),
            ("Imposto de Renda", imposto_renda)
        ]

        # Adicionar entradas na tabela para cada item preenchido
        for descricao, valor in itens:
            if valor:  # Apenas criar entrada para campos preenchidos
                contracheque = Contracheque(
                    mes_ano=mes_ano,
                    email=email,
                    descricao=descricao,
                    valor=float(valor)
                )
                db.session.add(contracheque)

        db.session.commit()
        flash('Contracheque adicionado com sucesso.', 'success')
        return redirect(url_for('time_contracheque.adicionar_contracheque', email=email))

    return render_template('contracheque_adicionar.html', pessoa=pessoa)

# Deletar um Contracheque
@time_contracheque_bp.route('/contracheque/deletar/<string:email>/<path:mes_ano>', methods=['POST'])
def deletar_contracheque(email, mes_ano):
    mes_ano = unquote(mes_ano)  # Decodifica o mes_ano
    try:
        # Deleta todas as entradas relacionadas ao contracheque específico
        contracheques = Contracheque.query.filter_by(email=email, mes_ano=mes_ano).all()
        if contracheques:
            for contracheque in contracheques:
                db.session.delete(contracheque)
            db.session.commit()
            flash(f'Contracheque de {mes_ano} deletado com sucesso.', 'success')
        else:
            flash(f'Nenhum contracheque encontrado para {mes_ano}.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar contracheque: {e}', 'danger')
    
    return redirect(url_for('time_contracheque.listar_contracheques', email=email))

