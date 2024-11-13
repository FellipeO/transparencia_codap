from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory
from app.models import OportunidadesInvestimento
from app.decorators import login_required
from app import db
from datetime import datetime
from app.admin_routes.routes import verificar_super_admin
import os

oportunidades_bp = Blueprint('oportunidades', __name__, url_prefix='/admin')

# Rota para visualizar a Política de Seleção e Avaliação de Oportunidades de Investimento
@oportunidades_bp.route('/oportunidades_investimento')
@login_required
def oportunidades_investimento():
    # Obtém todos os documentos de Política de Seleção e Avaliação de Oportunidades de Investimento ordenados por versão
    oportunidades = OportunidadesInvestimento.query.order_by(OportunidadesInvestimento.versao.desc()).all()
    return render_template('oportunidades_investimento.html', oportunidades=oportunidades)

@oportunidades_bp.route('/oportunidades_investimento/adicionar', methods=['GET', 'POST'])
@login_required
def oportunidades_adicionar():
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
            return redirect(url_for('oportunidades.oportunidades_adicionar'))

        # Verifica se a versão já existe na tabela
        versao_existente = OportunidadesInvestimento.query.filter_by(versao=int(versao)).first()
        if versao_existente:
            flash('Erro: A versão já existe. Por favor, insira uma versão única.', 'danger')
            return redirect(url_for('oportunidades.oportunidades_adicionar'))

        # Verifica se vigencia_inicio não é posterior a vigencia_fim
        if vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('oportunidades.oportunidades_adicionar'))

        # Busca a maior versão inferior à nova versão
        versao_anterior = (
            OportunidadesInvestimento.query
            .filter(OportunidadesInvestimento.versao < int(versao))
            .order_by(OportunidadesInvestimento.versao.desc())
            .first()
        )

        # Se houver uma versão anterior, valida a nova data de vigência contra a vigência final da versão anterior
        if versao_anterior and vigencia_inicio_date < versao_anterior.vigencia_fim:
            flash(
                f'Erro: A data de início da nova vigência deve ser igual ou posterior à data de fim da versão anterior ({versao_anterior.versao}).', 
                'danger'
            )
            return redirect(url_for('oportunidades.oportunidades_adicionar'))

        # Busca a menor versão superior à nova versão
        versao_subsequente = (
            OportunidadesInvestimento.query
            .filter(OportunidadesInvestimento.versao > int(versao))
            .order_by(OportunidadesInvestimento.versao.asc())
            .first()
        )

        # Se houver uma versão subsequente, valida a data de vigência final contra a data de vigência inicial da versão subsequente
        if versao_subsequente and vigencia_fim_date > versao_subsequente.vigencia_inicio:
            flash(
                f'Erro: A data de fim da nova vigência deve ser igual ou anterior à data de início da próxima versão ({versao_subsequente.versao}).', 
                'danger'
            )
            return redirect(url_for('oportunidades.oportunidades_adicionar'))
        
        # Gera o hash para o arquivo da nova versão
        hash_arquivo = gerar_hash_oportunidades(versao)
        documento_filename = None
        
        # Upload do documento, se o status for "registrado"
        if status == 'registrado' and 'documento' in request.files:
            documento = request.files['documento']
            if documento:
                # Salva o documento com o hash como nome do arquivo
                filename = f"{hash_arquivo}.pdf"
                documento.save(os.path.join(current_app.config['UPLOAD_FOLDER_OPORTUNIDADES'], filename))
                documento_filename = filename
        
        # Cria o novo regulamento após todas as validações
        nova_oportunidades = OportunidadesInvestimento(
            versao=int(versao),
            vigencia_inicio=vigencia_inicio_date,
            vigencia_fim=vigencia_fim_date,
            status=status,
            texto=texto,
            hash=hash_arquivo if status == 'registrado' else None
        )

        db.session.add(nova_oportunidades)
        db.session.commit()

        return redirect(url_for('oportunidades.oportunidades_investimento'))

    return render_template('oportunidades_adicionar.html')

