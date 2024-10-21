from flask import Blueprint, redirect, url_for, session
from app import oauth
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    redirect_uri = url_for('auth.auth_callback', _external=True)
    print(f'Redirect URI: {redirect_uri}')  # Exibe a URI no terminal
    session['nonce'] = os.urandom(16).hex()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'])

@auth_bp.route('/auth/callback')
def auth_callback():
    token = oauth.google.authorize_access_token()
    nonce = session.pop('nonce', None)
    
    if not nonce:
        return "Erro: Nonce ausente na sessão!", 400
    
    resp = oauth.google.parse_id_token(token, nonce=nonce)
    session['user'] = resp
    
    # Aqui alteramos para 'main.index'
    return redirect(url_for('main.index'))  # Certifique-se que a rota principal está registrada como 'main.index'
