from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory
from app.models import RegimentoInterno
from app.decorators import login_required
from app import db
from datetime import datetime
from app.admin_routes.routes import verificar_diretor
import os

regimento_bp = Blueprint('regimento', __name__, url_prefix='/admin')

# Rota para visualizar o Regimento Interno
@regimento_bp.route('/regimento_interno')
@login_required
def regimento_interno():
    # Obtém todos os documentos de Regimento Interno ordenados por versão
    regimentos = RegimentoInterno.query.order_by(RegimentoInterno.versao.desc()).all()
    return render_template('regimento_interno.html', regimentos=regimentos)

# Rota para adicionar um novo Regimento Interno
@regimento_bp.route('/regimento_interno/adicionar', methods=['GET', 'POST'])
@login_required
def regimento_adicionar():
    if not verificar_diretor():
        return redirect(url_for('auth.error'))

    if request.method == 'POST':
        versao = request.form.get('versao')
        vigencia_inicio = request.form.get('vigencia_inicio')
        vigencia_fim = request.form.get('vigencia_fim') if not request.form.get('em_vigencia') else None
        status = request.form.get('status')
        texto = request.form.get('texto')

        # Converte as datas para o tipo datetime e depois para date
        try:
            vigencia_inicio_date = datetime.strptime(vigencia_inicio, '%Y-%m-%d').date()
            vigencia_fim_date = datetime.strptime(vigencia_fim, '%Y-%m-%d').date() if vigencia_fim else None
        except ValueError:
            flash('Datas inválidas. Por favor, insira uma data válida.', 'danger')
            return redirect(url_for('regimento.regimento_adicionar'))

        # Verificação para vigência em andamento
        if vigencia_fim_date and vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('regimento.regimento_adicionar'))

        # Verifica se a versão já existe na tabela
        versao_existente = RegimentoInterno.query.filter_by(versao=int(versao)).first()
        if versao_existente:
            flash('Erro: A versão já existe. Por favor, insira uma versão única.', 'danger')
            return redirect(url_for('regimento.regimento_adicionar'))

        # Busca a maior versão inferior à nova versão
        versao_anterior = (
            RegimentoInterno.query
            .filter(RegimentoInterno.versao < int(versao))
            .order_by(RegimentoInterno.versao.desc())
            .first()
        )

        # Valida a nova data de vigência contra a vigência final da versão anterior, se houver
        if versao_anterior and versao_anterior.vigencia_fim and vigencia_inicio_date < versao_anterior.vigencia_fim:
            flash(
                f'Erro: A data de início da nova vigência deve ser igual ou posterior à data de fim da versão anterior ({versao_anterior.versao}).',
                'danger'
            )
            return redirect(url_for('regimento.regimento_adicionar'))

        # Busca a menor versão superior à nova versão
        versao_subsequente = (
            RegimentoInterno.query
            .filter(RegimentoInterno.versao > int(versao))
            .order_by(RegimentoInterno.versao.asc())
            .first()
        )

        # Valida a data de vigência final contra a data de vigência inicial da versão subsequente, se houver
        if versao_subsequente and vigencia_fim_date and vigencia_fim_date > versao_subsequente.vigencia_inicio:
            flash(
                f'Erro: A data de fim da nova vigência deve ser igual ou anterior à data de início da próxima versão ({versao_subsequente.versao}).',
                'danger'
            )
            return redirect(url_for('regimento.regimento_adicionar'))

        # Gera o hash para o arquivo da nova versão
        hash_arquivo = gerar_hash_regimento(versao)
        documento_filename = None

        # Upload do documento, se o status for "registrado"
        if status == 'registrado' and 'documento' in request.files:
            documento = request.files['documento']
            if documento:
                # Salva o documento com o hash como nome do arquivo
                filename = f"{hash_arquivo}.pdf"
                documento.save(os.path.join(current_app.config['UPLOAD_FOLDER_REGIMENTO'], filename))
                documento_filename = filename

        # Cria o novo regimento após todas as validações
        novo_regimento = RegimentoInterno(
            versao=int(versao),
            vigencia_inicio=vigencia_inicio_date,
            vigencia_fim=vigencia_fim_date,
            status=status,
            texto=texto,
            hash=hash_arquivo if status == 'registrado' else None
        )

        db.session.add(novo_regimento)
        db.session.commit()

        return redirect(url_for('regimento.regimento_interno'))

    return render_template('regimento_adicionar.html')

