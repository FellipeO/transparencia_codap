from flask import Blueprint, render_template, session, redirect, url_for, request
from app.models import Lancamento, GrupoUsuario  # Modelo GrupoUsuario
from app.decorators import login_required  # Certifique-se de usar o decorator de login
from app import db  # Instância do banco de dados

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

# Rota para exibir a tabela de usuários e gerenciar o CRUD
@main_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    # Verifica se o usuário é super_admin
    if session.get('grupo') != 'super_admin':
        return redirect(url_for('main.homepage'))

    # Exibe todos os usuários na tabela 'grupos_usuarios'
    usuarios = GrupoUsuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

# Função para adicionar um novo usuário
@main_bp.route('/usuarios/adicionar', methods=['POST'])
@login_required
def adicionar_usuario():
    if session.get('grupo') != 'super_admin':
        return redirect(url_for('main.homepage'))

    email = request.form.get('email')
    grupo = request.form.get('grupo')

    # Adiciona o novo usuário ao banco de dados
    novo_usuario = GrupoUsuario(email=email, grupo=grupo)
    db.session.add(novo_usuario)
    db.session.commit()
    
    return redirect(url_for('main.usuarios'))

# Rota para exibir o formulário de edição de um usuário
@main_bp.route('/usuarios/editar/<string:email>', methods=['GET'])
@login_required
def editar_usuario_form(email):
    # Verifica se o usuário é super_admin
    if session.get('grupo') != 'super_admin':
        return redirect(url_for('main.homepage'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    return render_template('editar_usuario.html', usuario=usuario)

# Função para editar um usuário existente
@main_bp.route('/usuarios/editar/<string:email>', methods=['POST'])
@login_required
def editar_usuario(email):
    # Verifica se o usuário é super_admin
    if session.get('grupo') != 'super_admin':
        return redirect(url_for('main.homepage'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    usuario.grupo = request.form.get('grupo')
    db.session.commit()
    
    return redirect(url_for('main.usuarios'))

# Rota para exibir o formulário de adicionar novo usuário
@main_bp.route('/usuarios/adicionar', methods=['GET'])
@login_required
def adicionar_usuario_form():
    if session.get('grupo') != 'super_admin':
        return redirect(url_for('main.homepage'))

    return render_template('adicionar_usuario.html')

# Função para excluir um usuário
@main_bp.route('/usuarios/excluir/<string:email>', methods=['POST'])
@login_required
def excluir_usuario(email):
    # Verifica se o usuário é super_admin
    if session.get('grupo') != 'super_admin':
        return redirect(url_for('main.homepage'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    db.session.delete(usuario)
    db.session.commit()

    return redirect(url_for('main.usuarios'))
