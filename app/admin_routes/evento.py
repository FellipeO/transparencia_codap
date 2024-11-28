from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models import db, Evento
from app.decorators import login_required
from app.admin_routes.routes import verificar_diretor
from datetime import datetime

# Blueprint para eventos
evento_bp = Blueprint('evento', __name__, url_prefix='/admin')

# Rota para visualizar os eventos
@evento_bp.route('/evento')
@login_required
def evento():
    eventos = db.session.query(Evento).order_by(Evento.data.asc(), Evento.hora.asc()).all()
    return render_template('evento.html', eventos=eventos)

# Rota para adicionar eventos
@evento_bp.route('/evento/adicionar', methods=['GET', 'POST'])
@login_required
def evento_adicionar():
    if not verificar_diretor():  # Verifica se o usuário tem permissão
        return redirect(url_for('auth.error'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        data = request.form.get('data')
        hora = request.form.get('hora')
        endereco = request.form.get('endereco')
        email_organizador = request.form.get('email_organizador')
        descricao = request.form.get('descricao')

        # Validação de campos obrigatórios
        if not all([nome, data, hora, endereco, email_organizador]):
            flash('Todos os campos devem ser preenchidos.', 'danger')
            return redirect(url_for('evento.evento_adicionar'))
        
        # Converter data e hora para os formatos corretos
        try:
            data = datetime.strptime(data, '%Y-%m-%d').date()
            hora = datetime.strptime(hora, '%H:%M').time()
        except ValueError:
            flash('Data ou hora inválidas.', 'danger')
            return redirect(url_for('evento.evento_adicionar'))
        
        # Criar o evento
        novo_evento = Evento(
            nome=nome,
            data=data,
            hora=hora,
            endereco=endereco,
            email_organizador=email_organizador,
            descricao=descricao
        )

        try:
            db.session.add(novo_evento)
            db.session.commit()
            flash('Evento adicionado com sucesso!', 'success')
            return redirect(url_for('evento.evento'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar evento: {str(e)}', 'danger')
            return redirect(url_for('evento.evento_adicionar'))
    
    return render_template('evento_adicionar.html')

# Rota para editar eventos
@evento_bp.route('/evento/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def evento_editar(id):
    if not verificar_diretor():
        return redirect(url_for('auth.error'))
    
    evento = db.session.get(Evento, id)
    if not evento:
        flash('Evento não encontrado.', 'danger')
        return redirect(url_for('evento.evento'))
    
    if request.method == 'POST':
        evento.nome = request.form.get('nome')
        evento.data = request.form.get('data')
        evento.hora = request.form.get('hora')
        evento.endereco = request.form.get('endereco')
        evento.email_organizador = request.form.get('email_organizador')
        evento.descricao = request.form.get('descricao')

        # Validação de campos obrigatórios
        if not all([evento.nome, evento.data, evento.hora, evento.endereco, evento.email_organizador]):
            flash('Todos os campos devem ser preenchidos.', 'danger')
            return redirect(url_for('evento.evento_editar', id=id))
        
        # Converter data e hora para os formatos corretos
        try:
            evento.data = datetime.strptime(evento.data, '%Y-%m-%d').date()
            evento.hora = datetime.strptime(evento.hora, '%H:%M').time()
        except ValueError:
            flash('Data ou hora inválidas.', 'danger')
            return redirect(url_for('evento.evento_editar', id=id))

        try:
            db.session.commit()
            flash('Evento atualizado com sucesso!', 'success')
            return redirect(url_for('evento.evento'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar evento: {str(e)}', 'danger')
            return redirect(url_for('evento.evento_editar', id=id))
    
    return render_template('evento_editar.html', evento=evento)

# Rota para deletar eventos
@evento_bp.route('/evento/deletar/<int:id>', methods=['POST'])
@login_required
def evento_deletar(id):
    if not verificar_diretor():
        return redirect(url_for('auth.error'))
    
    evento = db.session.get(Evento, id)
    if not evento:
        flash('Evento não encontrado.', 'danger')
        return redirect(url_for('evento.evento'))
    
    try:
        db.session.delete(evento)
        db.session.commit()
        flash('Evento deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar evento: {str(e)}', 'danger')
    
    return redirect(url_for('evento.evento'))

