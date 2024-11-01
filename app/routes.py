from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import Lancamento, GrupoUsuario, EstatutoSocial
from app.decorators import login_required
from app import db
from datetime import datetime

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

# Rota para visualizar o Estatuto Social
@admin_bp.route('/estatuto_social')
@login_required
def estatuto_social():
    # Obtém todos os documentos de Estatuto Social ordenados por versão
    estatutos = EstatutoSocial.query.order_by(EstatutoSocial.versao.desc()).all()
    return render_template('estatuto_social.html', estatutos=estatutos)

@admin_bp.route('/estatuto_social/adicionar', methods=['GET', 'POST'])
@login_required
def estatuto_adicionar():
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))

    if request.method == 'POST':
        versao = request.form.get('versao')
        vigencia_inicio = request.form.get('vigencia_inicio')
        vigencia_fim = request.form.get('vigencia_fim')
        status = request.form.get('status')
        texto = request.form.get('texto')

        # Converte as datas para o tipo datetime e depois para date
        try:
            vigencia_inicio_date = datetime.strptime(vigencia_inicio, '%Y-%m-%d').date()
            vigencia_fim_date = datetime.strptime(vigencia_fim, '%Y-%m-%d').date()
        except ValueError:
            flash('Datas inválidas. Por favor, insira uma data válida.', 'danger')
            return redirect(url_for('admin.estatuto_adicionar'))

        # Verifica se a versão já existe na tabela
        versao_existente = EstatutoSocial.query.filter_by(versao=int(versao)).first()
        if versao_existente:
            flash('Erro: A versão já existe. Por favor, insira uma versão única.', 'danger')
            return redirect(url_for('admin.estatuto_adicionar'))

        # Verifica se vigencia_inicio não é posterior a vigencia_fim
        if vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('admin.estatuto_adicionar'))

        # Busca a última versão do Estatuto Social para checar vigência
        ultima_versao = EstatutoSocial.query.order_by(EstatutoSocial.versao.desc()).first()

        # Se houver uma última versão, valida a nova data de vigência contra a versão anterior
        if ultima_versao and vigencia_inicio_date < ultima_versao.vigencia_fim:
            flash('Erro: A data de início da nova vigência deve ser igual ou posterior à data de fim da última vigência.', 'danger')
            return redirect(url_for('admin.estatuto_adicionar'))

        # Cria o novo estatuto após todas as validações
        novo_estatuto = EstatutoSocial(
            versao=int(versao),
            vigencia_inicio=vigencia_inicio,
            vigencia_fim=vigencia_fim,
            status=status,
            texto=texto
        )

        db.session.add(novo_estatuto)
        db.session.commit()

        return redirect(url_for('admin.estatuto_social'))

    return render_template('estatuto_adicionar.html')

@admin_bp.route('/estatuto_social/editar/<int:versao>', methods=['GET', 'POST'])
@login_required
def estatuto_editar(versao):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))
    
    estatuto = EstatutoSocial.query.get(versao)
    if not estatuto:
        flash("Versão não encontrada.", "danger")
        return redirect(url_for('admin.estatuto_social'))

    if request.method == 'POST':
        # Checagem para evitar duplicação de versão
        nova_versao = request.form.get('versao')
        if nova_versao != str(estatuto.versao):
            if EstatutoSocial.query.get(nova_versao):
                flash("Erro: A versão já existe!", "danger")
                return redirect(url_for('admin.estatuto_editar', versao=versao))

        # Atualização dos valores
        estatuto.versao = nova_versao
        estatuto.vigencia_inicio = request.form.get('vigencia_inicio')
        estatuto.vigencia_fim = request.form.get('vigencia_fim')
        estatuto.status = request.form.get('status')
        estatuto.texto = request.form.get('texto')
        
        db.session.commit()
        return redirect(url_for('admin.estatuto_detalhe', versao=estatuto.versao))

    return render_template('estatuto_editar.html', estatuto=estatuto)

@admin_bp.route('/estatuto_social/deletar/<int:versao>', methods=['POST'])
@login_required
def estatuto_deletar(versao):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))
    
    # Tenta buscar a versão do estatuto
    estatuto = EstatutoSocial.query.get(versao)
    if estatuto:
        db.session.delete(estatuto)
        db.session.commit()
        flash(f'Versão {versao} do Estatuto Social deletada com sucesso.', 'success')
    else:
        flash('Erro: Versão do Estatuto Social não encontrada.', 'danger')
    
    return redirect(url_for('admin.estatuto_social'))

@admin_bp.route('/estatuto_social/<int:versao>')
@login_required
def estatuto_detalhe(versao):
    estatuto = EstatutoSocial.query.get_or_404(versao)
    return render_template('estatuto_detalhe.html', estatuto=estatuto)

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