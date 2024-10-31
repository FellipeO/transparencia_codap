from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import Lancamento, GrupoUsuario
from app.decorators import login_required
from app import db

# Blueprint para rotas administrativas
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def admin_homepage():
    return render_template('admin.html')

@admin_bp.route('/lancamentos')
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

def verificar_super_admin():
    email = session.get('email')
    usuario = GrupoUsuario.query.filter_by(email=email).first()
    if usuario is None or usuario.grupo != 'super_admin':
        session.clear()
        flash('Seu acesso foi revogado. Por favor, faça login novamente.', 'danger')
        return False
    return True

@admin_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))
    usuarios = GrupoUsuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/adicionar', methods=['POST'])
@login_required
def adicionar_usuario():
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    email = request.form.get('email')
    grupo = request.form.get('grupo')

    novo_usuario = GrupoUsuario(email=email, grupo=grupo)
    db.session.add(novo_usuario)
    db.session.commit()
    
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/editar/<string:email>', methods=['GET'])
@login_required
def editar_usuario_form(email):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    return render_template('editar_usuario.html', usuario=usuario)

@admin_bp.route('/usuarios/editar/<string:email>', methods=['POST'])
@login_required
def editar_usuario(email):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    usuario.grupo = request.form.get('grupo')
    db.session.commit()
    
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/adicionar', methods=['GET'])
@login_required
def adicionar_usuario_form():
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    return render_template('adicionar_usuario.html')

@admin_bp.route('/usuarios/excluir/<string:email>', methods=['POST'])
@login_required
def excluir_usuario(email):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    usuario = GrupoUsuario.query.filter_by(email=email).first()
    db.session.delete(usuario)
    db.session.commit()

    return redirect(url_for('admin.usuarios'))

# Middleware para atualizar a sessão com as permissões mais recentes
@admin_bp.before_request
def atualizar_permissoes():
    email = session.get('email')
    if email:
        usuario = GrupoUsuario.query.filter_by(email=email).first()
        if usuario:
            session['grupo'] = usuario.grupo  # Atualiza a sessão com o grupo atual
        else:
            # Redireciona para o logout se o usuário não existir mais
            flash("Seu acesso foi revogado. Por favor, faça login novamente.", "danger")
            return redirect(url_for('auth.logout'))