@oportunidades_bp.route('/oportunidades_investimento/editar/<int:versao>', methods=['GET', 'POST'])
@login_required
def oportunidades_editar(versao):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))
    
    oportunidade = OportunidadesInvestimento.query.get(versao)
    if not oportunidade:
        flash("Versão não encontrada.", "danger")
        return redirect(url_for('oportunidades.oportunidades_investimento'))

    if request.method == 'POST':
        nova_versao = request.form.get('versao')
        vigencia_inicio = request.form.get('vigencia_inicio')
        vigencia_fim = request.form.get('vigencia_fim')
        status = request.form.get('status')
        texto = request.form.get('texto')

        # Verifica se a nova versão já existe no banco
        if nova_versao != str(oportunidade.versao):
            versao_existente = OportunidadesInvestimento.query.get(int(nova_versao))
            if versao_existente:
                flash("Erro: A versão já existe!", "danger")
                return redirect(url_for('oportunidades.oportunidades_editar', versao=versao))

        # Converte as datas e realiza a validação
        try:
            vigencia_inicio_date = datetime.strptime(vigencia_inicio, '%Y-%m-%d').date()
            vigencia_fim_date = datetime.strptime(vigencia_fim, '%Y-%m-%d').date()
        except ValueError:
            flash('Datas inválidas. Por favor, insira uma data válida.', 'danger')
            return redirect(url_for('oportunidades.oportunidades_editar', versao=versao))

        if vigencia_inicio_date > vigencia_fim_date:
            flash('Erro: A data de início da vigência não pode ser posterior à data de fim.', 'danger')
            return redirect(url_for('oportunidades.oportunidades_editar', versao=versao))

        # Busca a maior versão inferior à versão atual, excluindo a própria versão
        versao_anterior = (
            OportunidadesInvestimento.query
            .filter(OportunidadesInvestimento.versao < int(nova_versao), OportunidadesInvestimento.versao != oportunidade.versao)
            .order_by(OportunidadesInvestimento.versao.desc())
            .first()
        )

        # Valida a nova data de vigência contra a vigência final da versão anterior
        if versao_anterior and vigencia_inicio_date < versao_anterior.vigencia_fim:
            flash(
                f'Erro: A data de início da vigência deve ser igual ou posterior à data de fim da versão anterior ({versao_anterior.versao}).', 
                'danger'
            )
            return redirect(url_for('oportunidades.oportunidades_editar', versao=versao))

        # Busca a menor versão superior à versão atual, excluindo a própria versão
        versao_subsequente = (
            OportunidadesInvestimento.query
            .filter(OportunidadesInvestimento.versao > int(nova_versao), OportunidadesInvestimento.versao != oportunidade.versao)
            .order_by(OportunidadesInvestimento.versao.asc())
            .first()
        )

        # Valida a nova data de vigência contra a vigência inicial da versão subsequente
        if versao_subsequente and vigencia_fim_date > versao_subsequente.vigencia_inicio:
            flash(
                f'Erro: A data de fim da vigência deve ser igual ou anterior à data de início da próxima versão ({versao_subsequente.versao}).', 
                'danger'
            )
            return redirect(url_for('oportunidades.oportunidades_editar', versao=versao))

        # Deleta o arquivo antigo se o status mudar de 'registrado' para 'aprovado'
        if oportunidade.status == 'registrado' and status == 'aprovado' and oportunidade.hash:
            old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER_OPORTUNIDADES'], f"{oportunidade.hash}.pdf")
            if os.path.exists(old_filepath):
                os.remove(old_filepath)  # Remove o arquivo associado
            oportunidade.hash = None  # Remove o hash já que não deve haver documento para a versão aprovada

        # Verifica se um novo documento foi enviado
        documento = request.files.get('documento')
        if status == 'registrado' and documento and documento.filename != '':
            # Gera novo hash para o arquivo com base na nova versão
            hash_arquivo = gerar_hash_oportunidades(nova_versao)
            filename = f"{hash_arquivo}.pdf"
            
            # Salva o novo documento
            documento.save(os.path.join(current_app.config['UPLOAD_FOLDER_OPORTUNIDADES'], filename))
            
            # Deleta o arquivo antigo (se houver) e atualiza o hash no banco
            if oportunidade.hash and oportunidade.hash != hash_arquivo:  # Verifica se a hash é diferente
                old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER_OPORTUNIDADES'], f"{oportunidade.hash}.pdf")
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            oportunidade.hash = hash_arquivo
        elif status == 'registrado' and not oportunidade.hash:
            flash("Erro: Nenhum documento foi selecionado para upload. Por favor, selecione um arquivo.", "danger")
            return redirect(url_for('oportunidades.oportunidades_editar', versao=versao))

        # Atualiza os valores no banco de dados
        oportunidade.versao = int(nova_versao)
        oportunidade.vigencia_inicio = vigencia_inicio_date
        oportunidade.vigencia_fim = vigencia_fim_date
        oportunidade.status = status
        oportunidade.texto = texto
        
        db.session.commit()
        return redirect(url_for('oportunidades.oportunidades_detalhe', versao=oportunidade.versao))

    return render_template('oportunidades_editar.html', oportunidade=oportunidade)

@oportunidades_bp.route('/oportunidades_investimento/<int:versao>/download')
def oportunidade_download(versao):
    oportunidade = OportunidadesInvestimento.query.get(versao)
    if oportunidade and oportunidade.hash:
        # Gera o nome do arquivo a partir da versão
        nome_arquivo = f"Política de Seleção e Avaliação de Oportunidades de Investimento Versão {oportunidade.versao}.pdf"
        
        # Busca o arquivo pelo hash
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER_OPORTUNIDADES'],
            f"{oportunidade.hash}.pdf",
            as_attachment=True,
            download_name=nome_arquivo  # Define o nome do arquivo para o download
        )
    flash("Documento não encontrado ou não disponível para esta versão.", "warning")
    return redirect(url_for('oportunidades.oportunidades_investimento'))

@oportunidades_bp.route('/oportunidades_investimento/deletar/<int:versao>', methods=['POST'])
@login_required
def oportunidades_deletar(versao):
    if not verificar_super_admin():
        return redirect(url_for('auth.error'))
    
    # Tenta buscar a versão da política
    oportunidade = OportunidadesInvestimento.query.get(versao)
    if oportunidade:
        # Verifica se há um arquivo associado e tenta removê-lo
        if oportunidade.hash:
            arquivo_path = os.path.join(current_app.config['UPLOAD_FOLDER_OPORTUNIDADES'], f"{oportunidade.hash}.pdf")
            if os.path.exists(arquivo_path):
                os.remove(arquivo_path)  # Remove o arquivo associado à versão

        db.session.delete(oportunidade)
        db.session.commit()
    else:
        flash('Erro: Versão da Política de Seleção e Avaliação de Oportunidades de Investimento não encontrada.', 'danger')
    
    return redirect(url_for('oportunidades.oportunidades_investimento'))

@oportunidades_bp.route('/oportunidades_investimento/<int:versao>')
@login_required
def oportunidades_detalhe(versao):
    oportunidade = OportunidadesInvestimento.query.get_or_404(versao)
    return render_template('oportunidades_detalhe.html', oportunidade=oportunidade)

def gerar_hash_oportunidades(versao):
    import hashlib
    hash_obj = hashlib.sha256(f"Política de Seleção e Avaliação de Oportunidades de Investimento Versão {versao}".encode())
    return hash_obj.hexdigest()