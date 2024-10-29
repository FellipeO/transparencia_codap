from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import Lancamento, GrupoUsuario
from app.decorators import login_required
from app import db

main_bp = Blueprint('main', __name__)

# Rota para a homepage
@main_bp.route('/')
def homepage():
    return render_template('homepage.html')

# Rota para exibir os lançamentos, protegida por login
@main_bp.route('/lancamentos')
@login_required
def lancamentos():
    email = session.get('email')
    usuario = GrupoUsuario.query.filter_by(email=email).first()
    
    if usuario is None:
        session.clear()
        flash('Seu acesso foi revogado. Por favor, faça login novamente.', 'danger')
        return redirect(url_for('auth.error'))

    lancamentos = Lancamento.query.order_by(Lancamento.dDtLanc.desc()).all()
    return render_template('lancamentos.html', lancamentos=lancamentos)

# Rota para verificar se o usuário é super_admin
def verificar_super_admin():
    email = session.get('email')
    usuario = GrupoUsuario.query.filter_by(email=email).first()
    if usuario is None or usuario.grupo != 'super_admin':
        session.clear()
        flash('Seu acesso foi revogado. Por favor, faça login novamente.', 'danger')
        return False
    return True

# Rota para exibir a tabela de usuários e gerenciar o CRUD
@main_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    usuarios = GrupoUsuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

# Rota para adicionar um novo usuário
@main_bp.route('/usuarios/adicionar', methods=['POST'])
@login_required
def adicionar_usuario():
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    email = request.form.get('email')
    grupo = request.form.get('grupo')

    novo_usuario = GrupoUsuario(email=email, grupo=grupo)
    db.session.add(novo_usuario)
    db.session.commit()
    
    return redirect(url_for('main.usuarios'))

# Rota para exibir o formulário de edição de um usuário
@main_bp.route('/usuarios/editar/<string:email>', methods=['GET'])
@login_required
def editar_usuario_form(email):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    return render_template('editar_usuario.html', usuario=usuario)

# Função para editar um usuário existente
@main_bp.route('/usuarios/editar/<string:email>', methods=['POST'])
@login_required
def editar_usuario(email):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    usuario.grupo = request.form.get('grupo')
    db.session.commit()
    
    return redirect(url_for('main.usuarios'))

# Rota para exibir o formulário de adicionar novo usuário
@main_bp.route('/usuarios/adicionar', methods=['GET'])
@login_required
def adicionar_usuario_form():
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    return render_template('adicionar_usuario.html')

# Função para excluir um usuário
@main_bp.route('/usuarios/excluir/<string:email>', methods=['POST'])
@login_required
def excluir_usuario(email):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    db.session.delete(usuario)
    db.session.commit()

    return redirect(url_for('main.usuarios'))
