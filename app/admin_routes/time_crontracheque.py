from flask import Blueprint, request, redirect, url_for, render_template, flash
from app import db
from app.admin_routes.routes import verificar_diretor
from app.models import Contracheque, Pessoas, Timeline
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

    # Obter os contracheques consolidados
    contracheques = Contracheque.query.filter_by(email=email).all()

    # Organizar os dados em um dicionário por mês/ano
    tabela_contracheques = {
        c.mes_ano: {
            'Salário Bruto': c.salario_bruto,
            'INSS': c.inss,
            'Imposto de Renda': c.imposto_renda,
            'Gratificação': c.gratificacao
        }
        for c in contracheques
    }

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
        data_hora = request.form.get('data_hora')

        if not mes_ano:
            flash('O campo Mês/Ano é obrigatório.', 'danger')
            return redirect(url_for('time_contracheque.adicionar_contracheque', email=email))
        
        # Função para converter valores com vírgula para ponto
        def converter_valor(valor):
            if valor:
                return float(valor.replace(',', '.'))
            return 0.0

        salario_bruto = converter_valor(request.form.get('salario_bruto'))
        inss = converter_valor(request.form.get('inss'))
        gratificacao = converter_valor(request.form.get('gratificacao'))
        imposto_renda = converter_valor(request.form.get('imposto_renda'))
        
        # Verifica se já existe um contracheque para o mesmo mes_ano e email
        contracheque_existente = Contracheque.query.filter_by(
            email=email, mes_ano=mes_ano
        ).first()

        if contracheque_existente:
            flash(f'Já existe um contracheque para {mes_ano}.', 'danger')
            return redirect(url_for('time_contracheque.adicionar_contracheque', email=email))

        # Criar um novo contracheque
        contracheque = Contracheque(
            mes_ano=mes_ano,
            email=email,
            salario_bruto=float(salario_bruto),
            inss=float(inss),
            gratificacao=float(gratificacao),
            imposto_renda=float(imposto_renda)
        )

        db.session.add(contracheque)
        db.session.flush()  # Garante que o ID seja gerado antes do commit

        # Converter a string de data e hora para um objeto datetime
        data_hora_obj = datetime.strptime(data_hora, '%Y-%m-%dT%H:%M')

        # Adiciona o contracheque na timeline
        timeline_entry = Timeline(
            email=email,
            data_hora=data_hora_obj,
            tipo='contracheque',
            referencia_id=contracheque.id
        )
        db.session.add(timeline_entry)

        db.session.commit()

        return redirect(url_for('time_contracheque.listar_contracheques', email=email))

    return render_template('contracheque_adicionar.html', pessoa=pessoa)

# Deletar um Contracheque
@time_contracheque_bp.route('/contracheque/deletar/<string:email>/<path:mes_ano>', methods=['POST'])
def deletar_contracheque(email, mes_ano):
    mes_ano = unquote(mes_ano)  # Decodifica o mes_ano
    try:
        # Deleta a entrada do contracheque consolidado
        contracheque = Contracheque.query.filter_by(email=email, mes_ano=mes_ano).first()
        if contracheque:
            db.session.delete(contracheque)
            db.session.commit()
        else:
            flash(f'Nenhum contracheque encontrado para {mes_ano}.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar contracheque: {e}', 'danger')

    return redirect(url_for('time_contracheque.listar_contracheques', email=email))
