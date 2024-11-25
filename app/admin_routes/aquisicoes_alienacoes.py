from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory
from app.models import AquisicoesAlienacoes
from app.decorators import login_required
from app import db
from datetime import datetime
from app.admin_routes.routes import verificar_diretor
import os

aquisicoes_bp = Blueprint('aquisicoes', __name__, url_prefix='/admin')

# Rota para visualizar o Regulamento de Aquisições e Alienações
@aquisicoes_bp.route('/aquisicoes_alienacoes')
@login_required
def aquisicoes_alienacoes():
    # Obtém todos os documentos de Regulamento de Aquisições e Alienações ordenados por versão
    aquisicoes = AquisicoesAlienacoes.query.order_by(AquisicoesAlienacoes.versao.desc()).all()
    return render_template('aquisicoes_alienacoes.html', aquisicoes=aquisicoes)

@aquisicoes_bp.route('/aquisicoes_alienacoes/adicionar', methods=['GET', 'POST'])
@login_required
def aquisicoes_adicionar():
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
            return redirect(url_for('aquisicoes.aquisicoes_adicionar'))
        
        # Verificação para vigência em andamento
        if vigencia_fim_date and vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('aquisicoes.aquisicoes_adicionar'))

        # Verifica se a versão já existe na tabela
        versao_existente = AquisicoesAlienacoes.query.filter_by(versao=int(versao)).first()
        if versao_existente:
            flash('Erro: A versão já existe. Por favor, insira uma versão única.', 'danger')
            return redirect(url_for('aquisicoes.aquisicoes_adicionar'))

        # Verifica se vigencia_inicio não é posterior a vigencia_fim
        if vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('aquisicoes.aquisicoes_adicionar'))

        # Busca a maior versão inferior à nova versão
        versao_anterior = (
            AquisicoesAlienacoes.query
            .filter(AquisicoesAlienacoes.versao < int(versao))
            .order_by(AquisicoesAlienacoes.versao.desc())
            .first()
        )

        # Se houver uma versão anterior, valida a nova data de vigência contra a vigência final da versão anterior
        if versao_anterior and vigencia_inicio_date < versao_anterior.vigencia_fim:
            flash(
                f'Erro: A data de início da nova vigência deve ser igual ou posterior à data de fim da versão anterior ({versao_anterior.versao}).', 
                'danger'
            )
            return redirect(url_for('aquisicoes.aquisicoes_adicionar'))

        # Busca a menor versão superior à nova versão
        versao_subsequente = (
            AquisicoesAlienacoes.query
            .filter(AquisicoesAlienacoes.versao > int(versao))
            .order_by(AquisicoesAlienacoes.versao.asc())
            .first()
        )

        # Se houver uma versão subsequente, valida a data de vigência final contra a data de vigência inicial da versão subsequente
        if versao_subsequente and vigencia_fim_date > versao_subsequente.vigencia_inicio:
            flash(
                f'Erro: A data de fim da nova vigência deve ser igual ou anterior à data de início da próxima versão ({versao_subsequente.versao}).', 
                'danger'
            )
            return redirect(url_for('aquisicoes.aquisicoes_adicionar'))
        
        # Gera o hash para o arquivo da nova versão
        hash_arquivo = gerar_hash_aquisicoes(versao)
        documento_filename = None
        
        # Upload do documento, se o status for "registrado"
        if status == 'registrado' and 'documento' in request.files:
            documento = request.files['documento']
            if documento:
                # Salva o documento com o hash como nome do arquivo
                filename = f"{hash_arquivo}.pdf"
                documento.save(os.path.join(current_app.config['UPLOAD_FOLDER_AQUISICOES'], filename))
                documento_filename = filename
        
        # Cria o novo regulamento após todas as validações
        nova_aquisicoes = AquisicoesAlienacoes(
            versao=int(versao),
            vigencia_inicio=vigencia_inicio_date,
            vigencia_fim=vigencia_fim_date,
            status=status,
            texto=texto,
            hash=hash_arquivo if status == 'registrado' else None
        )

        db.session.add(nova_aquisicoes)
        db.session.commit()

        return redirect(url_for('aquisicoes.aquisicoes_alienacoes'))

    return render_template('aquisicoes_adicionar.html')

