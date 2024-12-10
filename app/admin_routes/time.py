from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models import db, Pessoas, PessoaCargo, PessoaLotacao
from app.decorators import login_required
from app import db
from app.admin_routes.routes import verificar_diretor
from unidecode import unidecode
import re
import os
import hashlib

time_bp = Blueprint('time', __name__, url_prefix='/admin')

# Função para gerar o hash da foto com base no email
def generate_photo_hash(email):
    return hashlib.sha256((email + "foto").encode('utf-8')).hexdigest()

# Função para salvar a foto no diretório
def save_photo(file, email):
    if file and file.filename != '':
        # Gera o hash do nome do arquivo com base no email
        hash_name = generate_photo_hash(email)
        filename = f"{hash_name}.jpg"
        upload_folder = current_app.config['UPLOAD_FOLDER_TIME']
        filepath = os.path.join(upload_folder, filename)

        # Log para verificar o caminho
        print(f"Salvando arquivo em: {filepath}")
        
        file.save(filepath)
        return hash_name
    return None

# Rota para visualizar a tabela de pessoas
@time_bp.route('/time')
@login_required
def time():
    # Obtém todas as pessoas ordenadas por nome
    pessoas = db.session.query(Pessoas).order_by(Pessoas.nome.asc()).all()
    return render_template('time.html', pessoas=pessoas)

# Rota para adicionar pessoas no time
@time_bp.route('/time/adicionar', methods=['GET', 'POST'])
def time_adicionar():
    if not verificar_diretor():  # Verifica se o usuário tem permissão
        return redirect(url_for('auth.error'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        cargos = request.form.getlist('cargos[]')
        lotacoes = request.form.getlist('lotacoes[]')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        data_admissao = request.form.get('data_admissao')
        aniversario = request.form.get('aniversario')
        genero = request.form.get('genero')
        etnia = request.form.get('etnia')
        linkedin = request.form.get('linkedin')
        instagram = request.form.get('instagram')
        twitter = request.form.get('twitter')  
        frase = request.form.get('frase')
        foto = request.files.get('foto')

        # Validar campos obrigatórios
        if not all([nome, cidade, estado, data_admissao, aniversario, genero, etnia, email]):
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('time.time_adicionar'))

        # Salva a foto e obtém o hash
        hash_foto = save_photo(foto, email)

        # Gerar o slug a partir do nome
        slug = generate_slug(nome)

        # Criar e salvar a nova pessoa
        nova_pessoa = Pessoas(
            nome=nome,
            email=email,
            cidade=cidade,
            estado=estado,
            data_admissao=data_admissao,
            aniversario=aniversario,
            genero=genero,
            etnia=etnia,
            linkedin=linkedin,
            instagram=instagram,
            twitter=twitter,
            frase=frase,
            slug=slug,
            hash_foto=hash_foto,
        )

        try:
            db.session.add(nova_pessoa)
            db.session.flush()  # Garante que a pessoa foi inserida antes de adicionar os cargos e lotações

            # Criar os objetos de cargo e lotação após a pessoa estar na sessão
            pessoa_cargos = [PessoaCargo(cargo=c, pessoa_email=email) for c in cargos]
            pessoa_lotacoes = [PessoaLotacao(lotacao=l, pessoa_email=email) for l in lotacoes]

            db.session.add_all(pessoa_cargos)
            db.session.add_all(pessoa_lotacoes)

            db.session.commit()
            return redirect(url_for('time.time'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao adicionar membro: ' + str(e), 'danger')
            return redirect(url_for('time.time_adicionar'))

    return render_template('time_adicionar.html')

# Rota para editar uma pessoa do time
@time_bp.route('/time/editar/<string:email>', methods=['GET', 'POST'])
def time_editar(email):
    email_session = session.get('email', '').strip().lower()
    email_url = email.strip().lower()
    if not (verificar_diretor() or email_session == email_url):
        return redirect(url_for('auth.error'))
    
    pessoa = db.session.get(Pessoas, email)
    if not pessoa:
        flash('Pessoa não encontrada.', 'danger')
        return redirect(url_for('time.time'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        cargos = request.form.getlist('cargos[]')
        lotacoes = request.form.getlist('lotacoes[]')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        data_admissao = request.form.get('data_admissao')
        aniversario = request.form.get('aniversario')
        genero = request.form.get('genero')
        etnia = request.form.get('etnia')
        linkedin = request.form.get('linkedin')
        instagram = request.form.get('instagram')
        twitter = request.form.get('twitter')  
        frase = request.form.get('frase')
        foto = request.files.get('foto')

        # Validar campos obrigatórios
        if not all([nome, cidade, estado, data_admissao, aniversario, genero, etnia, email]):
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('time.time_editar', email=email))

        # Salva a foto e obtém o hash, se nova foto for enviada
        if foto:
            hash_foto = save_photo(foto, email)
            pessoa.hash_foto = hash_foto

        # Atualizar os dados da pessoa
        pessoa.nome = nome
        pessoa.email = email
        pessoa.cidade = cidade
        pessoa.estado = estado
        pessoa.data_admissao = data_admissao
        pessoa.aniversario = aniversario
        pessoa.genero = genero
        pessoa.etnia = etnia
        pessoa.linkedin = linkedin
        pessoa.instagram = instagram
        pessoa.twitter = twitter
        pessoa.frase = frase

        # Atualizar cargos e lotações
        db.session.query(PessoaCargo).filter(PessoaCargo.pessoa_email == email).delete()
        db.session.query(PessoaLotacao).filter(PessoaLotacao.pessoa_email == email).delete()

        pessoa_cargos = [PessoaCargo(cargo=c, pessoa_email=email) for c in cargos]
        pessoa_lotacoes = [PessoaLotacao(lotacao=l, pessoa_email=email) for l in lotacoes]

        db.session.add_all(pessoa_cargos)
        db.session.add_all(pessoa_lotacoes)

        try:
            db.session.commit()
            return redirect(url_for('time.time'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar alterações: ' + str(e), 'danger')
            return redirect(url_for('time.time_editar', email=email))
    
    return render_template('time_editar.html', pessoa=pessoa)

# Rota para deletar uma pessoa do time
@time_bp.route('/time/deletar/<string:email>', methods=['POST'])
def time_deletar(email):
    if not verificar_diretor():
        return redirect(url_for('auth.error'))
    
    pessoa = db.session.get(Pessoas, email)
    if not pessoa:
        flash('Pessoa não encontrada.', 'danger')
        return redirect(url_for('time.time'))
    
    # Caminho completo da foto
    if pessoa.hash_foto:
        foto_path = os.path.join(current_app.config['UPLOAD_FOLDER_TIME'], f"{pessoa.hash_foto}.jpg")
        if os.path.exists(foto_path):
            try:
                os.remove(foto_path)
                flash('Foto associada removida com sucesso.', 'info')
            except Exception as e:
                flash(f'Erro ao remover a foto associada: {e}', 'warning')

    try:
        db.session.delete(pessoa)
        db.session.commit()
        flash(f'Pessoa {pessoa.nome} e dados relacionados removidos com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar pessoa: {e}', 'danger')
    
    return redirect(url_for('time.time'))

# Função para gerar slug a partir do nome
def generate_slug(nome):
    nome = unidecode(nome)  # Remove acentos
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', nome)  # Remove caracteres especiais
    slug = re.sub(r'\s+', '_', slug)  # Substitui espaços por _
    return slug.lower()

