from flask import Blueprint, redirect, url_for, session, flash, request
from app import oauth
from app.models import GrupoUsuario
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    redirect_uri = url_for('auth.auth_callback', _external=True)
    print(f'Redirect URI: {redirect_uri}')  # Exibe a URI no terminal
    session['nonce'] = os.urandom(16).hex()
    session['state'] = os.urandom(16).hex()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'], state=session['state'])

@auth_bp.route('/auth/callback')
def auth_callback():
    # Verifica se o estado recebido corresponde ao estado na sessão
    state_in_request = request.args.get('state')
    if 'state' not in session or session.get('state') != state_in_request:
        session.clear()  # Limpa a sessão caso o estado não corresponda
        flash("Erro de CSRF: estado não corresponde! Tente novamente.", 'danger')
        return redirect(url_for('auth.login'))  # Redireciona para a página de login
    
    token = oauth.google.authorize_access_token()
    nonce = session.pop('nonce', None)
    
    if not nonce:
        return "Erro: Nonce ausente na sessão!", 400
    
    resp = oauth.google.parse_id_token(token, nonce=nonce)
    email = resp['email']
    
    # Verifica se o email está na tabela grupos_usuarios
    usuario = GrupoUsuario.query.filter_by(email=email).first()
    if usuario is None:
        # Limpa a sessão e exibe mensagem de erro
        session.clear()
        flash('Seu email não está autorizado a acessar este sistema.', 'danger')
        return redirect(url_for('auth.error'))  # Redireciona para uma página de erro de autenticação

    # Se o email estiver na tabela, armazena o email e grupo na sessão
    session['email'] = email
    session['grupo'] = usuario.grupo  # Armazena o grupo do usuário

    return redirect(url_for('main.index'))  # Redireciona para a página principal

@auth_bp.route('/error')
def error():
    # Página de erro de autenticação
    return "Você não está autorizado a acessar este sistema. Tente novamente com outro e-mail ou entre em contato com o administrador."