@aquisicoes_bp.route('/aquisicoes_alienacoes/editar/<int:versao>', methods=['GET', 'POST'])
@login_required
def aquisicoes_editar(versao):
    if not verificar_diretor():
        return redirect(url_for('auth.error'))
    
    aquisicao = AquisicoesAlienacoes.query.get(versao)
    if not aquisicao:
        flash("Versão não encontrada.", "danger")
        return redirect(url_for('aquisicoes.aquisicoes_alienacoes'))

    if request.method == 'POST':
        nova_versao = request.form.get('versao')
        vigencia_inicio = request.form.get('vigencia_inicio')
        vigencia_fim = request.form.get('vigencia_fim') if not request.form.get('em_vigencia') else None
        status = request.form.get('status')
        texto = request.form.get('texto')

        # Verifica se a nova versão já existe no banco
        if nova_versao != str(aquisicao.versao):
            versao_existente = AquisicoesAlienacoes.query.get(int(nova_versao))
            if versao_existente:
                flash("Erro: A versão já existe!", "danger")
                return redirect(url_for('aquisicoes.aquisicoes_editar', versao=versao))

        # Converte as datas e realiza a validação
        try:
            vigencia_inicio_date = datetime.strptime(vigencia_inicio, '%Y-%m-%d').date()
            vigencia_fim_date = datetime.strptime(vigencia_fim, '%Y-%m-%d').date() if vigencia_fim else None
        except ValueError:
            flash('Datas inválidas. Por favor, insira uma data válida.', 'danger')
            return redirect(url_for('aquisicoes.aquisicoes_editar', versao=versao))
        
        if vigencia_fim:
            if vigencia_inicio_date > vigencia_fim_date:
                flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
                return redirect(url_for('aquisicoes.aquisicoes_editar', versao=versao))
        
        # Verificação para vigência em andamento
        if vigencia_fim_date and vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('aquisicoes.aquisicoes_editar', versao=versao))

        # Busca a maior versão inferior à versão atual, excluindo a própria versão
        versao_anterior = (
            AquisicoesAlienacoes.query
            .filter(AquisicoesAlienacoes.versao < int(nova_versao), AquisicoesAlienacoes.versao != aquisicao.versao)
            .order_by(AquisicoesAlienacoes.versao.desc())
            .first()
        )

        # Valida a nova data de vigência contra a vigência final da versão anterior
        if versao_anterior and vigencia_inicio_date < versao_anterior.vigencia_fim:
            flash(
                f'Erro: A data de início da vigência deve ser igual ou posterior à data de fim da versão anterior ({versao_anterior.versao}).', 
                'danger'
            )
            return redirect(url_for('aquisicoes.aquisicoes_editar', versao=versao))

        # Busca a menor versão superior à versão atual, excluindo a própria versão
        versao_subsequente = (
            AquisicoesAlienacoes.query
            .filter(AquisicoesAlienacoes.versao > int(nova_versao), AquisicoesAlienacoes.versao != aquisicao.versao)
            .order_by(AquisicoesAlienacoes.versao.asc())
            .first()
        )

        # Valida a nova data de vigência contra a vigência inicial da versão subsequente
        if versao_subsequente and vigencia_fim_date > versao_subsequente.vigencia_inicio:
            flash(
                f'Erro: A data de fim da vigência deve ser igual ou anterior à data de início da próxima versão ({versao_subsequente.versao}).', 
                'danger'
            )
            return redirect(url_for('aquisicoes.aquisicoes_editar', versao=versao))

        # Deleta o arquivo antigo se o status mudar de 'registrado' para 'aprovado'
        if aquisicao.status == 'registrado' and status == 'aprovado' and aquisicao.hash:
            old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER_AQUISICOES'], f"{aquisicao.hash}.pdf")
            if os.path.exists(old_filepath):
                os.remove(old_filepath)  # Remove o arquivo associado
            aquisicao.hash = None  # Remove o hash já que não deve haver documento para a versão aprovada

        # Verifica se um novo documento foi enviado
        documento = request.files.get('documento')
        if status == 'registrado' and documento and documento.filename != '':
            # Gera novo hash para o arquivo com base na nova versão
            hash_arquivo = gerar_hash_aquisicoes(nova_versao)
            filename = f"{hash_arquivo}.pdf"
            
            # Salva o novo documento
            documento.save(os.path.join(current_app.config['UPLOAD_FOLDER_AQUISICOES'], filename))
            
            # Deleta o arquivo antigo (se houver) e atualiza o hash no banco
            if aquisicao.hash and aquisicao.hash != hash_arquivo:  # Verifica se a hash é diferente
                old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER_AQUISICOES'], f"{aquisicao.hash}.pdf")
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            aquisicao.hash = hash_arquivo
        elif status == 'registrado' and not aquisicao.hash:
            flash("Erro: Nenhum documento foi selecionado para upload. Por favor, selecione um arquivo.", "danger")
            return redirect(url_for('aquisicoes.aquisicoes_editar', versao=versao))

        # Atualiza os valores no banco de dados
        aquisicao.versao = int(nova_versao)
        aquisicao.vigencia_inicio = vigencia_inicio_date
        aquisicao.vigencia_fim = vigencia_fim_date
        aquisicao.status = status
        aquisicao.texto = texto
        
        db.session.commit()
        return redirect(url_for('aquisicoes.aquisicoes_detalhe', versao=aquisicao.versao))

    return render_template('aquisicoes_editar.html', aquisicao=aquisicao)

