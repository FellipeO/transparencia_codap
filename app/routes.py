from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, send_from_directory
from app.models import Lancamento, GrupoUsuario, EstatutoSocial
from app.decorators import login_required
from app import db
from datetime import datetime
import hashlib, os

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
        
        # Gera o hash para o arquivo da nova versão
        hash_arquivo = gerar_hash_arquivo(versao)
        documento_filename = None
        
        # Upload do documento, se o status for "registrado"
        if status == 'registrado' and 'documento' in request.files:
            documento = request.files['documento']
            if documento:
                # Salva o documento com o hash como nome do arquivo
                filename = f"{hash_arquivo}.pdf"
                documento.save(os.path.join(current_app.config['UPLOAD_FOLDER_ESTATUTO'], filename))
                documento_filename = filename
        
        # Cria o novo estatuto após todas as validações
        novo_estatuto = EstatutoSocial(
            versao=int(versao),
            vigencia_inicio=vigencia_inicio,
            vigencia_fim=vigencia_fim,
            status=status,
            texto=texto,
            hash=hash_arquivo if status == 'registrado' else None
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
        nova_versao = request.form.get('versao')
        vigencia_inicio = request.form.get('vigencia_inicio')
        vigencia_fim = request.form.get('vigencia_fim')
        status = request.form.get('status')
        texto = request.form.get('texto')

        # Verifica se a nova versão já existe no banco
        if nova_versao != str(estatuto.versao):
            versao_existente = EstatutoSocial.query.get(int(nova_versao))
            if versao_existente:
                flash("Erro: A versão já existe!", "danger")
                return redirect(url_for('admin.estatuto_editar', versao=versao))

        # Converte as datas e realiza a validação
        try:
            vigencia_inicio_date = datetime.strptime(vigencia_inicio, '%Y-%m-%d').date()
            vigencia_fim_date = datetime.strptime(vigencia_fim, '%Y-%m-%d').date()
        except ValueError:
            flash('Datas inválidas. Por favor, insira uma data válida.', 'danger')
            return redirect(url_for('admin.estatuto_editar', versao=versao))

        if vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('admin.estatuto_editar', versao=versao))

        # Deleta o arquivo antigo se o status mudar de 'registrado' para 'aprovado'
        if estatuto.status == 'registrado' and status == 'aprovado' and estatuto.hash:
            old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER_ESTATUTO'], f"{estatuto.hash}.pdf")
            if os.path.exists(old_filepath):
                os.remove(old_filepath)  # Remove o arquivo associado

            estatuto.hash = None  # Remove o hash já que não deve haver documento para a versão aprovada

        # Atualiza o arquivo se o status for registrado e um novo arquivo for enviado
        if status == 'registrado' and 'documento' in request.files:
            documento = request.files['documento']
            if documento:
                # Gera novo hash para o arquivo com base na nova versão
                hash_arquivo = gerar_hash_arquivo(nova_versao)
                filename = f"{hash_arquivo}.pdf"
                
                # Salva o novo documento
                documento.save(os.path.join(current_app.config['UPLOAD_FOLDER_ESTATUTO'], filename))
                
                # Deleta o arquivo antigo (se houver) e atualiza o hash no banco
                if estatuto.hash and estatuto.hash != hash_arquivo:  # Verifica se a hash é diferente
                    old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER_ESTATUTO'], f"{estatuto.hash}.pdf")
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                
                estatuto.hash = hash_arquivo
            else:
                flash("Erro ao fazer upload do documento. Por favor, tente novamente.", "danger")
                return redirect(url_for('admin.estatuto_editar', versao=versao))

        # Atualiza os valores no banco de dados
        estatuto.versao = int(nova_versao)
        estatuto.vigencia_inicio = vigencia_inicio_date
        estatuto.vigencia_fim = vigencia_fim_date
        estatuto.status = status
        estatuto.texto = texto
        
        db.session.commit()
        return redirect(url_for('admin.estatuto_detalhe', versao=estatuto.versao))

    return render_template('estatuto_editar.html', estatuto=estatuto)

@admin_bp.route('/estatuto_social/<int:versao>/download')
@login_required
def estatuto_download(versao):
    estatuto = EstatutoSocial.query.get(versao)
    if estatuto and estatuto.hash:
        # Gera o nome do arquivo a partir da versão
        nome_arquivo = f"Estatuto Social Versão {estatuto.versao}.pdf"
        
        # Busca o arquivo pelo hash
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER_ESTATUTO'],
            f"{estatuto.hash}.pdf",
            as_attachment=True,
            download_name=nome_arquivo  # Define o nome do arquivo para o download
        )
    flash("Documento não encontrado ou não disponível para esta versão.", "warning")
    return redirect(url_for('admin.estatuto_social'))

@admin_bp.route('/estatuto_social/deletar/<int:versao>', methods=['POST'])
@login_required
def estatuto_deletar(versao):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))
    
    # Tenta buscar a versão do estatuto
    estatuto = EstatutoSocial.query.get(versao)
    if estatuto:
        # Verifica se há um arquivo associado e tenta removê-lo
        if estatuto.hash:
            arquivo_path = os.path.join(current_app.config['UPLOAD_FOLDER_ESTATUTO'], f"{estatuto.hash}.pdf")
            if os.path.exists(arquivo_path):
                os.remove(arquivo_path)  # Remove o arquivo associado à versão

        db.session.delete(estatuto)
        db.session.commit()
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
        
def gerar_hash_arquivo(versao):
    import hashlib
    hash_obj = hashlib.sha256(f"Estatuto Social Versão {versao}".encode())
    return hash_obj.hexdigest()