@regimento_bp.route('/regimento_interno/editar/<int:versao>', methods=['GET', 'POST'])
@login_required
def regimento_editar(versao):
    if not verificar_diretor():
        return redirect(url_for('auth.error'))
    
    regimento = RegimentoInterno.query.get(versao)
    if not regimento:
        flash("Versão não encontrada.", "danger")
        return redirect(url_for('regimento.regimento_interno'))

    if request.method == 'POST':
        nova_versao = request.form.get('versao')
        vigencia_inicio = request.form.get('vigencia_inicio')
        vigencia_fim = request.form.get('vigencia_fim') if not request.form.get('em_vigencia') else None
        status = request.form.get('status')
        texto = request.form.get('texto')

        # Verifica se a nova versão já existe no banco
        if nova_versao != str(regimento.versao):
            versao_existente = RegimentoInterno.query.get(int(nova_versao))
            if versao_existente:
                flash("Erro: A versão já existe!", "danger")
                return redirect(url_for('regimento.regimento_editar', versao=versao))

        # Converte as datas e realiza a validação
        try:
            vigencia_inicio_date = datetime.strptime(vigencia_inicio, '%Y-%m-%d').date()
            vigencia_fim_date = datetime.strptime(vigencia_fim, '%Y-%m-%d').date() if vigencia_fim else None
        except ValueError:
            flash('Datas inválidas. Por favor, insira uma data válida.', 'danger')
            return redirect(url_for('regimento.regimento_editar', versao=versao))
        
        if vigencia_fim:
            if vigencia_inicio_date > vigencia_fim_date:
                flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
                return redirect(url_for('regimento.regimento_editar', versao=versao))

        # Verificação para vigência em andamento
        if vigencia_fim_date and vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('regimento.regimento_editar', versao=versao))

        # Busca a maior versão inferior à versão atual, excluindo a própria versão
        versao_anterior = (
            RegimentoInterno.query
            .filter(RegimentoInterno.versao < int(nova_versao), RegimentoInterno.versao != regimento.versao)
            .order_by(RegimentoInterno.versao.desc())
            .first()
        )

        # Valida a nova data de vigência contra a vigência final da versão anterior, se houver
        if versao_anterior and versao_anterior.vigencia_fim and vigencia_inicio_date < versao_anterior.vigencia_fim:
            flash(
                f'Erro: A data de início da nova vigência deve ser igual ou posterior à data de fim da versão anterior ({versao_anterior.versao}).',
                'danger'
            )
            return redirect(url_for('regimento.regimento_editar', versao=versao))

        # Busca a menor versão superior à nova versão
        versao_subsequente = (
            RegimentoInterno.query
            .filter(RegimentoInterno.versao > int(nova_versao), RegimentoInterno.versao != regimento.versao)
            .order_by(RegimentoInterno.versao.asc())
            .first()
        )

        # Valida a data de vigência final contra a data de vigência inicial da versão subsequente, se houver
        if versao_subsequente and vigencia_fim_date and vigencia_fim_date > versao_subsequente.vigencia_inicio:
            flash(
                f'Erro: A data de fim da nova vigência deve ser igual ou anterior à data de início da próxima versão ({versao_subsequente.versao}).', 
                'danger'
            )
            return redirect(url_for('regimento.regimento_editar', versao=versao))

        # Deleta o arquivo antigo se o status mudar de 'registrado' para 'aprovado'
        if regimento.status == 'registrado' and status == 'aprovado' and regimento.hash:
            old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER_REGIMENTO'], f"{regimento.hash}.pdf")
            if os.path.exists(old_filepath):
                os.remove(old_filepath)  # Remove o arquivo associado
            regimento.hash = None  # Remove o hash já que não deve haver documento para a versão aprovada

        # Verifica se um novo documento foi enviado
        documento = request.files.get('documento')
        if status == 'registrado' and documento and documento.filename != '':
            # Gera novo hash para o arquivo com base na nova versão
            hash_arquivo = gerar_hash_regimento(nova_versao)
            filename = f"{hash_arquivo}.pdf"
            
            # Salva o novo documento
            documento.save(os.path.join(current_app.config['UPLOAD_FOLDER_REGIMENTO'], filename))
            
            # Deleta o arquivo antigo (se houver) e atualiza o hash no banco
            if regimento.hash and regimento.hash != hash_arquivo:  # Verifica se a hash é diferente
                old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER_REGIMENTO'], f"{regimento.hash}.pdf")
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            regimento.hash = hash_arquivo
        elif status == 'registrado' and not regimento.hash:
            flash("Erro: Nenhum documento foi selecionado para upload. Por favor, selecione um arquivo.", "danger")
            return redirect(url_for('regimento.regimento_editar', versao=versao))

        # Atualiza os valores no banco de dados
        regimento.versao = int(nova_versao)
        regimento.vigencia_inicio = vigencia_inicio_date
        regimento.vigencia_fim = vigencia_fim_date
        regimento.status = status
        regimento.texto = texto
        
        db.session.commit()
        return redirect(url_for('regimento.regimento_detalhe', versao=regimento.versao))

    return render_template('regimento_editar.html', regimento=regimento)

@regimento_bp.route('/regimento_interno/<int:versao>/download')
def regimento_download(versao):
    regimento = RegimentoInterno.query.get(versao)
    if regimento and regimento.hash:
        # Gera o nome do arquivo a partir da versão
        nome_arquivo = f"Regimento Interno Versão {regimento.versao}.pdf"
        
        # Busca o arquivo pelo hash
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER_REGIMENTO'],
            f"{regimento.hash}.pdf",
            as_attachment=True,
            download_name=nome_arquivo  # Define o nome do arquivo para o download
        )
    flash("Documento não encontrado ou não disponível para esta versão.", "warning")
    return redirect(url_for('regimento.regimento_interno'))

@regimento_bp.route('/regimento_interno/deletar/<int:versao>', methods=['POST'])
@login_required
def regimento_deletar(versao):
    if not verificar_diretor():
        return redirect(url_for('auth.error'))
    
    # Tenta buscar a versão do regimento
    regimento = RegimentoInterno.query.get(versao)
    if regimento:
        # Verifica se há um arquivo associado e tenta removê-lo
        if regimento.hash:
            arquivo_path = os.path.join(current_app.config['UPLOAD_FOLDER_REGIMENTO'], f"{regimento.hash}.pdf")
            if os.path.exists(arquivo_path):
                os.remove(arquivo_path)  # Remove o arquivo associado à versão

        db.session.delete(regimento)
        db.session.commit()
    else:
        flash('Erro: Versão do Regimento Interno não encontrada.', 'danger')
    
    return redirect(url_for('regimento.regimento_interno'))

@regimento_bp.route('/regimento_interno/<int:versao>')
@login_required
def regimento_detalhe(versao):
    regimento = RegimentoInterno.query.get_or_404(versao)
    return render_template('regimento_detalhe.html', regimento=regimento)

def gerar_hash_regimento(versao):
    import hashlib
    hash_obj = hashlib.sha256(f"Regimento Interno Versão {versao}".encode())
    return hash_obj.hexdigest()