@aquisicoes_bp.route('/aquisicoes_alienacoes/<int:versao>/download')
def aquisicao_download(versao):
    aquisicao = AquisicoesAlienacoes.query.get(versao)
    if aquisicao and aquisicao.hash:
        # Gera o nome do arquivo a partir da versão
        nome_arquivo = f"Regulamento de Aquisições e Alienações Versão {aquisicao.versao}.pdf"
        
        # Busca o arquivo pelo hash
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER_AQUISICOES'],
            f"{aquisicao.hash}.pdf",
            as_attachment=True,
            download_name=nome_arquivo  # Define o nome do arquivo para o download
        )
    flash("Documento não encontrado ou não disponível para esta versão.", "warning")
    return redirect(url_for('aquisicoes.aquisicoes_alienacoes'))

@aquisicoes_bp.route('/aquisicoes_alienacoes/deletar/<int:versao>', methods=['POST'])
@login_required
def aquisicoes_deletar(versao):
    if not verificar_diretor():
        return redirect(url_for('auth.error'))
    
    # Tenta buscar a versão do regulamento
    aquisicao = AquisicoesAlienacoes.query.get(versao)
    if aquisicao:
        # Verifica se há um arquivo associado e tenta removê-lo
        if aquisicao.hash:
            arquivo_path = os.path.join(current_app.config['UPLOAD_FOLDER_AQUISICOES'], f"{aquisicao.hash}.pdf")
            if os.path.exists(arquivo_path):
                os.remove(arquivo_path)  # Remove o arquivo associado à versão

        db.session.delete(aquisicao)
        db.session.commit()
    else:
        flash('Erro: Versão do Regulamento de Aquisições e Alienações não encontrada.', 'danger')
    
    return redirect(url_for('aquisicoes.aquisicoes_alienacoes'))

@aquisicoes_bp.route('/aquisicoes_alienacoes/<int:versao>')
@login_required
def aquisicoes_detalhe(versao):
    aquisicao = AquisicoesAlienacoes.query.get_or_404(versao)
    return render_template('aquisicoes_detalhe.html', aquisicao=aquisicao)

def gerar_hash_aquisicoes(versao):
    import hashlib
    hash_obj = hashlib.sha256(f"Regulamento de Aquisições e Alienações Versão {versao}".encode())
    return hash_obj.hexdigest()